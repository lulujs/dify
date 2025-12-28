"""Tests for different response type handling in response enhancement."""

import json
from unittest.mock import Mock, patch

import pytest
from flask import Flask, Response

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.decorator import (
    _detect_response_type,
    _handle_non_json_response,
    _handle_streaming_response,
    response_enhancer,
)


@pytest.fixture
def flask_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def flask_context(flask_app):
    """Create a Flask request context for testing."""
    with flask_app.test_request_context():
        yield


@pytest.fixture
def mock_context():
    """Create a mock processing context."""
    return ProcessingContext(
        request=Mock(),
        app_model=Mock(),
        end_user=Mock(),
        endpoint_name="/test",
        method="POST",
        original_response={"test": "data"},
        start_time=1234567890.0,
        response_type="dict",
    )


class TestResponseTypeDetection:
    """Test enhanced response type detection."""

    def test_detect_rate_limit_generator(self):
        """Test detection of RateLimitGenerator responses."""
        # Test with actual RateLimitGenerator import
        from core.app.features.rate_limiting.rate_limit import RateLimitGenerator

        # Create a mock generator and rate limit
        mock_rate_limit = Mock()
        mock_generator = Mock()

        # Create RateLimitGenerator instance
        rate_limit_gen = RateLimitGenerator(mock_rate_limit, mock_generator, "test-request-id")

        assert _detect_response_type(rate_limit_gen) == "streaming"

    def test_detect_compact_generate_response_dict(self):
        """Test detection of dict responses that would go through compact_generate_response."""
        response = {"data": "test", "status": "success"}
        assert _detect_response_type(response) == "dict"

    def test_detect_compact_generate_response_generator(self):
        """Test detection of generator responses that would go through compact_generate_response."""

        def test_generator():
            yield "data: test\n\n"
            yield "data: more\n\n"

        assert _detect_response_type(test_generator()) == "streaming"

    def test_detect_flask_response_from_compact_generate(self):
        """Test detection of Flask Response objects created by compact_generate_response."""
        # Simulate what compact_generate_response creates for dict
        json_response = Response(response=json.dumps({"data": "test"}), status=200, mimetype="application/json")
        assert _detect_response_type(json_response) == "json"

        # Simulate what compact_generate_response creates for generator
        streaming_response = Response(response="data: test\n\n", status=200, mimetype="text/event-stream")
        assert _detect_response_type(streaming_response) == "streaming"


class TestStreamingResponseHandling:
    """Test streaming response handling."""

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_streaming_response_with_flask_response(self, mock_registry, mock_context, flask_context):
        """Test handling streaming Flask Response objects."""
        streaming_response = Response(
            response="data: test\n\n", status=200, mimetype="text/event-stream", headers={"X-Original": "header"}
        )

        result = _handle_streaming_response(streaming_response, ["metadata"], mock_context)

        # Should return the original response
        assert result is streaming_response

        # Should have added timing header
        assert "X-Processing-Time" in result.headers

        # Should preserve original headers
        assert result.headers["X-Original"] == "header"

        # Should have called registry with streaming context
        mock_registry.execute_pipeline.assert_called_once()
        call_args = mock_registry.execute_pipeline.call_args[0]
        processors, original_response, context = call_args

        assert processors == ["metadata"]
        assert original_response is streaming_response
        assert context.response_type == "streaming"

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_streaming_response_with_generator(self, mock_registry, mock_context, flask_context):
        """Test handling raw generator responses."""

        def test_generator():
            yield "data: test\n\n"
            yield "data: more\n\n"

        generator = test_generator()
        result = _handle_streaming_response(generator, ["metadata"], mock_context)

        # Should return the original generator
        assert result is generator

        # Should have called registry
        mock_registry.execute_pipeline.assert_called_once()

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_streaming_response_error_recovery(self, mock_registry, mock_context, flask_context):
        """Test error recovery in streaming response handling."""
        mock_registry.execute_pipeline.side_effect = ValueError("Processing error")

        streaming_response = Response(response="data: test\n\n", status=200, mimetype="text/event-stream")

        result = _handle_streaming_response(streaming_response, ["metadata"], mock_context)

        # Should return original response despite error
        assert result is streaming_response


