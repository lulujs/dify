"""Tests for response enhancement decorator."""

import json
from unittest.mock import Mock, patch

import pytest
from flask import Flask, Response

from core.response_enhancement.decorator import (
    _detect_response_type,
    _extract_context,
    _get_endpoint_path,
    _preserve_response_structure,
    _validate_response_integrity,
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


class TestResponseTypeDetection:
    """Test response type detection functionality."""

    def test_detect_dict_response(self):
        """Test detection of dictionary responses."""
        response = {"key": "value"}
        assert _detect_response_type(response) == "dict"

    def test_detect_json_response(self):
        """Test detection of JSON Flask responses."""
        response = Response(response=json.dumps({"key": "value"}), mimetype="application/json")
        assert _detect_response_type(response) == "json"

    def test_detect_streaming_response(self):
        """Test detection of streaming responses."""
        response = Response(response="data: test\n\n", mimetype="text/event-stream")
        assert _detect_response_type(response) == "streaming"

        # Test generator response
        def generator():
            yield "test"

        assert _detect_response_type(generator()) == "streaming"

    def test_detect_binary_response(self):
        """Test detection of binary responses."""
        response = Response(response=b"binary data", mimetype="application/octet-stream")
        assert _detect_response_type(response) == "binary"

        # Test bytes response
        assert _detect_response_type(b"binary") == "binary"

    def test_detect_text_response(self):
        """Test detection of text responses."""
        response = Response(response="plain text", mimetype="text/plain")
        assert _detect_response_type(response) == "text"

        # Test string response
        assert _detect_response_type("text") == "text"

    def test_detect_list_response(self):
        """Test detection of list responses."""
        assert _detect_response_type([1, 2, 3]) == "list"
        assert _detect_response_type((1, 2, 3)) == "list"

    def test_detect_none_response(self):
        """Test detection of None response."""
        assert _detect_response_type(None) == "none"

    def test_detect_unknown_response(self):
        """Test detection of unknown response types."""

        class CustomObject:
            pass

        assert _detect_response_type(CustomObject()) == "unknown"


class TestResponseStructurePreservation:
    """Test response structure preservation functionality."""

    def test_preserve_flask_response_structure(self):
        """Test preserving Flask Response structure."""
        original = Response(
            response=json.dumps({"original": "data"}),
            status=200,
            mimetype="application/json",
            headers={"X-Custom": "header"},
        )

        enhanced = {"original": "data", "enhanced": "field"}

        result = _preserve_response_structure(original, enhanced)

        assert isinstance(result, Response)
        assert result.status_code == 200
        assert result.mimetype == "application/json"
        assert "X-Custom" in result.headers
        assert result.headers["X-Custom"] == "header"

        # Check response data
        response_data = json.loads(result.get_data(as_text=True))
        assert response_data["original"] == "data"
        assert response_data["enhanced"] == "field"

    def test_preserve_dict_response_structure(self):
        """Test preserving dictionary response structure."""
        original = {"original": "data"}
        enhanced = {"original": "data", "enhanced": "field"}

        result = _preserve_response_structure(original, enhanced)

        assert result is enhanced
        assert result["original"] == "data"
        assert result["enhanced"] == "field"

    def test_preserve_response_with_integrity_failure(self):
        """Test response preservation when integrity check fails."""
        original = {"original": "data"}
        enhanced = "invalid_response"  # Not a dict

        with patch("core.response_enhancement.decorator._validate_response_integrity") as mock_validate:
            mock_validate.return_value = False

            result = _preserve_response_structure(original, enhanced)

            assert result is original  # Should return original on integrity failure


class TestResponseIntegrityValidation:
    """Test response integrity validation."""

    def test_valid_enhanced_response(self):
        """Test validation of valid enhanced response."""
        original = {"original": "data"}
        enhanced = {"original": "data", "enhanced": "field"}

        assert _validate_response_integrity(original, enhanced) is True

    def test_invalid_response_type(self):
        """Test validation fails for non-dict enhanced response."""
        original = {"original": "data"}
        enhanced = "not_a_dict"

        assert _validate_response_integrity(original, enhanced) is False

    def test_non_serializable_response(self):
        """Test validation fails for non-JSON-serializable response."""
        original = {"original": "data"}

        class NonSerializable:
            pass

        enhanced = {"original": "data", "bad_field": NonSerializable()}

        assert _validate_response_integrity(original, enhanced) is False


class TestContextExtraction:
    """Test context extraction functionality."""

    def test_extract_context_from_kwargs(self, flask_context):
        """Test extracting context from function kwargs."""
        from models.model import App, EndUser

        app_model = Mock(spec=App)
        end_user = Mock(spec=EndUser)

        def mock_func():
            pass

        kwargs = {"app_model": app_model, "end_user": end_user}

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "POST"

            context = _extract_context(mock_func, (), kwargs, {"response": "data"}, 1234567890.0)

        assert context.app_model is app_model
        assert context.end_user is end_user
        assert context.method == "POST"
        assert context.original_response == {"response": "data"}
        assert context.start_time == 1234567890.0

    def test_extract_context_from_args(self, flask_context):
        """Test extracting context from function args when not in kwargs."""
        from models.model import App, EndUser

        app_model = Mock(spec=App)
        end_user = Mock(spec=EndUser)

        def mock_func():
            pass

        args = (Mock(), app_model, end_user)  # First arg is self
        kwargs = {}

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "GET"

            context = _extract_context(mock_func, args, kwargs, {"response": "data"}, 1234567890.0)

        assert context.app_model is app_model
        assert context.end_user is end_user
        assert context.method == "GET"


class TestEndpointPathExtraction:
    """Test endpoint path extraction."""

    def test_get_endpoint_path_from_class_mapping(self):
        """Test getting endpoint path from known class mappings."""

        class CompletionApi:
            def post(self):
                pass

        api_instance = CompletionApi()
        func = api_instance.post

        path = _get_endpoint_path(func)
        assert path == "/completion-messages"

    def test_get_endpoint_path_fallback(self):
        """Test fallback to function name when no mapping found."""

        def unknown_function():
            pass

        path = _get_endpoint_path(unknown_function)
        assert path == "unknown_function"


class TestResponseEnhancerDecorator:
    """Test the main response_enhancer decorator."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_decorator_disabled_globally(self, mock_registry, mock_get_config):
        """Test decorator when enhancement is disabled globally."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = False

        @response_enhancer(processors=["test"])
        def test_endpoint():
            return {"data": "test"}

        result = test_endpoint()

        assert result == {"data": "test"}
        mock_registry.execute_pipeline.assert_not_called()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_decorator_disabled_locally(self, mock_registry, mock_get_config):
        """Test decorator when disabled locally."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True

        @response_enhancer(processors=["test"], enabled=False)
        def test_endpoint():
            return {"data": "test"}

        result = test_endpoint()

        assert result == {"data": "test"}
        mock_registry.execute_pipeline.assert_not_called()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_decorator_handles_non_json_responses(self, mock_registry, mock_get_config, flask_context):
        """Test decorator handles non-JSON responses with limited processing."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "GET"

            @response_enhancer(processors=["test"])
            def test_endpoint():
                return "plain text response"

            result = test_endpoint()

            assert result == "plain text response"
            # Should call execute_pipeline for non-JSON responses (limited processing)
            mock_registry.execute_pipeline.assert_called_once()

            # Verify the context indicates text response type
            call_args = mock_registry.execute_pipeline.call_args[0]
            processors, original_response, context = call_args
            assert context.response_type == "text"

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_decorator_processes_dict_response(self, mock_registry, mock_get_config, flask_context):
        """Test decorator processes dictionary responses."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["test_processor"]

        # Mock registry to return enhanced response
        enhanced_response = {"data": "test", "enhanced": True}
        mock_registry.execute_pipeline.return_value = enhanced_response

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "POST"

            @response_enhancer()
            def test_endpoint():
                return {"data": "test"}

            result = test_endpoint()

            assert result == enhanced_response
            mock_registry.execute_pipeline.assert_called_once()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    @patch("core.response_enhancement.decorator._error_handler")
    def test_decorator_handles_processing_error(
        self, mock_error_handler, mock_registry, mock_get_config, flask_context
    ):
        """Test decorator handles processing errors gracefully."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["test_processor"]
        mock_config.get_global_config.return_value.fail_silently = True

        # Mock registry to raise an error
        mock_registry.execute_pipeline.side_effect = ValueError("Processing error")

        # Mock error handler to return original response
        original_response = {"data": "test"}
        mock_error_handler.handle_decorator_error.return_value = original_response

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "POST"

            @response_enhancer(fail_silently=True)
            def test_endpoint():
                return original_response

            result = test_endpoint()

            assert result == original_response
            mock_error_handler.handle_decorator_error.assert_called_once()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_decorator_raises_error_when_not_failing_silently(self, mock_registry, mock_get_config, flask_context):
        """Test decorator raises errors when fail_silently=False."""
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["test_processor"]

        # Mock registry to raise an error
        mock_registry.execute_pipeline.side_effect = ValueError("Processing error")

        with patch("core.response_enhancement.decorator.request") as mock_request:
            mock_request.method = "POST"

            @response_enhancer(fail_silently=False)
            def test_endpoint():
                return {"data": "test"}

            with pytest.raises(ValueError, match="Processing error"):
                test_endpoint()
