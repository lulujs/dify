"""Tests for error handling functionality."""

from unittest.mock import Mock

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.error_handler import EnhancementErrorHandler


class TestEnhancementErrorHandler:
    """Test the EnhancementErrorHandler class."""

    def test_error_handler_initialization(self):
        """Test that error handler initializes correctly."""
        handler = EnhancementErrorHandler()

        assert handler.get_error_count("any_processor") == 0
        assert not handler.is_processor_disabled("any_processor")

        health_status = handler.get_health_status()
        assert health_status["total_errors"] == 0
        assert health_status["disabled_processors"] == []

    def test_handle_processor_error(self):
        """Test handling processor errors."""
        handler = EnhancementErrorHandler()

        # Create mock context
        context = Mock(spec=ProcessingContext)
        context.endpoint_name = "/test-endpoint"
        context.method = "POST"
        context.end_user = Mock()
        context.end_user.id = "user123"
        context.app_model = Mock()
        context.app_model.id = "app456"
        context.request = Mock()
        context.request.id = "req789"
        context.start_time = 1234567890.0

        original_response = {"data": "test"}
        error = ValueError("Test error")

        result = handler.handle_processor_error(error, "test_processor", context, original_response)

        # Should return original response as fallback
        assert result is original_response

        # Should increment error count
        assert handler.get_error_count("test_processor") == 1

        # Should not disable processor after just one error
        assert not handler.is_processor_disabled("test_processor")

    def test_processor_disabled_after_multiple_errors(self):
        """Test that processor gets disabled after multiple errors."""
        handler = EnhancementErrorHandler()
        context = Mock(spec=ProcessingContext)
        context.endpoint_name = "/test-endpoint"
        context.method = "POST"
        context.end_user = None
        context.app_model = Mock()
        context.app_model.id = "app456"
        context.request = None
        context.start_time = 1234567890.0

        original_response = {"data": "test"}
        error = ValueError("Test error")

        # Generate 5 errors to trigger circuit breaker
        for i in range(5):
            handler.handle_processor_error(error, "failing_processor", context, original_response)

        # Processor should now be disabled
        assert handler.is_processor_disabled("failing_processor")
        assert handler.get_error_count("failing_processor") == 5

        # Health status should reflect the disabled processor
        health_status = handler.get_health_status()
        assert "failing_processor" in health_status["disabled_processors"]
        assert health_status["total_errors"] == 5

    def test_handle_decorator_error(self):
        """Test handling decorator-level errors."""
        handler = EnhancementErrorHandler()

        error = RuntimeError("Decorator error")
        original_response = {"data": "test"}

        result = handler.handle_decorator_error(error, "/test-endpoint", "POST", original_response)

        # Should return original response as fallback
        assert result is original_response

    def test_enable_processor(self):
        """Test manually re-enabling a disabled processor."""
        handler = EnhancementErrorHandler()
        context = Mock(spec=ProcessingContext)
        context.endpoint_name = "/test-endpoint"
        context.method = "POST"
        context.end_user = None
        context.app_model = Mock()
        context.app_model.id = "app456"
        context.request = None
        context.start_time = 1234567890.0

        original_response = {"data": "test"}
        error = ValueError("Test error")

        # Generate enough errors to disable processor
        for i in range(5):
            handler.handle_processor_error(error, "test_processor", context, original_response)

        assert handler.is_processor_disabled("test_processor")

        # Re-enable the processor
        handler.enable_processor("test_processor")

        assert not handler.is_processor_disabled("test_processor")
        assert handler.get_error_count("test_processor") == 0

    def test_reset_error_counts(self):
        """Test resetting all error counts."""
        handler = EnhancementErrorHandler()
        context = Mock(spec=ProcessingContext)
        context.endpoint_name = "/test-endpoint"
        context.method = "POST"
        context.end_user = None
        context.app_model = Mock()
        context.app_model.id = "app456"
        context.request = None
        context.start_time = 1234567890.0

        original_response = {"data": "test"}
        error = ValueError("Test error")

        # Generate errors for multiple processors
        for processor in ["proc1", "proc2", "proc3"]:
            for i in range(3):
                handler.handle_processor_error(error, processor, context, original_response)

        # Verify errors were recorded
        assert handler.get_error_count("proc1") == 3
        assert handler.get_error_count("proc2") == 3
        assert handler.get_error_count("proc3") == 3

        # Reset all error counts
        handler.reset_error_counts()

        # Verify all counts are reset
        assert handler.get_error_count("proc1") == 0
        assert handler.get_error_count("proc2") == 0
        assert handler.get_error_count("proc3") == 0

        # Verify no processors are disabled
        assert not handler.is_processor_disabled("proc1")
        assert not handler.is_processor_disabled("proc2")
        assert not handler.is_processor_disabled("proc3")

    def test_get_health_status(self):
        """Test getting comprehensive health status."""
        handler = EnhancementErrorHandler()
        context = Mock(spec=ProcessingContext)
        context.endpoint_name = "/test-endpoint"
        context.method = "POST"
        context.end_user = None
        context.app_model = Mock()
        context.app_model.id = "app456"
        context.request = None
        context.start_time = 1234567890.0

        original_response = {"data": "test"}
        error = ValueError("Test error")

        # Generate different error counts for different processors
        # proc1: 2 errors (healthy)
        for i in range(2):
            handler.handle_processor_error(error, "proc1", context, original_response)

        # proc2: 5 errors (disabled)
        for i in range(5):
            handler.handle_processor_error(error, "proc2", context, original_response)

        # proc3: 1 error (healthy)
        handler.handle_processor_error(error, "proc3", context, original_response)

        health_status = handler.get_health_status()

        assert health_status["error_counts"]["proc1"] == 2
        assert health_status["error_counts"]["proc2"] == 5
        assert health_status["error_counts"]["proc3"] == 1
        assert health_status["total_errors"] == 8
        assert "proc2" in health_status["disabled_processors"]
        assert len(health_status["disabled_processors"]) == 1
        assert health_status["healthy_processors"] == 2  # proc1 and proc3
