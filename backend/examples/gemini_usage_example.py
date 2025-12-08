"""Example usage of GeminiClient for text generation.

This script demonstrates how to use the GeminiClient to generate
stylized greeting card text in different styles.

Run with:
    python -m examples.gemini_usage_example
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.integrations import GeminiClient
from src.integrations.exceptions import (
    GeminiTextGenerationError,
    GeminiRateLimitError,
    GeminiConfigError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Main example function demonstrating GeminiClient usage."""

    # Initialize the client
    try:
        client = GeminiClient(api_key=settings.gemini_api_key)
        logger.info("✅ Gemini client initialized successfully")
    except GeminiConfigError as e:
        logger.error(f"❌ Configuration error: {e}")
        return

    # Example recipient data
    recipient = "Анна Смирнова"
    reason = "блестящую организацию новогоднего корпоратива"
    message = "Спасибо за создание праздничного настроения!"

    # Test all text styles
    styles = ["ode", "future", "haiku", "newspaper", "standup"]

    for style in styles:
        logger.info(f"\n{'='*80}")
        logger.info(f"Generating text in style: {style}")
        logger.info(f"{'='*80}\n")

        try:
            # Generate text
            text = await client.generate_text(
                prompt="",  # Empty prompt - style template is used
                style=style,
                recipient=recipient,
                reason=reason,
                message=message,
            )

            # Display result
            logger.info(f"✅ Generated text ({len(text)} chars):")
            logger.info(f"\n{text}\n")

        except GeminiRateLimitError as e:
            logger.warning(f"⚠️  Rate limit exceeded: {e}")
            retry_after = e.details.get("retry_after", 60)
            logger.info(f"Waiting {retry_after} seconds before continuing...")
            await asyncio.sleep(retry_after)

        except GeminiTextGenerationError as e:
            logger.error(f"❌ Text generation failed: {e}")
            if e.original_error:
                logger.error(f"Original error: {e.original_error}")

        except Exception as e:
            logger.exception(f"❌ Unexpected error: {e}")

        # Small delay between requests to avoid rate limiting
        await asyncio.sleep(2)

    # Test image generation (will raise NotImplementedError)
    logger.info(f"\n{'='*80}")
    logger.info("Testing image generation")
    logger.info(f"{'='*80}\n")

    try:
        image_bytes = await client.generate_image(
            recipient=recipient,
            reason=reason,
            style="digital_art",
        )
        logger.info(f"✅ Image generated: {len(image_bytes)} bytes")
    except NotImplementedError as e:
        logger.warning(f"⚠️  Image generation not implemented: {e}")
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")

    # Cleanup
    await client.close()
    logger.info("\n✅ Example completed successfully")


if __name__ == "__main__":
    # Run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)
