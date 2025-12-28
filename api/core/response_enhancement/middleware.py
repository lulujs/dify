"""
Global response enhancement middleware.

This middleware automatically applies response enhancement based on configuration
without requiring decorators on individual endpoints.
"""

import json
import logging
import time
from typing import Any, Optional

from flask import Flask, Response, g, request
from werkzeug.wrappers import Response as WerkzeugResponse

from .config import get_config
from .context import ProcessingContext
from .registry import get_registry

logger = logging.getLogger(__name__)


class ResponseEnhancementMiddleware:
    """Global response enhancement middleware.

    This middleware automatically applies response enhancement to API endpoints
    based on configuration files, eliminating the need for manual decorators.
    """

    def __init__(self, app: Optional[Flask] = None):
        """Initialize the middleware.

        Args:
            app: Flask application instance. If provided, middleware will be initialized.
        """
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize middleware with Flask application.

        Args:
            app: Flask application instance to attach middleware to.
        """
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        logger.info("Response enhancement middleware initialized")

    def before_request(self) -> None:
        """Process request before endpoint execution.

        Determines if the current endpoint needs response enhancement
        and stores configuration in Flask's g object.
        """
        try:
            config = get_config()
            endpoint_path = request.path

            # Record start time for timing information
            g.response_enhancement_start_time = time.time()

            # Check if enhancement is enabled for this endpoint
            if config.is_enabled(endpoint_path):
                processors = config.get_processors_for_endpoint(endpoint_path)

                g.response_enhancement = {
                    "enabled": True,
                    "processors": processors,
                    "endpoint_path": endpoint_path,
                    "method": request.method,
                }

                # Add debug logging for workflow endpoints
                if "/workflows/run" in endpoint_path:
                    logger.info(
                        "MIDDLEWARE DEBUG: Response enhancement enabled for %s %s with processors: %s",
                        request.method,
                        endpoint_path,
                        processors,
                    )
                else:
                    logger.debug(
                        "Response enhancement enabled for %s %s with processors: %s",
                        request.method,
                        endpoint_path,
                        processors,
                    )
            else:
                g.response_enhancement = {"enabled": False}
                if "/workflows/run" in endpoint_path:
                    logger.info(
                        "MIDDLEWARE DEBUG: Response enhancement disabled for %s %s", request.method, endpoint_path
                    )
                else:
                    logger.debug("Response enhancement disabled for %s %s", request.method, endpoint_path)

        except Exception:
            logger.exception("Error in response enhancement before_request")
            # Disable enhancement on error to prevent breaking the request
            g.response_enhancement = {"enabled": False}

    def after_request(self, response: Response) -> Response:
        """Process response after endpoint execution.

        Applies response enhancement if enabled for the current endpoint.

        Args:
            response: The Flask response object from the endpoint.

        Returns:
            Enhanced response or original response if enhancement fails/disabled.
        """
        # Check if enhancement is enabled for this request
        if not hasattr(g, "response_enhancement") or not g.response_enhancement.get("enabled"):
            return response

        try:
            processors = g.response_enhancement.get("processors", [])
            endpoint_path = g.response_enhancement.get("endpoint_path", "unknown")

            # Add debug logging for workflow endpoints
            if "/workflows/run" in endpoint_path:
                logger.info(
                    "MIDDLEWARE DEBUG: Processing response for %s with processors: %s", endpoint_path, processors
                )

            if not processors:
                logger.debug("No processors configured, skipping enhancement")
                return response

            # Get the registry and check if processors are available
            registry = get_registry()

            # Create processing context
            context = self._create_processing_context(response)

            # Detect response type to determine if we can process it
            response_type = self._detect_response_type(response)

            if "/workflows/run" in endpoint_path:
                logger.info("MIDDLEWARE DEBUG: Response type detected: %s for %s", response_type, endpoint_path)

            if response_type in ["json", "dict"]:
                # Handle JSON/dict responses - full processing
                enhanced_response = self._process_json_response(response, processors, context, registry)
                if "/workflows/run" in endpoint_path:
                    logger.info("MIDDLEWARE DEBUG: JSON response processed successfully for %s", endpoint_path)
                else:
                    logger.debug("JSON response processed successfully for %s", endpoint_path)
                return enhanced_response

            elif response_type == "streaming":
                # Handle streaming responses - limited processing
                return self._process_streaming_response(response, processors, context, registry)

            elif response_type in ["binary", "text"]:
                # Handle binary/text responses - header-only processing
                return self._process_non_json_response(response, processors, context, registry)

            else:
                logger.debug("Unknown response type %s, skipping enhancement", response_type)
                return response

        except Exception as e:
            # Handle errors based on configuration
            config = get_config()
            endpoint_path = g.response_enhancement.get("endpoint_path", "unknown")

            if config.get_global_config().fail_silently:
                logger.error(
                    "Response enhancement failed for %s: %s",
                    endpoint_path,
                    e,
                    extra={
                        "endpoint": endpoint_path,
                        "method": g.response_enhancement.get("method", "unknown"),
                        "error_type": type(e).__name__,
                    },
                    exc_info=True,
                )
                return response
            else:
                logger.error("Response enhancement failed for %s: %s", endpoint_path, e, exc_info=True)
                raise

    def _create_processing_context(self, response: Response) -> ProcessingContext:
        """Create processing context for the current request.

        Args:
            response: The Flask response object.

        Returns:
            ProcessingContext with request information.
        """
        # Extract app_model and end_user from Flask's g object
        # These are typically set by the @validate_app_token decorator
        app_model = getattr(g, "app_model", None)
        end_user = getattr(g, "end_user", None)

        # Also try to get them from request context if not in g
        if not app_model:
            app_model = getattr(request, "app_model", None)
        if not end_user:
            end_user = getattr(request, "end_user", None)

        return ProcessingContext(
            request=request,
            app_model=app_model,
            end_user=end_user,
            endpoint_name=g.response_enhancement.get("endpoint_path", "unknown"),
            method=g.response_enhancement.get("method", "unknown"),
            original_response=response,
            start_time=getattr(g, "response_enhancement_start_time", time.time()),
            response_type=self._detect_response_type(response),
        )

    def _detect_response_type(self, response: Any) -> str:
        """Detect the type of response for appropriate processing.

        Args:
            response: The response object to analyze.

        Returns:
            String indicating response type: 'json', 'streaming', 'binary', 'text', 'unknown'
        """
        if isinstance(response, (Response, WerkzeugResponse)):
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
        elif isinstance(response, dict):
            return "dict"
        else:
            return "unknown"

    def _process_json_response(
        self, response: Response, processors: list[str], context: ProcessingContext, registry
    ) -> Response:
        """Process JSON responses with full enhancement.

        Args:
            response: Original Flask response.
            processors: List of processor names to apply.
            context: Processing context.
            registry: Processor registry.

        Returns:
            Enhanced Flask response.
        """
        try:
            # Parse the JSON content from the response
            original_data = json.loads(response.get_data(as_text=True))

            # Execute processor pipeline on the data
            enhanced_data = registry.execute_pipeline(processors, original_data, context)

            # Create new response with enhanced data
            return Response(
                response=json.dumps(enhanced_data),
                status=response.status_code,
                mimetype="application/json",
                headers=dict(response.headers),
            )

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning("Failed to parse JSON response for enhancement: %s", e)
            return response

    def _process_streaming_response(
        self, response: Response, processors: list[str], context: ProcessingContext, registry
    ) -> Response:
        """Process streaming responses with limited enhancement.

        For streaming responses, we can only add headers or perform side-effects.

        Args:
            response: Original Flask response.
            processors: List of processor names to apply.
            context: Processing context.
            registry: Processor registry.

        Returns:
            Response with enhanced headers.
        """
        try:
            # Execute processors that can handle streaming responses
            # Most processors will skip streaming responses
            registry.execute_pipeline(processors, response, context)

            # Add timing information to headers
            processing_time = time.time() - context.start_time
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"

            return response

        except Exception as e:
            logger.warning("Failed to enhance streaming response: %s", e)
            return response

    def _process_non_json_response(
        self, response: Response, processors: list[str], context: ProcessingContext, registry
    ) -> Response:
        """Process non-JSON responses with header-only enhancement.

        Args:
            response: Original Flask response.
            processors: List of processor names to apply.
            context: Processing context.
            registry: Processor registry.

        Returns:
            Response with enhanced headers.
        """
        try:
            # Execute processors - most will skip non-JSON responses
            registry.execute_pipeline(processors, response, context)

            # Add timing information to headers
            processing_time = time.time() - context.start_time
            response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"

            # Add content type confirmation
            response.headers["X-Content-Type"] = context.response_type

            return response

        except Exception as e:
            logger.warning("Failed to enhance non-JSON response: %s", e)
            return response


# Global middleware instance
_middleware_instance: Optional[ResponseEnhancementMiddleware] = None


def get_middleware() -> ResponseEnhancementMiddleware:
    """Get the global middleware instance.

    Returns:
        Global middleware instance.
    """
    global _middleware_instance

    if _middleware_instance is None:
        _middleware_instance = ResponseEnhancementMiddleware()

    return _middleware_instance


def init_middleware(app: Flask) -> None:
    """Initialize response enhancement middleware with Flask app.

    Args:
        app: Flask application instance.
    """
    middleware = get_middleware()
    middleware.init_app(app)
