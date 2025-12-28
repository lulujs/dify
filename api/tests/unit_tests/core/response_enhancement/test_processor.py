"""Tests for PostProcessor interface and ProcessingContext."""

from unittest.mock import Mock

import pytest

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processor import PostProcessor


class TestPostProcessor:
    """Test the PostProcessor abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that PostProcessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            PostProcessor()

    def test_concrete_implementation_works(self):
        """Test that concrete implementations of PostProcessor work correctly."""

        class TestProcessor(PostProcessor):
            def process(self, response, context):
                if isinstance(response, dict):
                    response["test_field"] = "test_value"
                return response

            def can_process(self, response, context):
                return isinstance(response, dict)

        processor = TestProcessor()
        assert isinstance(processor, PostProcessor)

        # Test can_process method
        assert processor.can_process({"key": "value"}, Mock())
        assert not processor.can_process("string", Mock())

        # Test process method
        response = {"original": "data"}
        context = Mock()
        result = processor.process(response, context)

        assert result["original"] == "data"
        assert result["test_field"] == "test_value"


class TestProcessingContext:
    """Test the ProcessingContext dataclass."""

    def test_processing_context_creation(self):
        """Test that ProcessingContext can be created with all fields."""
        from flask import Request

        from models.model import App, EndUser

        # Create mock objects
        request = Mock(spec=Request)
        app_model = Mock(spec=App)
        end_user = Mock(spec=EndUser)
        original_response = {"data": "test"}
        start_time = 1234567890.0

        context = ProcessingContext(
            request=request,
            app_model=app_model,
            end_user=end_user,
            endpoint_name="/test-endpoint",
            method="POST",
            original_response=original_response,
            start_time=start_time,
        )

        assert context.request is request
        assert context.app_model is app_model
        assert context.end_user is end_user
        assert context.endpoint_name == "/test-endpoint"
        assert context.method == "POST"
        assert context.original_response is original_response
        assert context.start_time == start_time

    def test_processing_context_with_optional_end_user(self):
        """Test that ProcessingContext works with None end_user."""
        from flask import Request

        from models.model import App

        request = Mock(spec=Request)
        app_model = Mock(spec=App)

        context = ProcessingContext(
            request=request,
            app_model=app_model,
            end_user=None,
            endpoint_name="/test-endpoint",
            method="GET",
            original_response={"data": "test"},
            start_time=1234567890.0,
        )

        assert context.end_user is None
        assert context.app_model is app_model
