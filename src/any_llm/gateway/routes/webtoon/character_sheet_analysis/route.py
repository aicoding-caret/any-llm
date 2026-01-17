from __future__ import annotations

import base64
import re
from typing import Any

import httpx

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

from ..genai_helper import create_genai_client, get_response_text
from .parser import parse_metadata
from .prompt import PROMPT
from .schema import CharacterSheetMetadata, CharacterSheetRequest, CharacterSheetResponse, DEFAULT_MODEL

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])


def is_data_url(value: str) -> bool:
    return value.startswith("data:")


def parse_data_url(value: str) -> tuple[str, str]:
    match = re.match(r"^data:(.*?);base64,(.*)$", value)
    if not match:
        raise ValueError("Invalid data URL")
    mime_type, payload = match.groups()
    return mime_type, payload


async def fetch_image_as_base64(url: str) -> tuple[str, str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "image/png")
        payload = base64.b64encode(response.content).decode("utf-8")
        return content_type, payload


@router.post("/character-sheet-analysis", response_model=CharacterSheetResponse)
async def analyze_character_sheet(
    request: CharacterSheetRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> CharacterSheetResponse:
    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=None,
        missing_master_detail="When using master key, 'user' field is required",
    )
    validate_user_credit(db, user_id)

    if is_data_url(request.imageUrl):
        mime_type, payload = parse_data_url(request.imageUrl)
    else:
        mime_type, payload = await fetch_image_as_base64(request.imageUrl)

    model_input = DEFAULT_MODEL
    provider_name = "gemini"
    model_key, _ = _get_model_pricing(db, provider_name, model_input)

    client = create_genai_client(config)
    assert genai is not None

    # Build multimodal content with image
    image_bytes = base64.b64decode(payload)
    image_part = genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    text_part = genai.types.Part.from_text(text=PROMPT)

    content_config = genai.types.GenerateContentConfig(
        system_instruction="You analyze character sheets with precision.",
        response_modalities=["Text"],
        candidate_count=1,
    )

    contents = [genai.types.Content(role="user", parts=[image_part, text_part])]

    try:
        response = client.models.generate_content(
            model=model_input,
            contents=contents,
            config=content_config,
        )

        usage_info = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
        usage_for_charge = _coerce_usage_metadata(usage_info) or usage_info
        usage_log_id = _log_image_usage(
            db=db,
            api_key_obj=api_key,
            model=model_input,
            provider=provider_name,
            endpoint="/v1/webtoon/character-sheet-analysis",
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
        metadata = parse_metadata(text) if text else None
        if not metadata:
            metadata = CharacterSheetMetadata(
                summary=text or "",
                persona="",
                outfit=[],
                colors=[],
                accessories=[],
                hair="",
                face="",
                body="",
                props=[],
                shoes=[],
                notes=[],
            )
        return CharacterSheetResponse(metadata=metadata)
    except Exception as exc:
        logger.error("Character sheet analysis failed: %s", exc)
        raise HTTPException(status_code=502, detail="Character analysis failed") from exc
