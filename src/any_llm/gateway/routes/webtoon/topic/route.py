from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
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
from .parser import build_fallback_topics, parse_topic_candidates
from .prompt import LANGUAGE_LABELS, build_prompt, build_system_prompt, resolve_era_label, resolve_genre_prompt, resolve_season_label
from .schema import DEFAULT_MODEL, GenerateTopicRequest, GenerateTopicResponse

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])


@router.post("/topic", response_model=GenerateTopicResponse)
async def generate_topic(
    request: GenerateTopicRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> JSONResponse | GenerateTopicResponse:
    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=request.user,
        missing_master_detail="When using master key, 'user' field is required in request body",
    )
    validate_user_credit(db, user_id)

    resolved_language = request.language or "ko"
    language_label = LANGUAGE_LABELS[resolved_language]
    genre_prompt = resolve_genre_prompt(request.genre)
    era_label = resolve_era_label(request.era)
    season_label = resolve_season_label(request.season)
    character_count = request.characterCount
    panel_count = request.panelCount
    prompt = build_prompt(genre_prompt, language_label, era_label, season_label, character_count, panel_count)

    model_input = request.model or DEFAULT_MODEL
    provider_name = "gemini"
    model_key, _ = _get_model_pricing(db, provider_name, model_input)

    client = create_genai_client(config)

    try:
        logger.info(
            "webtoon.topic request model=%s genre=%s language=%s era=%s season=%s characterCount=%s panelCount=%s",
            model_input,
            request.genre,
            resolved_language,
            request.era,
            request.season,
            character_count,
            panel_count,
        )
        response = generate_text_content(
            client,
            model_input,
            build_system_prompt(language_label, character_count, panel_count),
            prompt,
            temperature=0.9,  # Higher temperature for creative diversity
        )

        usage_info = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
        usage_for_charge = _coerce_usage_metadata(usage_info) or usage_info
        usage_log_id = _log_image_usage(
            db=db,
            api_key_obj=api_key,
            model=model_input,
            provider=provider_name,
            endpoint="/v1/webtoon/topic",
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
        parsed = parse_topic_candidates(text) if text else None
        if not parsed:
            logger.error("Invalid response schema for topics")
            return build_fallback_topics(genre_prompt["title"], resolved_language)
        return parsed
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Topic generation failed: %s", exc)
        return build_fallback_topics(genre_prompt["title"], resolved_language)
