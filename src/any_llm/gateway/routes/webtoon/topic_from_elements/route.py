from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
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
from .parser import build_fallback_topic, parse_topic_text
from .prompt import (
    LANGUAGE_LABELS,
    build_prompt,
    build_world_setting_block,
    normalize_scene_elements,
    resolve_era_label,
    resolve_season_label,
)
from .schema import DEFAULT_MODEL, GenerateTopicFromElementsRequest, GenerateTopicFromElementsResponse
from ..topic.prompt import build_system_prompt

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])


@router.post("/topic-from-elements", response_model=GenerateTopicFromElementsResponse)
async def generate_topic_from_elements(
    request: GenerateTopicFromElementsRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> JSONResponse | GenerateTopicFromElementsResponse:
    normalized_elements = normalize_scene_elements(request.sceneElements)
    fallback_topic = build_fallback_topic(normalized_elements)
    if not fallback_topic:
        return JSONResponse(content={"topic": ""}, status_code=status.HTTP_400_BAD_REQUEST)

    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=None,
        missing_master_detail="When using master key, 'user' field is required",
    )
    validate_user_credit(db, user_id)

    resolved_language = request.language or "ko"
    language_label = LANGUAGE_LABELS[resolved_language]
    era_label = resolve_era_label(request.era)
    season_label = resolve_season_label(request.season)
    character_count = request.characterCount
    panel_count = request.panelCount
    world_setting_block = build_world_setting_block(era_label, season_label)
    prompt = build_prompt(
        topic=fallback_topic,
        normalized_elements=normalized_elements,
        genre=request.genre,
        language_label=language_label,
        world_setting_block=world_setting_block,
        character_count=character_count,
        panel_count=panel_count,
    )

    model_input = DEFAULT_MODEL
    provider_name = "gemini"
    model_key, _ = _get_model_pricing(db, provider_name, model_input)

    client = create_genai_client(config)

    try:
        logger.info(
            "webtoon.topic-from-elements request model=%s genre=%s language=%s era=%s season=%s characterCount=%s panelCount=%s sceneElements=%s",
            model_input,
            request.genre,
            resolved_language,
            request.era,
            request.season,
            character_count,
            panel_count,
            normalized_elements,
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
            endpoint="/v1/webtoon/topic-from-elements",
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
        logger.info("Topic-from-elements raw response: %s", text[:500] if text else None)
        topic_text = parse_topic_text(text) if text else None
        logger.info("Topic-from-elements parsed topic: %s", topic_text[:200] if topic_text else None)
        if not topic_text:
            logger.error("Topic-from-elements response invalid, falling back")
            return GenerateTopicFromElementsResponse(topic=fallback_topic)
        return GenerateTopicFromElementsResponse(topic=topic_text)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Topic-from-elements generation failed: %s", exc)
        return GenerateTopicFromElementsResponse(topic=fallback_topic)
