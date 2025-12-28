"""Response Enhancement Framework for Service API.

This module provides a decorator-based response enhancement framework that allows
post-processing of API responses without modifying existing business logic.
"""

from .config import EndpointConfig, EnhancementConfig, GlobalConfig
from .context import ProcessingContext
from .decorator import get_config, get_error_handler, get_registry, response_enhancer
from .error_handler import EnhancementErrorHandler
from .processor import PostProcessor
from .processors import MetadataProcessor, StandardFormatProcessor
from .registry import PostProcessorRegistry

__all__ = [
    "EndpointConfig",
    "EnhancementConfig",
    "EnhancementErrorHandler",
    "GlobalConfig",
    "MetadataProcessor",
    "PostProcessor",
    "PostProcessorRegistry",
    "ProcessingContext",
    "StandardFormatProcessor",
    "get_config",
    "get_error_handler",
    "get_registry",
    "response_enhancer",
]
