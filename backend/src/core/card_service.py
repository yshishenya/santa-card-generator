"""Card generation service for creating and managing greeting cards.

This module provides the main business logic for generating greeting cards,
managing regeneration sessions, and sending cards to Telegram.

New architecture:
- Generates 5 text variants (one per AI style) in parallel
- Generates 4 image variants (one per style) in parallel
- Regeneration replaces ALL variants of a type
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Protocol, Tuple

from src.core.exceptions import (
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    VariantNotFoundError,
)
from src.core.session_manager import GenerationSession, SessionManager
from src.models.card import (
    AI_TEXT_STYLES,
    ALL_IMAGE_STYLES,
    CardGenerationRequest,
    CardGenerationResponse,
    ImageStyle,
    ImageVariant,
    SendCardRequest,
    SendCardResponse,
    TextStyle,
    TextVariant,
)
from src.models.response import RegenerateResponse
from src.repositories.employee_repo import EmployeeRepository

logger = logging.getLogger(__name__)


class GeminiClient(Protocol):
    """Protocol for Gemini API client.

    This protocol defines the interface that the Gemini client must implement
    for text and image generation operations.
    """

    async def generate_text(
        self,
        prompt: str,
        style: str,
        recipient: str,
        reason: str | None = None,
        message: str | None = None,
    ) -> str:
        """Generate greeting text for a recipient.

        Args:
            prompt: Base prompt for generation.
            style: Style of text to generate.
            recipient: Name of the card recipient.
            reason: Optional reason for gratitude.
            message: Optional custom message.

        Returns:
            Generated greeting text.
        """
        ...

    async def generate_image(
        self,
        recipient: str,
        reason: str | None,
        style: str,
    ) -> Tuple[bytes, str]:
        """Generate greeting image for a recipient.

        Args:
            recipient: Name of the card recipient.
            reason: Optional reason for gratitude.
            style: Style of image to generate.

        Returns:
            Tuple of (image_bytes, prompt_used).
        """
        ...


class TelegramClient(Protocol):
    """Protocol for Telegram Bot API client.

    This protocol defines the interface that the Telegram client must implement
    for sending messages with images.
    """

    async def send_card(
        self,
        image_bytes: bytes,
        recipient: str,
        reason: str | None,
        message: str,
        sender: str | None,
        correlation_id: str | None = None,
        original_message: str | None = None,
    ) -> int:
        """Send a greeting card to Telegram.

        Args:
            image_bytes: Image data to send.
            recipient: Name of the card recipient.
            reason: Reason for gratitude (optional).
            message: The greeting message text (or AI text if original_message provided).
            sender: Name of the sender (optional, anonymous if None).
            correlation_id: Correlation ID for logging.
            original_message: Original user text to include alongside AI text.

        Returns:
            Telegram message ID.
        """
        ...


class CardService:
    """Service for generating and managing greeting cards.

    This service orchestrates the card generation workflow:
    - Validating recipients against the employee list
    - Generating 5 text variants (one per AI style) using Gemini
    - Generating 4 image variants (one per style) using Gemini
    - Managing generation sessions with regeneration limits
    - Sending completed cards to Telegram
    """

    def __init__(
        self,
        gemini_client: GeminiClient,
        telegram_client: TelegramClient,
        employee_repo: EmployeeRepository,
        max_regenerations: int = 3,
        session_ttl_minutes: int = 30,
    ) -> None:
        """Initialize the card service with required dependencies.

        Args:
            gemini_client: Client for Gemini API operations.
            telegram_client: Client for Telegram Bot API operations.
            employee_repo: Repository for employee data access.
            max_regenerations: Maximum number of regenerations allowed per element type.
            session_ttl_minutes: Time-to-live for sessions in minutes.
        """
        self._gemini_client = gemini_client
        self._telegram_client = telegram_client
        self._employee_repo = employee_repo
        self._session_manager = SessionManager(
            max_regenerations=max_regenerations,
            session_ttl_minutes=session_ttl_minutes,
        )
        self._max_regenerations = max_regenerations
        self._session_ttl_minutes = session_ttl_minutes

        logger.info(
            f"Initialized CardService with max_regenerations={max_regenerations}, "
            f"session_ttl={session_ttl_minutes}min"
        )

    def get_session(self, session_id: str) -> Optional[GenerationSession]:
        """Get session by ID.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            GenerationSession if found and not expired, None otherwise.
        """
        return self._session_manager.get_session(session_id)

    def get_image_data(self, session_id: str, image_url: str) -> bytes | None:
        """Get image data from session.

        Args:
            session_id: Session ID containing the image.
            image_url: Image URL identifier.

        Returns:
            Image bytes if found, None otherwise.
        """
        return self._session_manager.get_image_data(session_id, image_url)

    async def generate_card(
        self, request: CardGenerationRequest
    ) -> CardGenerationResponse:
        """Generate a new card with text and image variants.
        
        Args:
            request: Card generation request containing employee name.
        
        Returns:
            CardGenerationResponse with session ID and all variants.
        
        Raises:
            RecipientNotFoundError: If the employee is not found in the system.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Starting card generation for recipient: {request.recipient}"
        )

        # Validate recipient exists in employee list
        employee = await self._employee_repo.get_by_name(request.recipient)
        if employee is None:
            logger.error(
                f"[{correlation_id}] Employee not found: {request.recipient}"
            )
            raise RecipientNotFoundError(request.recipient)

        logger.info(
            f"[{correlation_id}] Validated employee: {employee.name} (id: {employee.id})"
        )

        # Store original text from user
        original_text = request.message

        # Generate text and image variants in parallel
        try:
            logger.info(
                f"[{correlation_id}] Generating 5 text variants and 4 image variants"
            )

            # Generate all text variants (5 AI styles) and image variants (4 styles)
            text_task = self._generate_text_variants(
                request=request, correlation_id=correlation_id
            )
            image_task = self._generate_image_variants(
                request=request, correlation_id=correlation_id
            )

            text_variants, image_results = await asyncio.gather(text_task, image_task)

            # Unpack image results (variants and raw data)
            image_variants: List[ImageVariant] = []
            image_data: Dict[str, bytes] = {}

            for variant, image_bytes in image_results:
                image_variants.append(variant)
                image_data[variant.url] = image_bytes

            logger.info(
                f"[{correlation_id}] Generated {len(text_variants)} text variants "
                f"and {len(image_variants)} image variants"
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error generating variants: {e}")
            raise

        # Create session for regeneration tracking
        session_id = self._session_manager.create_session(
            request=request,
            original_text=original_text,
            text_variants=text_variants,
            image_variants=image_variants,
            image_data=image_data,
        )

        logger.info(
            f"[{correlation_id}] Created session {session_id} for {request.recipient}"
        )

        return CardGenerationResponse(
            session_id=session_id,
            recipient=request.recipient,
            original_text=original_text,
            text_variants=text_variants,
            image_variants=image_variants,
            remaining_text_regenerations=self._max_regenerations,
            remaining_image_regenerations=self._max_regenerations,
        )

    async def regenerate_text(self, session_id: str) -> RegenerateResponse:
        """Regenerates all text variants for a given session.
        
        This asynchronous function retrieves the session using the provided  session_id
        and checks for its validity, including expiration and  regeneration limits. If
        the session is valid, it generates five new  text variants based on the
        original request and updates the session  with these new variants. It logs the
        process and handles any  exceptions that may arise during regeneration.
        
        Args:
            session_id: Session ID from initial generation.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Regenerating ALL texts for session: {session_id}"
        )

        # Get session
        session = self._session_manager.get_session(session_id)
        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {session_id}")
            raise SessionNotFoundError(session_id)

        if session.is_expired(self._session_ttl_minutes):
            logger.error(f"[{correlation_id}] Session expired: {session_id}")
            raise SessionExpiredError(session_id)

        # Check regeneration limit
        if session.text_regenerations_left <= 0:
            logger.error(
                f"[{correlation_id}] Regeneration limit exceeded for text in session {session_id}"
            )
            raise RegenerationLimitExceededError("text", self._max_regenerations)

        # Generate all 5 new text variants
        try:
            original_request = session.original_request
            new_variants = await self._generate_text_variants(
                request=original_request, correlation_id=correlation_id
            )

            # Replace all variants in session
            remaining = self._session_manager.replace_text_variants(
                session_id, new_variants
            )

            logger.info(
                f"[{correlation_id}] Regenerated {len(new_variants)} text variants, "
                f"remaining={remaining}"
            )

            return RegenerateResponse(
                text_variants=new_variants,
                image_variants=None,
                remaining_regenerations=remaining,
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error regenerating text: {e}")
            raise

    async def regenerate_image(self, session_id: str) -> RegenerateResponse:
        """Regenerates all image variants for a given session.
        
        This asynchronous function retrieves the session using the provided session_id
        and checks for its validity, including expiration and regeneration limits. If
        the session is valid, it generates four new image variants based on the
        original  request and updates the session with these new variants. The function
        handles  exceptions and logs relevant information throughout the process.
        
        Args:
            session_id: Session ID from initial generation.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Regenerating ALL images for session: {session_id}"
        )

        # Get session
        session = self._session_manager.get_session(session_id)
        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {session_id}")
            raise SessionNotFoundError(session_id)

        if session.is_expired(self._session_ttl_minutes):
            logger.error(f"[{correlation_id}] Session expired: {session_id}")
            raise SessionExpiredError(session_id)

        # Check regeneration limit
        if session.image_regenerations_left <= 0:
            logger.error(
                f"[{correlation_id}] Regeneration limit exceeded for image in session {session_id}"
            )
            raise RegenerationLimitExceededError("image", self._max_regenerations)

        # Generate all 4 new image variants
        try:
            original_request = session.original_request
            image_results = await self._generate_image_variants(
                request=original_request, correlation_id=correlation_id
            )

            # Unpack results
            new_variants: List[ImageVariant] = []
            new_image_data: Dict[str, bytes] = {}

            for variant, image_bytes in image_results:
                new_variants.append(variant)
                new_image_data[variant.url] = image_bytes

            # Replace all variants in session
            remaining = self._session_manager.replace_image_variants(
                session_id, new_variants, new_image_data
            )

            logger.info(
                f"[{correlation_id}] Regenerated {len(new_variants)} image variants, "
                f"remaining={remaining}"
            )

            return RegenerateResponse(
                text_variants=None,
                image_variants=new_variants,
                remaining_regenerations=remaining,
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error regenerating images: {e}")
            raise

    async def send_card(self, request: SendCardRequest) -> SendCardResponse:
        """Send selected card to Telegram.
        
        This method retrieves the selected text and image from the session and sends
        them as a greeting card message to Telegram. It validates the session, checks
        for expiration, and determines the appropriate text and image to use based on
        user input. If any required data is missing or invalid, it raises the
        corresponding exceptions.
        
        Args:
            request (SendCardRequest): Request containing session ID and selected variant indices.
        
        Returns:
            SendCardResponse: Response with success status and Telegram message ID.
        
        Raises:
            SessionNotFoundError: If session ID is not found.
            SessionExpiredError: If the session has expired.
            VariantNotFoundError: If selected variant index is invalid.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Sending card for session: {request.session_id}"
        )

        # Get session
        session = self._session_manager.get_session(request.session_id)
        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {request.session_id}")
            raise SessionNotFoundError(request.session_id)

        if session.is_expired(self._session_ttl_minutes):
            logger.error(f"[{correlation_id}] Session expired: {request.session_id}")
            raise SessionExpiredError(request.session_id)

        original_request = session.original_request
        if original_request is None:
            logger.error(f"[{correlation_id}] Original request not found in session")
            return SendCardResponse(
                success=False,
                message="Session data is corrupted",
                telegram_message_id=None,
            )

        # Determine which text to use
        message_text: str
        original_message_for_telegram: Optional[str] = None

        if request.use_original_text:
            # User wants to use their original text only
            if session.original_text:
                message_text = session.original_text
                logger.info(f"[{correlation_id}] Using original user text")
            else:
                # No original text, use default
                message_text = f"Поздравляю, {original_request.recipient}!"
                logger.info(f"[{correlation_id}] No original text, using default")
        else:
            # User selected an AI variant
            if request.selected_text_index >= len(session.text_variants):
                logger.error(
                    f"[{correlation_id}] Text variant not found at index: {request.selected_text_index}"
                )
                raise VariantNotFoundError("text", request.selected_text_index)

            selected_text = session.text_variants[request.selected_text_index]
            message_text = selected_text.text
            logger.info(
                f"[{correlation_id}] Using AI text variant index={request.selected_text_index}, "
                f"style={selected_text.style.value}"
            )

            # Check if we should also include original text alongside AI text
            if request.include_original_text and session.original_text:
                original_message_for_telegram = session.original_text
                logger.info(
                    f"[{correlation_id}] Including original text alongside AI text"
                )

        # Validate and get selected image variant
        if request.selected_image_index >= len(session.image_variants):
            logger.error(
                f"[{correlation_id}] Image variant not found at index: {request.selected_image_index}"
            )
            raise VariantNotFoundError("image", request.selected_image_index)

        selected_image = session.image_variants[request.selected_image_index]

        # Get image data
        image_data = self._session_manager.get_image_data(
            request.session_id, selected_image.url
        )

        if image_data is None:
            logger.error(
                f"[{correlation_id}] Image data not found for {selected_image.url}"
            )
            raise VariantNotFoundError("image", request.selected_image_index)

        # Send to Telegram
        try:
            message_id = await self._telegram_client.send_card(
                image_bytes=image_data,
                recipient=original_request.recipient,
                reason=original_request.reason,
                message=message_text,
                sender=original_request.sender,
                correlation_id=correlation_id,
                original_message=original_message_for_telegram,
            )

            logger.info(
                f"[{correlation_id}] Successfully sent card for {original_request.recipient}, "
                f"message_id={message_id}"
            )

            return SendCardResponse(
                success=True,
                message="Card sent successfully",
                telegram_message_id=message_id,
            )

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error sending card to Telegram: {e}")
            return SendCardResponse(
                success=False,
                message=f"Failed to send card: {str(e)}",
                telegram_message_id=None,
            )

    async def _generate_text_variants(
        self, request: CardGenerationRequest, correlation_id: str
    ) -> List[TextVariant]:
        """Generate 5 text variants in parallel for different AI styles.
        
        Args:
            request: Card generation request.
            correlation_id: Correlation ID for logging.
        
        Returns:
            List of 5 TextVariant objects (ode, haiku, future, standup, newspaper).
        """
        logger.debug(
            f"[{correlation_id}] Generating 5 text variants for {request.recipient}"
        )

        # Generate one variant per AI style in parallel
        tasks = [
            self._gemini_client.generate_text(
                prompt="",
                style=style.value,
                recipient=request.recipient,
                reason=request.reason,
                message=request.message,
            )
            for style in AI_TEXT_STYLES
        ]

        texts = await asyncio.gather(*tasks)

        # Create variants with their respective styles
        variants = [
            TextVariant(text=text, style=style)
            for text, style in zip(texts, AI_TEXT_STYLES)
        ]

        logger.debug(
            f"[{correlation_id}] Generated {len(variants)} text variants "
            f"(styles: {[v.style.value for v in variants]})"
        )

        return variants

    async def _generate_image_variants(
        self, request: CardGenerationRequest, correlation_id: str
    ) -> List[Tuple[ImageVariant, bytes]]:
        """Generate image variants in parallel for a card generation request.
        
        This function generates four image variants, one for each style defined in
        ALL_IMAGE_STYLES, using asynchronous calls to the _gemini_client. It handles
        partial failures gracefully, ensuring that at least one image must succeed.  If
        some images fail to generate, the function logs the failures and returns  only
        the successful ones.
        
        Args:
            request: Card generation request.
            correlation_id: Correlation ID for logging.
        """
        logger.debug(
            f"[{correlation_id}] Generating 4 image variants for {request.recipient}"
        )

        # Generate one variant per image style in parallel
        tasks = [
            self._gemini_client.generate_image(
                recipient=request.recipient,
                reason=request.reason,
                style=style.value,
            )
            for style in ALL_IMAGE_STYLES
        ]

        # Use return_exceptions=True to handle partial failures
        image_results = await asyncio.gather(*tasks, return_exceptions=True)

        variants: List[Tuple[ImageVariant, bytes]] = []
        failed_styles: List[str] = []

        for result, style in zip(image_results, ALL_IMAGE_STYLES):
            if isinstance(result, Exception):
                # Log the failure but continue with other images
                logger.warning(
                    f"[{correlation_id}] Failed to generate image for style {style.value}: {result}"
                )
                failed_styles.append(style.value)
                continue

            image_bytes, prompt = result
            # Create unique URL for each image
            image_id = str(uuid.uuid4())
            image_url = f"generated://{image_id}"

            variant = ImageVariant(
                url=image_url,
                style=style,
                prompt=prompt,
            )

            variants.append((variant, image_bytes))

        # If all images failed, raise an error
        if not variants:
            raise Exception(
                f"All image generations failed. Styles attempted: {failed_styles}"
            )

        if failed_styles:
            logger.warning(
                f"[{correlation_id}] Partial image generation: {len(variants)} succeeded, "
                f"{len(failed_styles)} failed (styles: {failed_styles})"
            )

        logger.debug(
            f"[{correlation_id}] Generated {len(variants)} image variants "
            f"(styles: {[v.style.value for v, _ in variants]})"
        )

        return variants
