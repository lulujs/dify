"""Unit tests for MetadataProcessor."""

import json
import time
import uuid
from unittest.mock import Mock

from flask import Flask, Response

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processors.metadata import MetadataProcessor


class TestMetadataProcessor:
    """Test cases for MetadataProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = MetadataProcessor(api_version="1.0")

        # Create mock context
        self.mock_request = Mock()
        self.mock_request.headers = {}
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

    def test_can_process_dict_response(self):
        """Test that processor can handle dictionary responses."""
        response = {"data": "test"}
        assert self.processor.can_process(response, self.context) is True

    def test_cannot_process_non_dict_response(self):
        """Test that processor skips non-dictionary responses."""
        # Test string response
        assert self.processor.can_process("string response", self.context) is False

        # Test list response
        assert self.processor.can_process([1, 2, 3], self.context) is False

        # Test None response
        assert self.processor.can_process(None, self.context) is False

    def test_can_process_flask_json_response(self):
        """Test that processor can handle Flask JSON responses."""
        with Flask(__name__).app_context():
            response = Response(response=json.dumps({"message": "test"}), status=200, mimetype="application/json")
            assert self.processor.can_process(response, self.context) is True

    def test_cannot_process_flask_non_json_response(self):
        """Test that processor skips Flask non-JSON responses."""
        with Flask(__name__).app_context():
            response = Response(response="plain text", status=200, mimetype="text/plain")
            assert self.processor.can_process(response, self.context) is False

    def test_process_adds_metadata_fields(self):
        """Test that processor adds timestamp, request_id, and api_version."""
        response = {"data": "test"}

        result = self.processor.process(response, self.context)

        # Check that all metadata fields are added
        assert "timestamp" in result
        assert "request_id" in result
        assert "api_version" in result

        # Check values
        assert result["api_version"] == "1.0"
        assert isinstance(result["request_id"], str)
        assert isinstance(result["timestamp"], str)

        # Original data should be preserved
        assert result["data"] == "test"

    def test_process_preserves_existing_fields(self):
        """Test that processor doesn't overwrite existing metadata fields."""
        response = {
            "data": "test",
            "timestamp": "existing_timestamp",
            "request_id": "existing_id",
            "api_version": "existing_version",
        }

        result = self.processor.process(response, self.context)

        # Existing fields should be preserved
        assert result["timestamp"] == "existing_timestamp"
        assert result["request_id"] == "existing_id"
        assert result["api_version"] == "existing_version"
        assert result["data"] == "test"

    def test_process_uses_request_id_from_headers(self):
        """Test that processor uses request ID from headers when available."""
        expected_request_id = "header-request-id-123"
        self.mock_request.headers = {"X-Request-ID": expected_request_id}

        response = {"data": "test"}
        result = self.processor.process(response, self.context)

        assert result["request_id"] == expected_request_id

    def test_process_generates_uuid_when_no_header(self):
        """Test that processor generates UUID when no request ID header."""
        response = {"data": "test"}
        result = self.processor.process(response, self.context)

        # Should be a valid UUID string
        request_id = result["request_id"]
        assert isinstance(request_id, str)
        # Verify it's a valid UUID by trying to parse it
        uuid.UUID(request_id)

    def test_process_skips_non_dict_response(self):
        """Test that processor returns non-dict responses unchanged."""
        string_response = "not a dict"
        result = self.processor.process(string_response, self.context)
        assert result == string_response

    def test_process_does_not_modify_original_response(self):
        """Test that processor doesn't modify the original response object."""
        original_response = {"data": "test"}
        original_copy = original_response.copy()

        result = self.processor.process(original_response, self.context)

        # Original response should be unchanged
        assert original_response == original_copy

        # Result should have additional fields
        assert len(result) > len(original_response)
        assert "timestamp" in result
        assert "request_id" in result
        assert "api_version" in result

    def test_custom_api_version(self):
        """Test processor with custom API version."""
        custom_processor = MetadataProcessor(api_version="2.1")
        response = {"data": "test"}

        result = custom_processor.process(response, self.context)

        assert result["api_version"] == "2.1"

    def test_request_id_header_variations(self):
        """Test different request ID header name variations."""
        test_cases = ["X-Request-ID", "X-Request-Id", "Request-ID", "Request-Id"]

        for header_name in test_cases:
            expected_id = f"test-id-{header_name.lower()}"
            self.mock_request.headers = {header_name: expected_id}

            response = {"data": "test"}
            result = self.processor.process(response, self.context)

            assert result["request_id"] == expected_id

    def test_process_flask_json_response(self):
        """Test processing Flask JSON responses."""
        with Flask(__name__).app_context():
            original_data = {"message": "test", "status": "success"}
            response = Response(response=json.dumps(original_data), status=200, mimetype="application/json")

            result = self.processor.process(response, self.context)

            # Should return a Flask Response
            assert isinstance(result, Response)
            assert result.status_code == 200
            assert result.mimetype == "application/json"

            # Parse the JSON content to verify metadata was added
            response_data = json.loads(result.get_data(as_text=True))
            assert response_data["message"] == "test"
            assert response_data["status"] == "success"
            assert "timestamp" in response_data
            assert "request_id" in response_data
            assert "api_version" in response_data
            assert response_data["api_version"] == "1.0"

    def test_process_flask_response_preserves_headers(self):
        """Test that processing Flask responses preserves original headers."""
        with Flask(__name__).app_context():
            original_data = {"data": "test"}
            response = Response(
                response=json.dumps(original_data),
                status=200,
                mimetype="application/json",
                headers={"X-Custom-Header": "custom-value", "Cache-Control": "no-cache"},
            )

            result = self.processor.process(response, self.context)

            # Headers should be preserved
            assert "X-Custom-Header" in result.headers
            assert result.headers["X-Custom-Header"] == "custom-value"
            assert "Cache-Control" in result.headers
            assert result.headers["Cache-Control"] == "no-cache"

    def test_process_flask_response_invalid_json(self):
        """Test processing Flask response with invalid JSON."""
        with Flask(__name__).app_context():
            response = Response(response="invalid json {", status=200, mimetype="application/json")

            result = self.processor.process(response, self.context)

            # Should return original response unchanged when JSON parsing fails
            assert result is response
