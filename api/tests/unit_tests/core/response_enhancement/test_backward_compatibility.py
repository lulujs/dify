"""Tests for backward compatibility of response enhancement framework.

This module tests that existing API contracts are maintained and all original
fields and behaviors are preserved when response enhancement is applied.
"""

import json
from unittest.mock import Mock, patch

import pytest
from flask import Response

from core.response_enhancement import response_enhancer
from models.model import App, AppMode, EndUser


class TestBackwardCompatibility:
    """Test that response enhancement maintains backward compatibility."""

    def test_original_response_fields_preserved(self):
        """Test that all original response fields are preserved."""

        # Create a controller method that returns a typical API response
        def api_controller(app_model: App, end_user: EndUser):
            return {
                "message": "Hello world",
                "conversation_id": "conv-123",
                "created_at": 1234567890,
                "metadata": {"tokens": 150, "model": "gpt-3.5-turbo"},
            }

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_app.mode = AppMode.COMPLETION
        mock_user = Mock(spec=EndUser)

        # Mock configuration and registry
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                # Mock processor that adds a field but preserves all original fields
                def mock_processor(processor_list, response, context):
                    enhanced = response.copy()
                    enhanced["_enhanced"] = True
                    return enhanced

                mock_registry.execute_pipeline.side_effect = mock_processor

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

        # Verify all original fields are preserved
        assert result["message"] == "Hello world"
        assert result["conversation_id"] == "conv-123"
        assert result["created_at"] == 1234567890
        assert result["metadata"]["tokens"] == 150
        assert result["metadata"]["model"] == "gpt-3.5-turbo"

        # Verify enhancement was applied
        assert result["_enhanced"] is True

    def test_response_structure_unchanged(self):
        """Test that response structure remains unchanged."""
        # Test various response structures
        test_responses = [
            # Simple dict
            {"result": "success"},
            # Nested dict
            {"data": {"items": [1, 2, 3], "total": 3}, "status": "ok"},
            # List response
            [{"id": 1, "name": "item1"}, {"id": 2, "name": "item2"}],
            # String response
            "Simple string response",
            # None response
            None,
        ]

        for original_response in test_responses:

            def api_controller(app_model: App, end_user: EndUser, response=original_response):
                return response

            # Apply enhancement with no processors (should return unchanged)
            enhanced_controller = response_enhancer(processors=[])(api_controller)

            # Mock objects
            mock_app = Mock(spec=App)
            mock_user = Mock(spec=EndUser)

            # Mock configuration
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = True
                config_instance.get_processors_for_endpoint.return_value = []
                mock_config.return_value = config_instance

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

            # Verify response is unchanged
            assert result == original_response, f"Response structure changed for {type(original_response)}"

    def test_http_status_codes_preserved(self):
        """Test that HTTP status codes are preserved."""
        # Test different Flask Response objects with various status codes
        test_cases = [
            (200, "OK"),
            (201, "Created"),
            (400, "Bad Request"),
            (404, "Not Found"),
            (500, "Internal Server Error"),
        ]

        for status_code, status_text in test_cases:

            def api_controller(app_model: App, end_user: EndUser, code=status_code, text=status_text):
                return Response(response=json.dumps({"message": text}), status=code, mimetype="application/json")

            # Apply enhancement
            enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

            # Mock objects
            mock_app = Mock(spec=App)
            mock_user = Mock(spec=EndUser)

            # Mock configuration and registry
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = True
                config_instance.get_processors_for_endpoint.return_value = ["metadata"]
                config_instance.get_global_config.return_value = Mock(fail_silently=True)
                mock_config.return_value = config_instance

                with patch("core.response_enhancement.decorator._registry") as mock_registry:
                    # Mock processor that returns enhanced dict
                    mock_registry.execute_pipeline.return_value = {"message": status_text, "_enhanced": True}

                    # Call enhanced controller
                    result = enhanced_controller(mock_app, mock_user)

            # Verify status code is preserved
            assert isinstance(result, Response)
            assert result.status_code == status_code

            # Verify content is enhanced but status is preserved
            response_data = json.loads(result.get_data(as_text=True))
            assert response_data["message"] == status_text
            assert response_data["_enhanced"] is True

    def test_response_headers_preserved(self):
        """Test that response headers are preserved."""

        def api_controller(app_model: App, end_user: EndUser):
            response = Response(response=json.dumps({"data": "test"}), status=200, mimetype="application/json")
            response.headers["X-Custom-Header"] = "custom-value"
            response.headers["X-Rate-Limit"] = "100"
            return response

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock configuration and registry
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                mock_registry.execute_pipeline.return_value = {"data": "test", "_enhanced": True}

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

        # Verify headers are preserved
        assert result.headers["X-Custom-Header"] == "custom-value"
        assert result.headers["X-Rate-Limit"] == "100"

        # Verify content is enhanced
        response_data = json.loads(result.get_data(as_text=True))
        assert response_data["_enhanced"] is True

    def test_api_contract_compatibility(self):
        """Test that API contracts remain compatible."""

        # Simulate a typical Service API response structure
        def completion_api_controller(app_model: App, end_user: EndUser):
            return {
                "message_id": "msg-123",
                "conversation_id": "conv-456",
                "mode": "completion",
                "answer": "This is the AI response",
                "metadata": {
                    "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
                    "retriever_resources": [],
                },
                "created_at": 1234567890,
            }

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(completion_api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_app.mode = AppMode.COMPLETION
        mock_user = Mock(spec=EndUser)

        # Mock configuration and registry
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                # Mock processor that adds enhancement metadata
                def mock_processor(processor_list, response, context):
                    enhanced = response.copy()
                    enhanced["_meta"] = {"processing_time": 0.123, "request_id": "req-789"}
                    return enhanced

                mock_registry.execute_pipeline.side_effect = mock_processor

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

        # Verify all original API contract fields are present
        assert result["message_id"] == "msg-123"
        assert result["conversation_id"] == "conv-456"
        assert result["mode"] == "completion"
        assert result["answer"] == "This is the AI response"
        assert result["created_at"] == 1234567890

        # Verify nested metadata structure is preserved
        assert result["metadata"]["usage"]["prompt_tokens"] == 10
        assert result["metadata"]["usage"]["completion_tokens"] == 20
        assert result["metadata"]["usage"]["total_tokens"] == 30
        assert result["metadata"]["retriever_resources"] == []

        # Verify enhancement was added without breaking contract
        assert "_meta" in result
        assert result["_meta"]["processing_time"] == 0.123
        assert result["_meta"]["request_id"] == "req-789"

    def test_error_response_compatibility(self):
        """Test that error responses remain compatible."""

        # Test that error responses are handled correctly
        def error_controller(app_model: App, end_user: EndUser):
            return {
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "The request is invalid",
                    "details": {"field": "query", "issue": "required"},
                }
            }, 400

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(error_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock configuration
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            # Call enhanced controller
            result = enhanced_controller(mock_app, mock_user)

        # Verify error response structure is preserved (tuple responses are not processed)
        assert isinstance(result, tuple)
        data, status = result
        assert status == 400

        # Verify error fields are preserved exactly as original
        assert data["error"]["code"] == "INVALID_REQUEST"
        assert data["error"]["message"] == "The request is invalid"
        assert data["error"]["details"]["field"] == "query"
        assert data["error"]["details"]["issue"] == "required"

        # Verify no enhancement was added (tuple responses are skipped)
        assert "_timestamp" not in data

    def test_streaming_response_compatibility(self):
        """Test that streaming responses remain compatible."""

        def streaming_generator():
            yield "data: chunk1\n\n"
            yield "data: chunk2\n\n"
            yield "data: [DONE]\n\n"

        def streaming_controller(app_model: App, end_user: EndUser):
            return streaming_generator()

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(streaming_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock configuration
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                # Mock registry that doesn't modify streaming responses
                mock_registry.execute_pipeline.return_value = None

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

        # Verify streaming response is preserved
        assert hasattr(result, "__iter__")

        # Collect all chunks
        chunks = list(result)
        assert chunks == ["data: chunk1\n\n", "data: chunk2\n\n", "data: [DONE]\n\n"]

    def test_disabled_enhancement_full_compatibility(self):
        """Test that disabled enhancement provides full compatibility."""
        # Test various response types with enhancement disabled
        test_responses = [{"data": "test"}, Response("test", status=200), ["item1", "item2"], "plain text", None]

        for original_response in test_responses:

            def api_controller(app_model: App, end_user: EndUser, response=original_response):
                return response

            # Apply enhancement but disable it
            enhanced_controller = response_enhancer(processors=["metadata"], enabled=False)(api_controller)

            # Mock objects
            mock_app = Mock(spec=App)
            mock_user = Mock(spec=EndUser)

            # Call enhanced controller (should be identical to original)
            result = enhanced_controller(mock_app, mock_user)

            # Verify response is completely unchanged
            assert result is original_response, f"Disabled enhancement changed response for {type(original_response)}"

    def test_json_serialization_compatibility(self):
        """Test that enhanced responses remain JSON serializable."""

        def api_controller(app_model: App, end_user: EndUser):
            return {"message": "Hello", "data": {"items": [1, 2, 3], "metadata": {"key": "value"}}}

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock configuration and registry
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                # Mock processor that adds serializable data
                def mock_processor(processor_list, response, context):
                    enhanced = response.copy()
                    enhanced["_meta"] = {"timestamp": 1234567890, "version": "1.0", "enhanced": True}
                    return enhanced

                mock_registry.execute_pipeline.side_effect = mock_processor

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

        # Verify result is JSON serializable
        try:
            json_str = json.dumps(result)
            parsed_back = json.loads(json_str)

            # Verify original data is preserved
            assert parsed_back["message"] == "Hello"
            assert parsed_back["data"]["items"] == [1, 2, 3]
            assert parsed_back["data"]["metadata"]["key"] == "value"

            # Verify enhancement is present and serializable
            assert parsed_back["_meta"]["timestamp"] == 1234567890
            assert parsed_back["_meta"]["version"] == "1.0"
            assert parsed_back["_meta"]["enhanced"] is True

        except (TypeError, ValueError) as e:
            pytest.fail(f"Enhanced response is not JSON serializable: {e}")
