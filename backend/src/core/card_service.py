"""Card generation service for creating and managing greeting cards.

This module provides the main business logic for generating greeting cards,
managing regeneration sessions, and sending cards to Telegram.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Protocol, Tuple

from src.core.exceptions import (
    RecipientNotFoundError,
    RegenerationLimitExceededError,
    SessionExpiredError,
    SessionNotFoundError,
    VariantNotFoundError,
)
from src.core.session_manager import SessionManager
from src.models.card import (
    CardGenerationRequest,
    CardGenerationResponse,
    ImageVariant,
    SendCardRequest,
    SendCardResponse,
    TextVariant,
)
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
    ) -> int:
        """Send a greeting card to Telegram.

        Args:
            image_bytes: Image data to send.
            recipient: Name of the card recipient.
            reason: Reason for gratitude (optional).
            message: The greeting message text.
            sender: Name of the sender (optional, anonymous if None).
            correlation_id: Correlation ID for logging.

        Returns:
            Telegram message ID.
        """
        ...


class CardService:
    """Service for generating and managing greeting cards.

    This service orchestrates the card generation workflow, including:
    - Validating recipients against the employee list
    - Generating text and image variants using Gemini
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
            max_regenerations: Maximum number of regenerations allowed per element.
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

    def get_session(self, session_id: str) -> "GenerationSession | None":
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

        This method performs the following operations:
        1. Validates that the recipient exists in the employee list
        2. Generates 3 text variants (or uses original text if enhance_text is False)
        3. Generates 3 image variants in parallel
        4. Creates a session to store the variants and track regenerations
        5. Returns the response with all variants

        Args:
            request: Card generation request containing employee name and styles.

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

        # Generate text and image variants
        try:
            text_style_value = request.text_style.value if request.text_style else None
            logger.info(
                f"[{correlation_id}] Generating variants: "
                f"enhance_text={request.enhance_text}, "
                f"text_style={text_style_value}, "
                f"image_style={request.image_style.value}"
            )

            # Generate text variants (AI-enhanced or original message)
            text_task = self._generate_text_variants(
                request=request, correlation_id=correlation_id
            )
            # Generate image variants
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
            text_variants=text_variants,
            image_variants=image_variants,
            remaining_regenerations=self._max_regenerations,
        )

    async def regenerate_text(
        self, generation_id: str, original_request: CardGenerationRequest
    ) -> Tuple[TextVariant, int]:
        """Regenerate a text variant and return the new variant with remaining count.

        Args:
            generation_id: Session ID from initial generation.
            original_request: Original card generation request.

        Returns:
            Tuple of (new TextVariant, remaining regenerations count).

        Raises:
            SessionNotFoundError: If session ID is not found.
            SessionExpiredError: If the session has expired.
            RegenerationLimitExceededError: If regeneration limit exceeded.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Regenerating text for session: {generation_id}"
        )

        # Get session
        session = self._session_manager.get_session(generation_id)
        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {generation_id}")
            raise SessionNotFoundError(generation_id)

        if session.is_expired(self._session_ttl_minutes):
            logger.error(f"[{correlation_id}] Session expired: {generation_id}")
            raise SessionExpiredError(generation_id)

        # Check regeneration limit
        if session.text_regenerations_left <= 0:
            logger.error(
                f"[{correlation_id}] Regeneration limit exceeded for text in session {generation_id}"
            )
            raise RegenerationLimitExceededError("text", self._max_regenerations)

        # Generate new text variant
        try:
            text = await self._gemini_client.generate_text(
                prompt="",  # Will be built inside
                style=original_request.text_style.value if original_request.text_style else "ode",
                recipient=original_request.recipient,
                reason=original_request.reason,
                message=original_request.message,
            )

            new_variant = TextVariant(
                text=text, style=original_request.text_style or "ode"
            )

            # Add to session and get remaining count
            remaining = self._session_manager.add_text_variant(generation_id, new_variant)

            logger.info(
                f"[{correlation_id}] Regenerated text for session {generation_id}, "
                f"remaining={remaining}"
            )

            return new_variant, remaining

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error regenerating text: {e}")
            raise

    async def regenerate_image(
        self, generation_id: str, original_request: CardGenerationRequest
    ) -> Tuple[ImageVariant, int]:
        """Regenerate an image variant and return the new variant with remaining count.

        Args:
            generation_id: Session ID from initial generation.
            original_request: Original card generation request.

        Returns:
            Tuple of (new ImageVariant, remaining regenerations count).

        Raises:
            SessionNotFoundError: If session ID is not found.
            SessionExpiredError: If the session has expired.
            RegenerationLimitExceededError: If regeneration limit exceeded.
        """
        correlation_id = str(uuid.uuid4())
        logger.info(
            f"[{correlation_id}] Regenerating image for session: {generation_id}"
        )

        # Get session
        session = self._session_manager.get_session(generation_id)
        if session is None:
            logger.error(f"[{correlation_id}] Session not found: {generation_id}")
            raise SessionNotFoundError(generation_id)

        if session.is_expired(self._session_ttl_minutes):
            logger.error(f"[{correlation_id}] Session expired: {generation_id}")
            raise SessionExpiredError(generation_id)

        # Check regeneration limit
        if session.image_regenerations_left <= 0:
            logger.error(
                f"[{correlation_id}] Regeneration limit exceeded for image in session {generation_id}"
            )
            raise RegenerationLimitExceededError("image", self._max_regenerations)

        # Generate new image variant
        try:
            image_bytes, prompt = await self._gemini_client.generate_image(
                recipient=original_request.recipient,
                reason=original_request.reason,
                style=original_request.image_style.value,
            )

            # Create unique URL for the image (using UUID)
            image_id = str(uuid.uuid4())
            image_url = f"generated://{image_id}"

            new_variant = ImageVariant(
                url=image_url,
                style=original_request.image_style,
                prompt=prompt,
            )

            # Add to session and get remaining count
            remaining = self._session_manager.add_image_variant(
                generation_id, new_variant, image_bytes
            )

            logger.info(
                f"[{correlation_id}] Regenerated image for session {generation_id}, "
                f"remaining={remaining}"
            )

            return new_variant, remaining

        except Exception as e:
            logger.exception(f"[{correlation_id}] Error regenerating image: {e}")
            raise

    async def send_card(self, request: SendCardRequest) -> SendCardResponse:
        """Send selected card to Telegram.

        This method retrieves the selected text and image from the session
        and sends them as a greeting card message to Telegram.

        Args:
            request: Request containing session ID and selected variant indices.

        Returns:
            SendCardResponse with success status and Telegram message ID.

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

        # Validate and get selected text variant
        if request.selected_text_index >= len(session.text_variants):
            logger.error(
                f"[{correlation_id}] Text variant not found at index: {request.selected_text_index}"
            )
            raise VariantNotFoundError("text", request.selected_text_index)

        selected_text = session.text_variants[request.selected_text_index]

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
        # Get sender info from original request in session
        original_request = session.original_request
        try:
            message_id = await self._telegram_client.send_card(
                image_bytes=image_data,
                recipient=request.employee_name,
                reason=original_request.reason if original_request else None,
                message=selected_text.text,
                sender=original_request.sender if original_request else None,
                correlation_id=correlation_id,
            )

            logger.info(
                f"[{correlation_id}] Successfully sent card for {request.employee_name}, "
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
        """Generate text variants - either AI-enhanced or original message.

        Args:
            request: Card generation request.
            correlation_id: Correlation ID for logging.

        Returns:
            List of TextVariant objects.
        """
        if not request.enhance_text:
            # Use original message without AI enhancement
            original_text = request.message or f"Поздравляю, {request.recipient}!"
            logger.debug(
                f"[{correlation_id}] Using original message for {request.recipient}"
            )
            return [TextVariant(text=original_text, style="original")]

        # Generate AI-enhanced text variants
        text_style = request.text_style.value if request.text_style else "ode"
        logger.debug(
            f"[{correlation_id}] Generating 3 text variants for {request.recipient} "
            f"in style: {text_style}"
        )

        # Generate 3 variants in parallel
        tasks = [
            self._gemini_client.generate_text(
                prompt="",
                style=text_style,
                recipient=request.recipient,
                reason=request.reason,
                message=request.message,
            )
            for _ in range(3)
        ]
        texts = await asyncio.gather(*tasks)

        variants = [
            TextVariant(text=text, style=text_style)
            for text in texts
        ]

        logger.debug(
            f"[{correlation_id}] Generated {len(variants)} text variants"
        )

        return variants

    async def _generate_image_variants(
        self, request: CardGenerationRequest, correlation_id: str
    ) -> List[Tuple[ImageVariant, bytes]]:
        """Generate 3 image variants using Gemini.

        Args:
            request: Card generation request.
            correlation_id: Correlation ID for logging.

        Returns:
            List of 3 tuples containing (ImageVariant, image_bytes).
        """
        image_style = request.image_style.value
        logger.debug(
            f"[{correlation_id}] Generating 3 image variants for {request.recipient} "
            f"in style: {image_style}"
        )

        # Generate 3 variants in parallel
        tasks = [
            self._gemini_client.generate_image(
                recipient=request.recipient,
                reason=request.reason,
                style=image_style,
            )
            for _ in range(3)
        ]
        image_results = await asyncio.gather(*tasks)

        variants: List[Tuple[ImageVariant, bytes]] = []
        for i, (image_bytes, prompt) in enumerate(image_results):
            # Create unique URL for each image
            image_id = str(uuid.uuid4())
            image_url = f"generated://{image_id}"

            variant = ImageVariant(
                url=image_url,
                style=image_style,
                prompt=prompt,
            )

            variants.append((variant, image_bytes))

        logger.debug(
            f"[{correlation_id}] Generated {len(variants)} image variants"
        )

        return variants
