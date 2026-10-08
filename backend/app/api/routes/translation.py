"""Translation API Endpoints (v1) for Kollamo.ai Phase 8."""

from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.schemas.translation import TranslationRequest, TranslationResponse, CommentTranslation
from backend.app.schemas.common import ErrorResponse
from backend.app.services.translation_service import (
    BaseTranslationService,
    get_translation_service,
)
from backend.app.core.logging import logger

router = APIRouter(tags=["Translation"])


@router.post(
    "/translation",
    response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate regional text to English (v1)",
    description="Translates Malayalam, Manglish, or code-mixed text to English, preserving original text.",
    responses={
        422: {"model": ErrorResponse, "description": "Validation error"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
@router.post(
    "/translate",
    response_model=TranslationResponse,
    status_code=status.HTTP_200_OK,
    summary="Translate regional text to English alias (v1)",
    description="Alias for /translation endpoint.",
)
async def translate_text_v1(
    request: TranslationRequest,
    translation_service: BaseTranslationService = Depends(get_translation_service),
) -> TranslationResponse:
    """Translates submitted text to English while maintaining original text verbatim."""
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
            error_message=res.error_message,
        )
    except Exception as exc:
        logger.error(f"Translation failed unexpectedly: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation error: {str(exc)}",
        )
