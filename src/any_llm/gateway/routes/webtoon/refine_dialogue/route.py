from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from any_llm.gateway.auth import verify_jwt_or_api_key_or_master
from any_llm.gateway.auth.dependencies import get_config
from any_llm.gateway.config import GatewayConfig
from any_llm.gateway.db import APIKey, SessionToken, get_db
from any_llm.gateway.log_config import logger
from any_llm.gateway.routes.chat import _get_model_pricing
from any_llm.gateway.routes.image import (
    _add_user_spend,
    _coerce_usage_metadata,
    _log_image_usage,
    _set_usage_cost,
)
from any_llm.gateway.routes.utils import (
    charge_usage_cost,
    resolve_target_user,
    validate_user_credit,
)

from ..genai_helper import create_genai_client, generate_text_content, get_response_text
from .parser import clean_text
from .prompt import (
    LANGUAGE_LABELS,
    build_prompt,
    build_world_setting_block,
    resolve_era_label,
    resolve_season_label,
    TONE_LABELS,
)
from .schema import DEFAULT_MODEL, RefineDialogueRequest, RefineDialogueResponse

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])


@router.post("/refine-dialogue", response_model=RefineDialogueResponse)
async def refine_dialogue(
    request: RefineDialogueRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> RefineDialogueResponse:
    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=None,
        missing_master_detail="When using master key, 'user' field is required",
    )
    validate_user_credit(db, user_id)

    resolved_language = request.language or "ko"
    language_label = LANGUAGE_LABELS[resolved_language]
    tone_label = TONE_LABELS[request.tone or "neutral"]
    era_label = resolve_era_label(request.era)
    season_label = resolve_season_label(request.season)
    world_setting_block = build_world_setting_block(era_label, season_label)
    prompt = build_prompt(
        dialogue=request.dialogue,
        tone_label=tone_label,
        language_label=language_label,
        character_mode=request.characterGenerationMode or "ai",
        scene=request.scene,
        speaker=request.speaker,
        world_setting_block=world_setting_block,
    )

    model_input = DEFAULT_MODEL
    provider_name = "gemini"
    model_key, _ = _get_model_pricing(db, provider_name, model_input)

    client = create_genai_client(config)

    try:
        logger.info(
            "webtoon.refine-dialogue request language=%s tone=%s era=%s season=%s mode=%s dialogue=%s scene=%s speaker=%s",
            resolved_language,
            request.tone,
            request.era,
            request.season,
            request.characterGenerationMode,
            request.dialogue,
            request.scene,
            request.speaker,
        )
        response = generate_text_content(
            client,
            model_input,
            "You strictly follow dialogue refinement rules.",
            prompt,
        )

        usage_info = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
        usage_for_charge = _coerce_usage_metadata(usage_info) or usage_info
        usage_log_id = _log_image_usage(
            db=db,
            api_key_obj=api_key,
            model=model_input,
            provider=provider_name,
            endpoint="/v1/webtoon/refine-dialogue",
            user_id=user_id,
            usage=usage_for_charge,
        )

        if usage_for_charge:
            cost = charge_usage_cost(
                db,
                user_id=user_id,
                usage=usage_for_charge,
                model_key=model_key,
                usage_id=usage_log_id,
            )
            _set_usage_cost(db, usage_log_id, cost)
            _add_user_spend(db, user_id, cost)

        text = get_response_text(response)
        if not text:
            raise HTTPException(status_code=502, detail="Empty response")
        cleaned = clean_text(text)
        return RefineDialogueResponse(dialogue=cleaned)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Dialogue refinement failed: %s", exc)
        raise HTTPException(status_code=502, detail="Dialogue refinement failed") from exc
