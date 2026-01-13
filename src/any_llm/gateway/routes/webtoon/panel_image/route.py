from __future__ import annotations

import base64
from typing import Any, Iterable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from any_llm import AnyLLM
from any_llm.gateway.auth import verify_jwt_or_api_key_or_master
from any_llm.gateway.auth.dependencies import get_config
from any_llm.gateway.config import GatewayConfig
from any_llm.gateway.db import APIKey, SessionToken, get_db
from any_llm.gateway.log_config import logger
from any_llm.gateway.routes.chat import (
    _get_model_pricing,
)
from any_llm.gateway.routes.image import (
    _add_user_spend,
    _build_contents,
    _coerce_usage_metadata,
    _get_gemini_api_key,
    _log_image_usage,
    _set_usage_cost,
    ImageUsage,
)
from any_llm.gateway.routes.utils import (
    charge_usage_cost,
    resolve_target_user,
    validate_user_credit,
)

from .prompt import build_prompt
from .schema import GeneratePanelImageRequest, GeneratePanelImageResponse

try:
    from google import genai
except ImportError:  # pragma: no cover
    genai = None  # type: ignore[assignment]

router = APIRouter(prefix="/v1/webtoon", tags=["webtoon"])

DEFAULT_MODEL = "gemini-3-pro-image-preview"
DEFAULT_RESOLUTION = "1K"
DEFAULT_ASPECT_RATIO = "1:1"


def _to_data_url(mime_type: str, payload: str) -> str:
    return f"data:{mime_type};base64,{payload}"


def _guess_or_format_data_url(value: str, mime_type: str | None = None) -> str:
    trimmed = value.strip()
    if trimmed.startswith("data:"):
        return trimmed
    return _to_data_url(mime_type or "image/png", trimmed)


def _build_reference_urls(
    references: Iterable[str] | None,
    extra_images: Iterable[str] | None,
) -> list[str]:
    result: list[str] = []
    if references:
        result.extend(filter(None, references))
    if extra_images:
        result.extend(filter(None, extra_images))
    return result


def _build_reference_data_urls(scene_references: list[str] | None, character_images: list[str] | None) -> list[str]:
    # If values already include data:, keep them; otherwise assume base64 raw and add png header.
    result: list[str] = []
    for item in scene_references or []:
        result.append(item)
    for image in character_images or []:
        result.append(_guess_or_format_data_url(image))
    return result


def _resolve_resolution(value: str | None) -> str:
    return value or DEFAULT_RESOLUTION


def _resolve_aspect_ratio(value: str | None) -> str:
    return value or DEFAULT_ASPECT_RATIO


def _build_image_usage_payload(usage: Any | None, cost: float | None) -> ImageUsage | None:
    if not usage:
        return None
    return ImageUsage(
        inputTokens=getattr(usage, "prompt_tokens", 0) or 0,
        outputTokens=getattr(usage, "completion_tokens", 0) or 0,
        totalTokens=getattr(usage, "total_tokens", 0) or 0,
        totalCost=float(cost) if cost is not None else None,
        cacheWriteTokens=0,
        cacheReadTokens=0,
    )


def _ensure_genai_available() -> None:
    if genai is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="google-genai dependency is not installed",
        )


def _build_reference_urls_from_data(
    references: list[str] | None,
    extra_images: list[str] | None,
) -> list[str]:
    transformed: list[str] = []
    for item in references or []:
        transformed.append(_guess_or_format_data_url(item))
    for extra in extra_images or []:
        transformed.append(_guess_or_format_data_url(extra))
    return transformed


@router.post("/panel-image", response_model=GeneratePanelImageResponse)
async def generate_panel_image(
    request: GeneratePanelImageRequest,
    auth_result: tuple[APIKey | None, bool, str | None, SessionToken | None] = Depends(verify_jwt_or_api_key_or_master),
    db: Session = Depends(get_db),
    config: GatewayConfig = Depends(get_config),
) -> GeneratePanelImageResponse:
    api_key, _, _, _ = auth_result
    user_id = resolve_target_user(
        auth_result,
        explicit_user=None,
        missing_master_detail="When using master key, 'user' detail is required",
    )
    validate_user_credit(db, user_id)

    prompt_text = build_prompt(request)
    reference_data_urls = _build_reference_urls_from_data(request.references and [ref.base64 for ref in request.references], request.characterImages)

    model_input = request.model or DEFAULT_MODEL
    provider, model = AnyLLM.split_model_provider(model_input)
    model_key, _ = _get_model_pricing(db, provider, model)
    credentials = _get_provider_credentials(config, provider)

    _ensure_genai_available()
    api_key_val = _get_gemini_api_key(config)
    client = genai.Client(api_key=api_key_val)

    image_config = genai.types.ImageConfig(
        aspect_ratio=_resolve_aspect_ratio(request.aspectRatio),
        image_size=_resolve_resolution(request.resolution),
    )

    content_config = genai.types.GenerateContentConfig(
        response_modalities=["Text", "Image"],
        image_config=image_config,
        candidate_count=1,
        thinking_config=genai.types.ThinkingConfig(include_thoughts=True),
    )

    contents = _build_contents(prompt_text, reference_data_urls)

    logger.info(
        "webtoon.panel-image request model=%s panel=%s references=%d prompt_len=%d",
        model_input,
        request.panelNumber,
        len(reference_data_urls),
        len(prompt_text),
    )

    try:
        response = client.models.generate_content(
            model=model_input,
            contents=contents,
            config=content_config,
            **credentials,
        )
    except Exception as exc:
        logger.error("panel image generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Panel image generation failed: {exc!s}",
        ) from exc

    parts = getattr(response, "parts", None) or []
    texts: list[str] = []
    thoughts: list[str] = []
    image_bytes: bytes | None = None
    mime_type = "image/png"

    for part in parts:
        text_value = getattr(part, "text", None)
        if isinstance(text_value, str) and text_value:
            if getattr(part, "thought", False):
                thoughts.append(text_value)
            else:
                texts.append(text_value)

        inline_data = getattr(part, "inline_data", None)
        data = getattr(inline_data, "data", None) if inline_data is not None else None
        candidate_mime = getattr(inline_data, "mime_type", None) if inline_data is not None else None
        if not data:
            continue
        if isinstance(data, bytearray):
            data = bytes(data)
        if not isinstance(data, (bytes, bytearray)):
            continue
        if isinstance(candidate_mime, str) and candidate_mime.startswith("image/"):
            mime_type = candidate_mime
        image_bytes = data
        break

    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Panel image generation returned no image parts",
        )

    base64_data = base64.b64encode(image_bytes).decode("utf-8")
    usage_info = getattr(response, "usage_metadata", None) or getattr(response, "usage", None)
    usage_for_charge = _coerce_usage_metadata(usage_info) or usage_info

    usage_log_id = _log_image_usage(
        db=db,
        api_key_obj=api_key,
        model=model_input,
        provider=provider,
        endpoint="/v1/webtoon/panel-image",
        user_id=user_id,
        usage=usage_for_charge,
    )

    usage_payload: ImageUsage | None = None
    if usage_for_charge:
        cost = charge_usage_cost(db, user_id, usage=usage_for_charge, model_key=model_key, usage_id=usage_log_id)
        _set_usage_cost(db, usage_log_id, cost)
        _add_user_spend(db, user_id, cost)
        usage_payload = _build_image_usage_payload(usage_for_charge, cost)

    return GeneratePanelImageResponse(
        mimeType=mime_type,
        base64=base64_data,
        prompt=prompt_text,
        texts=texts,
        thoughts=thoughts,
        usage=usage_payload,
    )
