"""Cards API endpoints for generating and sending greeting cards.

This module provides REST endpoints for:
- Generating new greeting cards with text and image variants
- Regenerating specific text or image variants
- Sending selected cards to Telegram
- Retrieving generated images
"""

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings
from src.core import CardService
from src.core.exceptions import (
    CardServiceError,
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    VariantNotFoundError,
)
from src.models import (
    APIResponse,
    CardGenerationRequest,
    CardGenerationResponse,
    RegenerateRequest,
    RegenerateResponse,
    SendCardRequest,
    SendCardResponse,
)

from .dependencies import get_card_service

# Rate limiter for card endpoints
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_rate_limit() -> str:
    """Get rate limit from settings dynamically.

    Using a callable allows tests to modify the rate limit.
    """
    return f"{settings.rate_limit_per_minute}/minute"


@router.post("/cards/generate", response_model=APIResponse[CardGenerationResponse])
@limiter.limit(get_rate_limit)
async def generate_card(
    request: Request,
    body: CardGenerationRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[CardGenerationResponse]:
    """Generate a new greeting card with text and image variants."""
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] POST /cards/generate - recipient: {body.recipient}"
    )

    try:
        response = await service.generate_card(body)
        logger.info(
            f"[{correlation_id}] Card generated successfully, session: {response.session_id}, "
            f"text_variants: {len(response.text_variants)}, "
            f"image_variants: {len(response.image_variants)}"
        )
        return APIResponse(success=True, data=response, error=None)

    except RecipientNotFoundError as e:
        logger.error(f"[{correlation_id}] Employee not found: {e.employee_name}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee not found: {e.employee_name}",
        )

    except CardServiceError as e:
        logger.error(f"[{correlation_id}] Card service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Card generation failed: {e.message}",
        )

    except Exception as e:
        logger.exception(f"[{correlation_id}] Unexpected error during card generation")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/cards/regenerate", response_model=APIResponse[RegenerateResponse])
