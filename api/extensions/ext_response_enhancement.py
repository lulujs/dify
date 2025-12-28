"""Response Enhancement Extension.

This extension initializes the response enhancement middleware for the Dify application.
"""

import logging

from core.response_enhancement import init_middleware
from core.response_enhancement.processors import MetadataProcessor, StandardFormatProcessor
from core.response_enhancement.registry import get_registry
from dify_app import DifyApp

logger = logging.getLogger(__name__)


def init_app(app: DifyApp) -> None:
    """Initialize response enhancement for the application.

    Args:
        app: The Dify application instance.
    """
    try:
        # Register built-in processors
        _register_processors()

        # Initialize middleware
        init_middleware(app)

        logger.info("Response enhancement extension initialized successfully")

    except Exception:
        logger.exception("Failed to initialize response enhancement extension")
        raise


def _register_processors() -> None:
    """Register built-in response processors."""
    registry = get_registry()

    # Register metadata processor
    if not registry.get("metadata"):
        registry.register("metadata", MetadataProcessor(api_version="1.0"))
        logger.debug("Registered metadata processor")

    # Register standard format processor
    if not registry.get("standard_format"):
        registry.register("standard_format", StandardFormatProcessor())
        logger.debug("Registered standard_format processor")

    logger.info("Response enhancement processors registered")


def is_enabled() -> bool:
    """Check if response enhancement extension should be enabled.

    Returns:
        True if the extension should be enabled, False otherwise.
    """
    try:
        from core.response_enhancement.config import get_config

        config = get_config()
        return config.get_global_config().enabled

    except Exception as e:
        logger.warning("Failed to check response enhancement config, defaulting to disabled: %s", e)
        return False
