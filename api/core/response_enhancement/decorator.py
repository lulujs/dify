"""Response enhancement decorator for Service API endpoints."""

import functools
import json
import logging
import time
from collections.abc import Callable, Generator, Mapping
from typing import Any, Optional

from flask import Response, request
from werkzeug.wrappers import Response as WerkzeugResponse

from .config import get_config
from .context import ProcessingContext
from .error_handler import EnhancementErrorHandler
from .registry import PostProcessorRegistry

logger = logging.getLogger(__name__)

# Global instances
_registry = PostProcessorRegistry()
_error_handler = EnhancementErrorHandler()


def get_registry() -> PostProcessorRegistry:
    """Get the global post-processor registry."""
    return _registry


def get_error_handler() -> EnhancementErrorHandler:
    """Get the global error handler."""
    return _error_handler


def response_enhancer(
    processors: Optional[list[str]] = None,
    enabled: bool = True,
    fail_silently: bool = True,
    config_key: Optional[str] = None,
) -> Callable:
    """Decorator to add response enhancement to API endpoints.

    This decorator wraps API endpoint methods to provide post-processing
    capabilities. It executes a pipeline of processors on the response
    before returning it to the client.

    Args:
        processors: List of processor names to apply. If None, uses configuration.
        enabled: Whether enhancement is enabled for this endpoint.
        fail_silently: Whether to continue on processor errors.
        config_key: Configuration key for endpoint-specific settings.

    Returns:
        Decorated function that applies response enhancement.

    Example:
        @response_enhancer(processors=['metadata', 'timing'])
        def post(self, app_model: App, end_user: EndUser):
            return original_response
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Get current configuration
            config = get_config()

            # Check if enhancement is enabled
            endpoint_path = _get_endpoint_path(func)
            if not enabled or not config.is_enabled(endpoint_path):
                return func(*args, **kwargs)

            # Record start time for timing information
            start_time = time.time()

            # Execute original function
            original_response = func(*args, **kwargs)

            try:
                # Detect response type and determine if we can process it
                response_type = _detect_response_type(original_response)

                # Extract context information from function arguments
                context = _extract_context(func, args, kwargs, original_response, start_time)

                # Determine which processors to use
                processor_list = processors
                if processor_list is None:
                    processor_list = config.get_processors_for_endpoint(endpoint_path)

                if not processor_list:
                    return original_response

                # Handle different response types appropriately
                if response_type in ["json", "dict"]:
                    # Standard JSON/dict responses - full processing
                    enhanced_response = _registry.execute_pipeline(processor_list, original_response, context)
                    return _preserve_response_structure(original_response, enhanced_response)

                elif response_type == "streaming":
                    # Streaming responses - special handling
                    return _handle_streaming_response(original_response, processor_list, context)

                elif response_type in ["binary", "text"]:
                    # Binary and text responses - limited processing
                    return _handle_non_json_response(original_response, processor_list, context, response_type)

                else:
                    # Unknown response types - skip processing
                    logger.debug("Skipping enhancement for response type: %s", response_type)
                    return original_response

            except Exception as e:
                endpoint_name = _get_endpoint_path(func)
                method = request.method if request else "UNKNOWN"

                # Use configuration setting for fail_silently if not explicitly set
                should_fail_silently = fail_silently
                if should_fail_silently is True:  # Use config default if True
                    should_fail_silently = config.get_global_config().fail_silently

                if should_fail_silently:
                    return _error_handler.handle_decorator_error(e, endpoint_name, method, original_response)
                else:
                    # Still log the error even when not failing silently
                    logger.error(
                        "Response enhancement failed for %s: %s",
                        endpoint_name,
                        e,
                        extra={
                            "endpoint": endpoint_name,
                            "method": method,
                            "error_type": type(e).__name__,
                        },
                        exc_info=True,
                    )
                    raise

        return wrapper

    return decorator


def _extract_context(
    func: Callable, args: tuple, kwargs: dict, original_response: Any, start_time: float
) -> ProcessingContext:
    """Extract processing context from function call.

    This function examines the function signature and arguments to extract
    the necessary context information for post-processors.

    Args:
        func: The original function being decorated
        args: Positional arguments passed to the function
        kwargs: Keyword arguments passed to the function
        original_response: The response returned by the original function
        start_time: Timestamp when processing started

    Returns:
        ProcessingContext with extracted information
    """
    # Extract app_model and end_user from function arguments
    # These are typically injected by the @validate_app_token decorator
    app_model = kwargs.get("app_model")
    end_user = kwargs.get("end_user")

    # If not in kwargs, try to find them in args
    # This is a fallback for different decorator ordering
    if app_model is None or end_user is None:
        # Look for App and EndUser instances in args
        from models.model import App, EndUser

        for arg in args:
            if isinstance(arg, App) and app_model is None:
                app_model = arg
            elif isinstance(arg, EndUser) and end_user is None:
                end_user = arg

    # Get endpoint information
    endpoint_name = _get_endpoint_path(func)
    method = request.method if request else "UNKNOWN"

    # Detect response type
    response_type = _detect_response_type(original_response)

    return ProcessingContext(
        request=request,
        app_model=app_model,
        end_user=end_user,
        endpoint_name=endpoint_name,
        method=method,
        original_response=original_response,
        start_time=start_time,
        response_type=response_type,
    )


def _get_endpoint_path(func: Callable) -> str:
    """Get the endpoint path for a function.

    This function attempts to determine the API endpoint path
    from the function and its class context.

    Args:
        func: The function to get the endpoint path for

    Returns:
        The endpoint path string
    """
    # Try to get the path from Flask-RESTx route information
    # Check if this is a bound method (has __self__ attribute)
    try:
        # Use getattr to safely access __self__ attribute
        self_obj = getattr(func, "__self__", None)
        if self_obj is not None and hasattr(self_obj, "__class__"):
            class_name = self_obj.__class__.__name__

            # Map common class names to endpoint patterns
            endpoint_mapping = {
                "CompletionApi": "/completion-messages",
                "ChatApi": "/chat-messages",
                "CompletionStopApi": "/completion-messages/{task_id}/stop",
                "ChatStopApi": "/chat-messages/{task_id}/stop",
            }

            if class_name in endpoint_mapping:
                return endpoint_mapping[class_name]
    except AttributeError:
        # If we can't access the attributes, just continue to fallback
        pass

    # Fallback to function name
    return getattr(func, "__name__", "unknown")


def _detect_response_type(response: Any) -> str:
    """Detect the type of response for appropriate processing.

    This function analyzes the response to determine its type so that
    processors can decide how to handle it appropriately.

    Args:
        response: The response object to analyze

    Returns:
        String indicating the response type: 'json', 'dict', 'streaming', 'binary', 'text', 'unknown'
    """
    # Import here to avoid circular imports
    from core.app.features.rate_limiting.rate_limit import RateLimitGenerator

    if isinstance(response, dict):
        return "dict"
    elif isinstance(response, (Response, WerkzeugResponse)):
        # Check Flask Response objects by mimetype
        mimetype = getattr(response, "mimetype", "")
        if mimetype == "application/json":
            return "json"
        elif mimetype == "text/event-stream":
            return "streaming"
        elif mimetype.startswith("application/") and mimetype != "application/json":
            return "binary"
        elif mimetype.startswith("text/"):
            return "text"
        else:
            return "unknown"
    elif isinstance(response, (Generator, RateLimitGenerator)):
        # Handle generators (streaming responses) and rate-limited generators
        return "streaming"
    elif isinstance(response, Mapping):
        # Handle other mapping types (dict-like objects)
        return "dict"
    elif isinstance(response, str):
        return "text"
    elif isinstance(response, bytes):
        return "binary"
    elif isinstance(response, (list, tuple)):
        return "list"
    elif response is None:
        return "none"
    else:
        return "unknown"


def _preserve_response_structure(original_response: Any, enhanced_response: Any) -> Any:
    """Preserve the original response structure and HTTP status codes.

    This function ensures that the enhanced response maintains the same
    structure and metadata as the original response.

    Args:
        original_response: The original response from the endpoint
        enhanced_response: The response after processing

    Returns:
        The enhanced response with preserved structure
    """
    # If the original response was a Flask Response object, preserve its structure
    if isinstance(original_response, (Response, WerkzeugResponse)):
        if isinstance(enhanced_response, dict):
            # Convert enhanced dict back to Response with same properties
            return Response(
                response=json.dumps(enhanced_response),
                status=original_response.status_code,
                mimetype=original_response.mimetype,
                headers=dict(original_response.headers),  # Preserve all headers
            )
        elif isinstance(enhanced_response, (Response, WerkzeugResponse)):
            # If enhanced response is already a Response, preserve original metadata
            enhanced_response.status_code = original_response.status_code

            # Preserve all original headers, but allow enhanced response to override
            for header_name, header_value in original_response.headers:
                if header_name not in enhanced_response.headers:
                    enhanced_response.headers[header_name] = header_value

            return enhanced_response
        else:
            # For other types, wrap in Response with original metadata
            return Response(
                response=str(enhanced_response),
                status=original_response.status_code,
                mimetype=original_response.mimetype,
                headers=dict(original_response.headers),
            )

    # For dict responses, validate structure integrity
    if isinstance(original_response, dict):
        if isinstance(enhanced_response, dict):
            # Validate that enhanced response is still a valid dict
            if not _validate_response_integrity(original_response, enhanced_response):
                logger.warning("Enhanced response failed integrity check, returning original")
                return original_response
        else:
            # If original was dict but enhanced is not, this is likely an error
            logger.warning("Enhanced response changed type from dict to non-dict, returning original")
            return original_response

    # For other response types, return the enhanced version directly
    return enhanced_response


def _validate_response_integrity(original_response: dict, enhanced_response: dict) -> bool:
    """Validate that the enhanced response maintains structural integrity.

    This function checks that the enhanced response is still a valid response
    and hasn't been corrupted during processing.

    Args:
        original_response: The original response dictionary
        enhanced_response: The enhanced response dictionary

    Returns:
        True if the enhanced response is valid, False otherwise
    """
    try:
        # Check that enhanced response is still a dictionary
        if not isinstance(enhanced_response, dict):
            logger.warning("Enhanced response is not a dictionary")
            return False

        # Check that enhanced response is JSON serializable
        json.dumps(enhanced_response)

        # Check that all original keys are still present (unless explicitly removed)
        # This is a basic integrity check - processors should preserve original structure
        if len(enhanced_response) < len(original_response):
            # Allow processors to add fields, but warn if fields are removed
            missing_keys = set(original_response.keys()) - set(enhanced_response.keys())
            if missing_keys:
                logger.warning("Enhanced response is missing original keys: %s", missing_keys)
                # Don't fail validation for missing keys - processors might intentionally remove them

        return True

    except (TypeError, ValueError):
        logger.exception("Enhanced response failed integrity validation")
        return False


def _handle_streaming_response(original_response: Any, processor_list: list[str], context: ProcessingContext) -> Any:
    """Handle streaming responses with limited enhancement capabilities.

    For streaming responses, we can only add metadata to headers or perform
    side-effect operations (like logging). We cannot modify the stream content
    without buffering it, which would defeat the purpose of streaming.

    Args:
        original_response: The original streaming response
        processor_list: List of processors to apply
        context: Processing context

    Returns:
        The original response, potentially with enhanced headers
    """
    try:
        # For streaming responses, we can only run processors that don't modify content
        # Create a special context indicating this is a streaming response
        streaming_context = ProcessingContext(
            request=context.request,
            app_model=context.app_model,
            end_user=context.end_user,
            endpoint_name=context.endpoint_name,
            method=context.method,
            original_response=original_response,
            start_time=context.start_time,
            response_type="streaming",  # Add response type to context
        )

        # Execute processors that can handle streaming responses
        # Most processors will skip streaming responses, but some (like logging) might still work
        _registry.execute_pipeline(processor_list, original_response, streaming_context)

        # For Flask Response objects, we might be able to add headers
        if isinstance(original_response, (Response, WerkzeugResponse)):
            # Add timing information to headers if available
            processing_time = time.time() - context.start_time
            original_response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"

            # Add request ID if available
            if hasattr(context, "request_id"):
                original_response.headers["X-Request-ID"] = context.request_id

        return original_response

    except Exception as e:
        logger.warning("Failed to enhance streaming response: %s", e)
        return original_response


def _handle_non_json_response(
    original_response: Any, processor_list: list[str], context: ProcessingContext, response_type: str
) -> Any:
    """Handle non-JSON responses (binary, text) with limited enhancement.

    For non-JSON responses, we can add headers but cannot modify the content
    without changing the response type.

    Args:
        original_response: The original non-JSON response
        processor_list: List of processors to apply
        context: Processing context
        response_type: The detected response type

    Returns:
        The original response, potentially with enhanced headers
    """
    try:
        # Create context indicating the response type
        non_json_context = ProcessingContext(
            request=context.request,
            app_model=context.app_model,
            end_user=context.end_user,
            endpoint_name=context.endpoint_name,
            method=context.method,
            original_response=original_response,
            start_time=context.start_time,
            response_type=response_type,
        )

        # Execute processors - most will skip non-JSON responses
        _registry.execute_pipeline(processor_list, original_response, non_json_context)

        # For Flask Response objects, add metadata to headers
        if isinstance(original_response, (Response, WerkzeugResponse)):
            # Add timing information
            processing_time = time.time() - context.start_time
            original_response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"

            # Add content type confirmation
            original_response.headers["X-Content-Type"] = response_type

            # Add request ID if available
            if hasattr(context, "request_id"):
                original_response.headers["X-Request-ID"] = context.request_id

        return original_response

    except Exception as e:
        logger.warning("Failed to enhance %s response: %s", response_type, e)
        return original_response
