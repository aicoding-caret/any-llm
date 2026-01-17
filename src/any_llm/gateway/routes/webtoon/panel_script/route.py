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
from .parser import clean_text, parse_json
from .prompt import build_prompt, build_previous_context, build_world_setting_block, resolve_era_label, resolve_season_label
from .schema import DEFAULT_MODEL, PanelHistoryEntry, RefinePanelScriptRequest, RefinePanelScriptResponse

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])


@router.post("/refine-panel-script", response_model=RefinePanelScriptResponse)
async def refine_panel_script(
    request: RefinePanelScriptRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> RefinePanelScriptResponse:
    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=None,
        missing_master_detail="When using master key, 'user' field is required",
    )
    validate_user_credit(db, user_id)

    era_label = resolve_era_label(request.era)
    season_label = resolve_season_label(request.season)
    world_setting_block = build_world_setting_block(era_label, season_label)

    previous_context_list = []
    for panel in request.previousPanels or []:
        index = panel.panel or panel.panelNumber or ""
        scene_text = panel.scene or ""
        dialogue_text = panel.dialogue or ""
        metadata_text = f" / Meta: {panel.metadata}" if panel.metadata else ""
        if scene_text or dialogue_text:
            previous_context_list.append(f"Panel {index}: {scene_text} / {dialogue_text}{metadata_text}")

    prompt_system, prompt_user = build_prompt(
        topic=request.topic or "",
        genre=request.genre or "",
        style=request.style or "",
        world_setting_block=world_setting_block,
        panel_number=request.panelNumber,
        speaker=request.speaker or "",
        scene=request.scene,
        dialogue=request.dialogue,
        improvement=request.improvement or "",
        revision_prompt=request.revisionPrompt or "",
        next_hint=request.nextHint or "",
        previous_context=build_previous_context(previous_context_list),
    )

    model_input = DEFAULT_MODEL
    provider_name = "gemini"
    model_key, _ = _get_model_pricing(db, provider_name, model_input)

    client = create_genai_client(config)

    try:
        logger.info(
            "webtoon.refine-panel-script request panel=%s topic=%s genre=%s style=%s era=%s season=%s speaker=%s scene=%s dialogue=%s improvement=%s revisionPrompt=%s nextHint=%s",
            request.panelNumber,
            request.topic,
            request.genre,
            request.style,
            request.era,
            request.season,
            request.speaker,
            request.scene,
            request.dialogue,
            request.improvement,
            request.revisionPrompt,
            request.nextHint,
        )
        response = generate_text_content(
            client,
            model_input,
            prompt_system,
            prompt_user,
        )

        usage_info = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
        usage_for_charge = _coerce_usage_metadata(usage_info) or usage_info
        usage_log_id = _log_image_usage(
            db=db,
            api_key_obj=api_key,
            model=model_input,
            provider=provider_name,
            endpoint="/v1/webtoon/refine-panel-script",
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
            logger.warning("Refine script response empty")
            raise HTTPException(status_code=502, detail="Empty response from AI")
        cleaned = clean_text(text)
        parsed = parse_json(cleaned)
        if not parsed:
            raise HTTPException(status_code=502, detail="Invalid response structure")
        try:
            return RefinePanelScriptResponse.model_validate(parsed)
        except Exception as exc:
            logger.warning("Refine script validation failed: %s", exc)
            raise HTTPException(status_code=502, detail="Invalid response structure")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Panel script refinement failed: %s", exc)
        raise HTTPException(status_code=502, detail="Panel script refinement failed") from exc
