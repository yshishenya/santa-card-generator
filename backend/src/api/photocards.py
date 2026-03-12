"""Photocard API endpoints for the MVP flow."""

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status

from src.core import CardService
from src.core.exceptions import CardServiceError, SessionNotFoundError, VariantNotFoundError
from src.models import (
    APIResponse,
    PhotocardGenerateRequest,
    PhotocardGenerateResponse,
    PhotocardSendRequest,
    PhotocardSendResponse,
)

from .dependencies import get_card_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/photocards/generate",
    response_model=APIResponse[PhotocardGenerateResponse],
)
async def generate_photocard(
    body: PhotocardGenerateRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[PhotocardGenerateResponse]:
    correlation_id = str(uuid4())
    logger.info(
        "[%s] POST /photocards/generate full_name=%s",
        correlation_id,
        body.full_name,
    )

    try:
        response = await service.generate_photocard(body)
        return APIResponse(success=True, data=response, error=None)
    except CardServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc


@router.post(
    "/photocards/send",
    response_model=APIResponse[PhotocardSendResponse],
)
async def send_photocard(
    body: PhotocardSendRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[PhotocardSendResponse]:
    correlation_id = str(uuid4())
    logger.info(
        "[%s] POST /photocards/send session_id=%s selected_image_index=%s",
        correlation_id,
        body.session_id,
        body.selected_image_index,
    )

    try:
        response = await service.send_photocard(body)
        return APIResponse(success=True, data=response, error=None)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {exc.session_id}",
        ) from exc
    except VariantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image variant not found at index: {exc.variant_index}",
        ) from exc
    except CardServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=exc.message,
        ) from exc


@router.get("/photocards/images/{session_id}/{image_id}")
async def get_photocard_image(
    session_id: str,
    image_id: str,
    service: Annotated[CardService, Depends(get_card_service)],
) -> Response:
    image_url = f"generated://{image_id}"
    image_data = service.get_image_data(session_id, image_url)
    if image_data is None:
        if service.get_session(session_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session not found: {session_id}",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image not found: {image_id}",
        )

    return Response(
        content=image_data,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Length": str(len(image_data)),
        },
    )
