"""Tests for PostProcessorRegistry."""

from unittest.mock import Mock, patch

import pytest

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processor import PostProcessor
from core.response_enhancement.registry import PostProcessorRegistry


class MockProcessor(PostProcessor):
    """Mock processor for testing."""

    def __init__(self, name="mock", can_process_result=True, process_result=None):
        self.name = name
        self.can_process_result = can_process_result
        self.process_result = process_result
        self.process_called = False
        self.can_process_called = False

    def process(self, response, context):
        self.process_called = True
        if self.process_result is not None:
            return self.process_result
        # Default behavior: add a field to dict responses
        if isinstance(response, dict):
            response[f"{self.name}_processed"] = True
        return response

    def can_process(self, response, context):
        self.can_process_called = True
        return self.can_process_result


class TestPostProcessorRegistry:
    """Test the PostProcessorRegistry class."""

    def test_registry_initialization(self):
        """Test that registry initializes with empty processor dictionary."""
        registry = PostProcessorRegistry()
        assert registry.list_processors() == []

    def test_register_processor(self):
        """Test registering a processor."""
        registry = PostProcessorRegistry()
        processor = MockProcessor("test")

        registry.register("test_processor", processor)

        assert "test_processor" in registry.list_processors()
        assert registry.get("test_processor") is processor

    def test_register_processor_validation(self):
        """Test validation when registering processors."""
        registry = PostProcessorRegistry()

        # Test empty name
        with pytest.raises(ValueError, match="Processor name cannot be empty"):
            registry.register("", MockProcessor())

        with pytest.raises(ValueError, match="Processor name cannot be empty"):
            registry.register("   ", MockProcessor())

        # Test None processor
        with pytest.raises(ValueError, match="Processor cannot be None"):
            registry.register("test", None)

        # Test invalid processor type
        with pytest.raises(TypeError, match="Processor must implement PostProcessor interface"):
            registry.register("test", "not_a_processor")

    def test_get_nonexistent_processor(self):
        """Test getting a processor that doesn't exist."""
        registry = PostProcessorRegistry()
        assert registry.get("nonexistent") is None

    def test_execute_pipeline_empty(self):
        """Test executing an empty pipeline."""
        registry = PostProcessorRegistry()
        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        result = registry.execute_pipeline([], response, context)
        assert result is response

    def test_execute_pipeline_single_processor(self):
        """Test executing a pipeline with a single processor."""
        registry = PostProcessorRegistry()
        processor = MockProcessor("test")
        registry.register("test_processor", processor)

        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        result = registry.execute_pipeline(["test_processor"], response, context)

        assert processor.can_process_called
        assert processor.process_called
        assert result["data"] == "test"
        assert result["test_processed"] is True

    def test_execute_pipeline_multiple_processors(self):
        """Test executing a pipeline with multiple processors."""
        registry = PostProcessorRegistry()

        processor1 = MockProcessor("first")
        processor2 = MockProcessor("second")

        registry.register("first_processor", processor1)
        registry.register("second_processor", processor2)

        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        result = registry.execute_pipeline(["first_processor", "second_processor"], response, context)

        assert processor1.can_process_called
        assert processor1.process_called
        assert processor2.can_process_called
        assert processor2.process_called

        assert result["data"] == "test"
        assert result["first_processed"] is True
        assert result["second_processed"] is True

    def test_execute_pipeline_processor_cannot_process(self):
        """Test pipeline execution when processor cannot process response."""
        registry = PostProcessorRegistry()
        processor = MockProcessor("test", can_process_result=False)
        registry.register("test_processor", processor)

        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        result = registry.execute_pipeline(["test_processor"], response, context)

        assert processor.can_process_called
        assert not processor.process_called
        assert result is response  # Unchanged

    def test_execute_pipeline_nonexistent_processor(self):
        """Test pipeline execution with nonexistent processor."""
        registry = PostProcessorRegistry()
        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        with patch("core.response_enhancement.registry.logger") as mock_logger:
            result = registry.execute_pipeline(["nonexistent"], response, context)

            mock_logger.warning.assert_called_once()
            assert "not found in registry" in mock_logger.warning.call_args[0][0]

        assert result is response  # Unchanged

    @patch("core.response_enhancement.decorator.get_error_handler")
    def test_execute_pipeline_processor_error(self, mock_get_error_handler):
        """Test pipeline execution when processor raises an error."""
        registry = PostProcessorRegistry()

        # Create a processor that raises an error
        class ErrorProcessor(PostProcessor):
            def process(self, response, context):
                raise ValueError("Test error")

            def can_process(self, response, context):
                return True

        processor = ErrorProcessor()
        registry.register("error_processor", processor)

        # Mock error handler
        mock_error_handler = Mock()
        mock_error_handler.is_processor_disabled.return_value = False
        mock_error_handler.handle_processor_error.return_value = {"data": "test"}
        mock_get_error_handler.return_value = mock_error_handler

        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        result = registry.execute_pipeline(["error_processor"], response, context)

        # Verify error handler was called
        mock_error_handler.handle_processor_error.assert_called_once()
        assert result["data"] == "test"

    @patch("core.response_enhancement.decorator.get_error_handler")
    def test_execute_pipeline_disabled_processor(self, mock_get_error_handler):
        """Test pipeline execution with disabled processor."""
        registry = PostProcessorRegistry()
        processor = MockProcessor("test")
        registry.register("test_processor", processor)

        # Mock error handler to return processor as disabled
        mock_error_handler = Mock()
        mock_error_handler.is_processor_disabled.return_value = True
        mock_get_error_handler.return_value = mock_error_handler

        context = Mock(spec=ProcessingContext)
        response = {"data": "test"}

        with patch("core.response_enhancement.registry.logger") as mock_logger:
            result = registry.execute_pipeline(["test_processor"], response, context)

            mock_logger.debug.assert_called()
            assert "is disabled" in mock_logger.debug.call_args[0][0]

        assert not processor.can_process_called
        assert not processor.process_called
        assert result is response  # Unchanged

    def test_unregister_processor(self):
        """Test unregistering a processor."""
        registry = PostProcessorRegistry()
        processor = MockProcessor("test")
        registry.register("test_processor", processor)

        assert "test_processor" in registry.list_processors()

        result = registry.unregister("test_processor")
        assert result is True
        assert "test_processor" not in registry.list_processors()

        # Test unregistering nonexistent processor
        result = registry.unregister("nonexistent")
        assert result is False

    def test_clear_registry(self):
        """Test clearing all processors from registry."""
        registry = PostProcessorRegistry()

        registry.register("processor1", MockProcessor("test1"))
        registry.register("processor2", MockProcessor("test2"))

        assert len(registry.list_processors()) == 2

        registry.clear()
        assert len(registry.list_processors()) == 0
