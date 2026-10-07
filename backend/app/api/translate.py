"""Translation API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.translation import TranslationRequest, TranslationResponse
from backend.app.schemas.error import ErrorResponse
from backend.app.services.translation_service import (
    BaseTranslationService,
    get_translation_service,
)
from backend.app.core.logging import logger

router = APIRouter(tags=["Translation"])


@router.post(
    "/translate",
    response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate regional text to English",
    description="Translates Malayalam script, Manglish / Romanized Malayalam, or code-mixed text to English using the multi-tier translation engine.",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def translate_text(
    request: TranslationRequest,
    translation_service: BaseTranslationService = Depends(get_translation_service),
) -> TranslationResponse:
    """Translates submitted Malayalam or Manglish text into English."""
    try:
        res = translation_service.translate_detailed(
            text=request.text,
            source=request.source_language,
            target=request.target_language,
        )
        return TranslationResponse(
            original_text=request.text,
            translated_text=res.text,
            source_language=res.source_language,
            target_language=request.target_language,
            confidence=res.confidence,
            detected_script=res.detected_script,
            intermediate_malayalam=res.intermediate_malayalam,
            method=res.method,
            status=res.status,
        )
    except Exception as exc:
        logger.error(f"Translation failed unexpectedly: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(exc)}",
        )
