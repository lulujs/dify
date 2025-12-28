"""Error handling utilities for response enhancement."""

import logging
from typing import Any

from .context import ProcessingContext

logger = logging.getLogger(__name__)


class EnhancementErrorHandler:
    """Handles errors during response enhancement processing.

    This class provides comprehensive error handling, logging, and recovery
    mechanisms for the response enhancement framework.
    """

    def __init__(self):
        """Initialize the error handler."""
        self._error_counts: dict[str, int] = {}
        self._disabled_processors: set = set()

    def handle_processor_error(
        self, error: Exception, processor_name: str, context: ProcessingContext, original_response: Any
    ) -> Any:
        """Handle an error that occurred during processor execution.

        This method logs the error with detailed context information,
        updates error metrics, and implements circuit breaker logic
        to disable problematic processors.

        Args:
            error: The exception that occurred
            processor_name: Name of the processor that failed
            context: Processing context containing request information
            original_response: The original response to return as fallback

        Returns:
            The original response as a fallback
        """
        # Increment error count for this processor
        self._error_counts[processor_name] = self._error_counts.get(processor_name, 0) + 1

        # Create detailed error context
        error_context = {
            "processor": processor_name,
            "endpoint": context.endpoint_name,
            "method": context.method,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "user_id": context.end_user.id if context.end_user else None,
            "app_id": context.app_model.id if context.app_model else None,
            "request_id": getattr(context.request, "id", None) if context.request else None,
            "processing_time": context.start_time,
            "error_count": self._error_counts[processor_name],
        }

        # Log the error with full context
        logger.error(
            "Processor '%s' failed during response enhancement: %s",
            processor_name,
            error,
            extra=error_context,
            exc_info=True,
        )

        # Implement circuit breaker logic
        if self._should_disable_processor(processor_name):
            self._disabled_processors.add(processor_name)
            logger.warning(
                "Processor '%s' disabled due to high failure rate",
                processor_name,
                extra={"processor": processor_name, "error_count": self._error_counts[processor_name]},
            )

        # Return original response as fallback
        return original_response

    def handle_decorator_error(self, error: Exception, endpoint_name: str, method: str, original_response: Any) -> Any:
        """Handle an error that occurred in the decorator itself.

        This method handles errors that occur outside of processor execution,
        such as context extraction failures or pipeline setup errors.

        Args:
            error: The exception that occurred
            endpoint_name: Name of the endpoint where error occurred
            method: HTTP method of the request
            original_response: The original response to return as fallback

        Returns:
            The original response as a fallback
        """
        error_context = {
            "endpoint": endpoint_name,
            "method": method,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "component": "decorator",
        }

        logger.error("Response enhancement decorator failed: %s", error, extra=error_context, exc_info=True)

        return original_response

    def is_processor_disabled(self, processor_name: str) -> bool:
        """Check if a processor has been disabled due to errors.

        Args:
            processor_name: Name of the processor to check

        Returns:
            True if the processor is disabled, False otherwise
        """
        return processor_name in self._disabled_processors

    def enable_processor(self, processor_name: str) -> None:
        """Re-enable a previously disabled processor.

        Args:
            processor_name: Name of the processor to enable
        """
        self._disabled_processors.discard(processor_name)
        # Reset error count when manually re-enabling
        self._error_counts[processor_name] = 0
        logger.info("Processor '%s' re-enabled", processor_name)

    def get_error_count(self, processor_name: str) -> int:
        """Get the error count for a specific processor.

        Args:
            processor_name: Name of the processor

        Returns:
            Number of errors recorded for this processor
        """
        return self._error_counts.get(processor_name, 0)

    def reset_error_counts(self) -> None:
        """Reset all error counts and re-enable all processors."""
        self._error_counts.clear()
        self._disabled_processors.clear()
        logger.info("All processor error counts reset and processors re-enabled")

    def _should_disable_processor(self, processor_name: str) -> bool:
        """Determine if a processor should be disabled based on error count.

        Args:
            processor_name: Name of the processor to check

        Returns:
            True if the processor should be disabled, False otherwise
        """
        error_count = self._error_counts.get(processor_name, 0)
        # Disable processor after 5 consecutive errors
        return error_count >= 5

    def get_health_status(self) -> dict[str, Any]:
        """Get health status information for monitoring.

        Returns:
            Dictionary containing health status information
        """
        return {
            "error_counts": dict(self._error_counts),
            "disabled_processors": list(self._disabled_processors),
            "total_errors": sum(self._error_counts.values()),
            "healthy_processors": len(self._error_counts) - len(self._disabled_processors),
        }