class TestNonJsonResponseHandling:
    """Test non-JSON response handling."""

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_binary_response(self, mock_registry, mock_context, flask_context):
        """Test handling binary responses."""
        binary_response = Response(response=b"binary data", status=200, mimetype="application/octet-stream")

        result = _handle_non_json_response(binary_response, ["metadata"], mock_context, "binary")

        # Should return the original response
        assert result is binary_response

        # Should have added headers
        assert "X-Processing-Time" in result.headers
        assert result.headers["X-Content-Type"] == "binary"

        # Should have called registry with correct context
        mock_registry.execute_pipeline.assert_called_once()
        call_args = mock_registry.execute_pipeline.call_args[0]
        processors, original_response, context = call_args

        assert context.response_type == "binary"

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_text_response(self, mock_registry, mock_context, flask_context):
        """Test handling text responses."""
        text_response = Response(response="plain text content", status=200, mimetype="text/plain")

        result = _handle_non_json_response(text_response, ["metadata"], mock_context, "text")

        # Should return the original response
        assert result is text_response

        # Should have added headers
        assert "X-Processing-Time" in result.headers
        assert result.headers["X-Content-Type"] == "text"

    @patch("core.response_enhancement.decorator._registry")
    def test_handle_non_json_response_error_recovery(self, mock_registry, mock_context, flask_context):
        """Test error recovery in non-JSON response handling."""
        mock_registry.execute_pipeline.side_effect = ValueError("Processing error")

        text_response = Response(response="plain text", status=200, mimetype="text/plain")

        result = _handle_non_json_response(text_response, ["metadata"], mock_context, "text")

        # Should return original response despite error
        assert result is text_response


class TestIntegrationWithCompactGenerateResponse:
    """Test integration with helper.compact_generate_response function."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_enhancement_of_dict_before_compact_generate_response(self, mock_registry, mock_get_config, flask_context):
        """Test enhancing dict responses before they go through compact_generate_response."""
        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        enhanced_response = {"data": "test", "metadata": {"enhanced": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        @response_enhancer(processors=["metadata"])
        def test_endpoint():
            # This simulates what happens before compact_generate_response
            return {"data": "test"}

        result = test_endpoint()

        # Should return enhanced dict (before compact_generate_response converts it)
        assert result == enhanced_response
        assert result["metadata"]["enhanced"] is True

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_enhancement_of_streaming_response_from_compact_generate_response(
        self, mock_registry, mock_get_config, flask_context
    ):
        """Test handling streaming responses created by compact_generate_response."""
        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        @response_enhancer(processors=["metadata"])
        def test_streaming_endpoint():
            # Simulate what compact_generate_response creates for generators
            def generator():
                yield "data: test\n\n"
                yield "data: more\n\n"

            from flask import stream_with_context

            return Response(stream_with_context(generator()), status=200, mimetype="text/event-stream")

        result = test_streaming_endpoint()

        # Should return the streaming response with potential header enhancements
        assert isinstance(result, Response)
        assert result.mimetype == "text/event-stream"

        # Should have called registry for streaming handling
        mock_registry.execute_pipeline.assert_called_once()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_enhancement_skipped_for_unknown_response_types(self, mock_registry, mock_get_config, flask_context):
        """Test that enhancement is skipped for unknown response types."""
        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        class CustomResponseType:
            def __init__(self, data):
                self.data = data

        @response_enhancer(processors=["metadata"])
        def test_unknown_endpoint():
            return CustomResponseType("custom data")

        result = test_unknown_endpoint()

        # Should return original response unchanged
        assert isinstance(result, CustomResponseType)
        assert result.data == "custom data"

        # Should not have called registry
        mock_registry.execute_pipeline.assert_not_called()


class TestResponseTypeContextPassing:
    """Test that response type is correctly passed in context."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_response_type_in_context_for_dict(self, mock_registry, mock_get_config, flask_context):
        """Test that response_type is correctly set in context for dict responses."""
        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        mock_registry.execute_pipeline.return_value = {"data": "test", "enhanced": True}

        @response_enhancer(processors=["metadata"])
        def test_endpoint():
            return {"data": "test"}

        test_endpoint()

        # Verify context has correct response_type
        mock_registry.execute_pipeline.assert_called_once()
        call_args = mock_registry.execute_pipeline.call_args[0]
        processors, original_response, context = call_args

        assert context.response_type == "dict"

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_response_type_in_context_for_streaming(self, mock_registry, mock_get_config, flask_context):
        """Test that response_type is correctly set in context for streaming responses."""
        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        @response_enhancer(processors=["metadata"])
        def test_streaming_endpoint():
            return Response(response="data: test\n\n", status=200, mimetype="text/event-stream")

        test_streaming_endpoint()

        # Verify context has correct response_type
        mock_registry.execute_pipeline.assert_called_once()
        call_args = mock_registry.execute_pipeline.call_args[0]
        processors, original_response, context = call_args

        assert context.response_type == "streaming"
