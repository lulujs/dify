"""Response Enhancement Framework for Service API.

This module provides both decorator-based and middleware-based response enhancement
that allows post-processing of API responses without modifying existing business logic.
The middleware approach is recommended for new implementations.
"""

from .config import EndpointConfig, EnhancementConfig, GlobalConfig
from .context import ProcessingContext
from .decorator import get_config, get_error_handler, response_enhancer
from .error_handler import EnhancementErrorHandler
from .middleware import ResponseEnhancementMiddleware, get_middleware, init_middleware
from .processor import PostProcessor
from .processors import MetadataProcessor, StandardFormatProcessor
from .registry import PostProcessorRegistry, get_registry

__all__ = [
    "EndpointConfig",
    "EnhancementConfig",
    "EnhancementErrorHandler",
    "GlobalConfig",
    "MetadataProcessor",
    "PostProcessor",
    "PostProcessorRegistry",
    "ProcessingContext",
    "ResponseEnhancementMiddleware",
    "StandardFormatProcessor",
    "get_config",
    "get_error_handler",
    "get_middleware",
    "get_registry",
    "init_middleware",
    "response_enhancer",
]