@limiter.limit(get_rate_limit)
async def regenerate_variant(
    request: Request,
    body: RegenerateRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[RegenerateResponse]:
    """Regenerate all text or image variants based on the specified type.
    
    This function handles the regeneration of variants for either text or image
    elements. It first logs the request details, then checks the element type to
    call the appropriate regeneration method from the CardService. If the element
    type is invalid, it raises an HTTPException. The function also manages various
    exceptions related to session validity and regeneration limits, ensuring proper
    error handling and logging throughout the process.
    
    Args:
        request (Request): Starlette Request object (required for rate limiting).
        body (RegenerateRequest): Regeneration request containing session ID and element type.
        service (CardService): Injected CardService instance.
    
    Returns:
        APIResponse[RegenerateResponse]: APIResponse containing RegenerateResponse with new variants and remaining
            count.
    
    Raises:
        HTTPException 404: If session is not found.
        HTTPException 400: If session has expired or invalid element type.
        HTTPException 429: If regeneration limit has been exceeded.
        HTTPException 500: If regeneration fails due to internal error.
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] POST /cards/regenerate - session: {body.session_id}, "
        f"element: {body.element_type}"
    )

    try:
        # Regenerate based on element type
        if body.element_type == "text":
            response = await service.regenerate_text(session_id=body.session_id)
            variant_count = len(response.text_variants) if response.text_variants else 0
        elif body.element_type == "image":
            response = await service.regenerate_image(session_id=body.session_id)
            variant_count = len(response.image_variants) if response.image_variants else 0
        else:
            logger.error(f"[{correlation_id}] Invalid element type: {body.element_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid element type: {body.element_type}",
            )

        logger.info(
            f"[{correlation_id}] Regenerated {variant_count} {body.element_type} variants, "
            f"remaining: {response.remaining_regenerations}"
        )

        return APIResponse(success=True, data=response, error=None)

    except SessionNotFoundError as e:
        logger.error(f"[{correlation_id}] Session not found: {e.session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {e.session_id}",
        )

    except SessionExpiredError as e:
        logger.error(f"[{correlation_id}] Session expired: {e.session_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session expired: {e.session_id}",
        )

    except RegenerationLimitExceededError as e:
        logger.error(
            f"[{correlation_id}] Regeneration limit exceeded for {e.element_type}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Regeneration limit exceeded for {e.element_type}: "
            f"maximum {e.max_regenerations} regenerations allowed",
        )

    except CardServiceError as e:
        logger.error(f"[{correlation_id}] Card service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration failed: {e.message}",
        )

    except Exception as e:
        logger.exception(f"[{correlation_id}] Unexpected error during regeneration")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.post("/cards/send", response_model=APIResponse[SendCardResponse])
@limiter.limit(get_rate_limit)
async def send_card(
    request: Request,
    body: SendCardRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[SendCardResponse]:
    """Send selected card to Telegram.
    
    This endpoint processes a request to send a card, which includes a text and an
    image variant, to a configured Telegram chat/topic. It logs the request details
    and utilizes the CardService to send the card. The function handles various
    exceptions related to session and variant validation, ensuring appropriate
    error responses are returned in case of failures.
    
    Args:
        request: Starlette Request object (required for rate limiting).
        body: Send request with session ID and selected variant indices.
        service: Injected CardService instance.
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] POST /cards/send - session: {body.session_id}, "
        f"employee: {body.employee_name}, text_idx: {body.selected_text_index}, "
        f"image_idx: {body.selected_image_index}, "
        f"use_original: {body.use_original_text}, include_original: {body.include_original_text}"
    )

    try:
        send_response = await service.send_card(body)

        if send_response.success:
            logger.info(
                f"[{correlation_id}] Card sent successfully, "
                f"message_id: {send_response.telegram_message_id}"
            )
            return APIResponse(success=True, data=send_response, error=None)
        else:
            logger.error(f"[{correlation_id}] Failed to send card: {send_response.message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=send_response.message,
            )

    except SessionNotFoundError as e:
        logger.error(f"[{correlation_id}] Session not found: {e.session_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session not found: {e.session_id}",
        )

    except SessionExpiredError as e:
        logger.error(f"[{correlation_id}] Session expired: {e.session_id}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session expired: {e.session_id}",
        )

    except VariantNotFoundError as e:
        logger.error(
            f"[{correlation_id}] Variant not found: {e.element_type} at index {e.variant_index}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{e.element_type.capitalize()} variant not found at index: {e.variant_index}",
        )

    except CardServiceError as e:
        logger.error(f"[{correlation_id}] Card service error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send card: {e.message}",
        )

    except Exception as e:
        logger.exception(f"[{correlation_id}] Unexpected error while sending card")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/cards/images/{session_id}/{image_id}")
async def get_image(
    session_id: str,
    image_id: str,
    service: Annotated[CardService, Depends(get_card_service)],
) -> Response:
    """Get generated image by ID.

    This endpoint retrieves the binary image data for a specific image variant.
    The image is returned as a PNG response with appropriate content type.

    Args:
        session_id: Session ID from the generation request.
        image_id: Unique identifier for the image variant.
        service: Injected CardService instance.

    Returns:
        Response with image binary data and PNG content type.

    Raises:
        HTTPException 404: If session or image is not found.
        HTTPException 400: If session has expired.
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] GET /cards/images/{session_id}/{image_id}"
    )

    try:
        # Construct image URL as stored in session
        image_url = f"generated://{image_id}"

        # Get image data using public method
        image_data = service.get_image_data(session_id, image_url)

        if image_data is None:
            # Check if session exists (get_session returns None for expired sessions)
            session = service.get_session(session_id)
            if session is None:
                logger.error(f"[{correlation_id}] Session not found or expired: {session_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found or expired: {session_id}",
                )

            # Session exists but image not found
            logger.error(f"[{correlation_id}] Image not found: {image_url}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image not found: {image_id}",
            )

        logger.info(f"[{correlation_id}] Returning image, size: {len(image_data)} bytes")

        # Return image as PNG
        return Response(
            content=image_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Length": str(len(image_data)),
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.exception(f"[{correlation_id}] Unexpected error retrieving image")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )
