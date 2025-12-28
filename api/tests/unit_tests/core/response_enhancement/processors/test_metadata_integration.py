"""Integration tests for MetadataProcessor with registry."""

import time
from unittest.mock import Mock

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processor import PostProcessor
from core.response_enhancement.processors.metadata import MetadataProcessor
from core.response_enhancement.registry import PostProcessorRegistry


class TestMetadataProcessorIntegration:
    """Integration tests for MetadataProcessor with PostProcessorRegistry."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = PostProcessorRegistry()
        self.processor = MetadataProcessor(api_version="2.0")
        self.registry.register("metadata", self.processor)

        # Create mock context
        self.mock_request = Mock()
        self.mock_request.headers = {"X-Request-ID": "test-request-123"}
        self.mock_app_model = Mock()
        self.mock_end_user = Mock()

        self.context = ProcessingContext(
            request=self.mock_request,
            app_model=self.mock_app_model,
            end_user=self.mock_end_user,
            endpoint_name="test_endpoint",
            method="POST",
            original_response={},
            start_time=time.time(),
        )

    def test_registry_executes_metadata_processor(self):
        """Test that registry can execute metadata processor in pipeline."""
        response = {"data": "test", "status": "success"}

        result = self.registry.execute_pipeline(["metadata"], response, self.context)

        # Check that metadata fields were added
        assert "timestamp" in result
        assert "request_id" in result
        assert "api_version" in result

        # Check values
        assert result["request_id"] == "test-request-123"  # From headers
        assert result["api_version"] == "2.0"  # From processor config

        # Original data should be preserved
        assert result["data"] == "test"
        assert result["status"] == "success"

    def test_registry_skips_non_dict_responses(self):
        """Test that registry handles non-dict responses correctly."""
        string_response = "plain text response"

        result = self.registry.execute_pipeline(["metadata"], string_response, self.context)

        # Should return original response unchanged
        assert result == string_response

    def test_registry_handles_multiple_processors(self):
        """Test that registry can handle multiple processors including metadata."""

        # Register a simple test processor
        class TestProcessor(PostProcessor):
            def can_process(self, response, context):
                return isinstance(response, dict)

            def process(self, response, context):
                if self.can_process(response, context):
                    response = response.copy()
                    response["test_field"] = "added_by_test_processor"
                return response

        self.registry.register("test", TestProcessor())

        response = {"data": "test"}

        result = self.registry.execute_pipeline(["test", "metadata"], response, self.context)

        # Both processors should have run
        assert result["test_field"] == "added_by_test_processor"
        assert "timestamp" in result
        assert "request_id" in result
        assert "api_version" in result
        assert result["data"] == "test"

    def test_registry_handles_processor_not_found(self):
        """Test that registry handles missing processors gracefully."""
        response = {"data": "test"}

        result = self.registry.execute_pipeline(["nonexistent", "metadata"], response, self.context)

        # Should still process with metadata processor
        assert "timestamp" in result
        assert "request_id" in result
        assert "api_version" in result
        assert result["data"] == "test"
