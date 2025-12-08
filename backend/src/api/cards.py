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

from fastapi import APIRouter, Depends, HTTPException, Response, status

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

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/cards/generate", response_model=APIResponse[CardGenerationResponse])
async def generate_card(
    request: CardGenerationRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[CardGenerationResponse]:
    """Generate a new greeting card with text and image variants.

    This endpoint creates a new card generation session and produces:
    - 3 text variants in the specified style
    - 3 image variants in the specified style

    The session ID returned can be used for regeneration and sending operations.

    Args:
        request: Card generation request with employee name and styles.
        service: Injected CardService instance.

    Returns:
        APIResponse containing CardGenerationResponse with session ID and all variants.

    Raises:
        HTTPException 404: If employee is not found in the system.
        HTTPException 500: If generation fails due to internal error.
    """
    correlation_id = str(uuid4())
    text_style_value = request.text_style.value if request.text_style else "none"
    logger.info(
        f"[{correlation_id}] POST /cards/generate - recipient: {request.recipient}, "
        f"enhance_text: {request.enhance_text}, text_style: {text_style_value}, "
        f"image_style: {request.image_style.value}"
    )

    try:
        response = await service.generate_card(request)
        logger.info(
            f"[{correlation_id}] Card generated successfully, session: {response.session_id}"
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
async def regenerate_variant(
    request: RegenerateRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[RegenerateResponse]:
    """Regenerate a text or image variant.

    This endpoint regenerates a specific variant within an existing session.
    The regeneration count is tracked per element type (text/image) separately.

    Args:
        request: Regeneration request with session ID and element details.
        service: Injected CardService instance.

    Returns:
        APIResponse containing RegenerateResponse with new variant and remaining count.

    Raises:
        HTTPException 404: If session or variant is not found.
        HTTPException 400: If session has expired.
        HTTPException 429: If regeneration limit has been exceeded.
        HTTPException 500: If regeneration fails due to internal error.
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] POST /cards/regenerate - session: {request.session_id}, "
        f"element: {request.element_type}, index: {request.element_index}"
    )

    try:
        # Get the original request from session to use for regeneration
        # We need to retrieve it first to know the styles
        session_manager = service._session_manager
        session = session_manager.get_session(request.session_id)

        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {request.session_id}")
            raise SessionNotFoundError(request.session_id)

        if session.is_expired(30):
            logger.error(f"[{correlation_id}] Session expired: {request.session_id}")
            raise SessionExpiredError(request.session_id)

        # Regenerate based on element type
        if request.element_type == "text":
            new_variant, remaining = await service.regenerate_text(
                generation_id=request.session_id,
                original_request=session.original_request,
            )
        elif request.element_type == "image":
            new_variant, remaining = await service.regenerate_image(
                generation_id=request.session_id,
                original_request=session.original_request,
            )
        else:
            logger.error(f"[{correlation_id}] Invalid element type: {request.element_type}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid element type: {request.element_type}",
            )

        logger.info(
            f"[{correlation_id}] Regenerated {request.element_type} successfully, "
            f"remaining: {remaining}"
        )

        return APIResponse(
            success=True,
            data=RegenerateResponse(variant=new_variant, remaining_regenerations=remaining),
            error=None,
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
async def send_card(
    request: SendCardRequest,
    service: Annotated[CardService, Depends(get_card_service)],
) -> APIResponse[SendCardResponse]:
    """Send selected card to Telegram.

    This endpoint sends the selected text and image variant to the configured
    Telegram chat/topic. The card is formatted as a photo message with the
    greeting text as caption.

    Args:
        request: Send request with session ID and selected variant indices.
        service: Injected CardService instance.

    Returns:
        APIResponse containing SendCardResponse with success status and message ID.

    Raises:
        HTTPException 404: If session or variant is not found.
        HTTPException 400: If session has expired.
        HTTPException 500: If sending fails due to internal error.
    """
    correlation_id = str(uuid4())
    logger.info(
        f"[{correlation_id}] POST /cards/send - session: {request.session_id}, "
        f"employee: {request.employee_name}, text_idx: {request.selected_text_index}, "
        f"image_idx: {request.selected_image_index}"
    )

    try:
        send_response = await service.send_card(request)

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

        # Get image data from session manager
        image_data = service._session_manager.get_image_data(session_id, image_url)

        if image_data is None:
            # Check if session exists
            session = service._session_manager.get_session(session_id)
            if session is None:
                logger.error(f"[{correlation_id}] Session not found: {session_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Session not found: {session_id}",
                )

            if session.is_expired(30):
                logger.error(f"[{correlation_id}] Session expired: {session_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Session expired: {session_id}",
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
