"""Tests for StandardFormatProcessor."""

import json
from unittest.mock import Mock

from flask import Flask, Response

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processors.standard_format import StandardFormatProcessor
from models.model import App, EndUser


class TestStandardFormatProcessor:
    """Test cases for StandardFormatProcessor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = StandardFormatProcessor()
        self.mock_request = Mock()
        self.mock_app = Mock(spec=App)
        self.mock_user = Mock(spec=EndUser)

    def create_context(self, original_response=None, response_type=None):
        """Create a processing context for testing."""
        return ProcessingContext(
            request=self.mock_request,
            app_model=self.mock_app,
            end_user=self.mock_user,
            endpoint_name="/test",
            method="POST",
            original_response=original_response or {},
            start_time=1234567890.0,
            response_type=response_type,
        )

    def test_can_process_dict_response(self):
        """Test that processor can handle dict responses."""
        response = {"message": "test"}
        context = self.create_context(response)

        assert self.processor.can_process(response, context) is True

    def test_can_process_flask_json_response(self):
        """Test that processor can handle Flask JSON responses."""
        with Flask(__name__).app_context():
            response = Response(response=json.dumps({"message": "test"}), status=200, mimetype="application/json")
            context = self.create_context(response)

            assert self.processor.can_process(response, context) is True

    def test_can_process_flask_streaming_response(self):
        """Test that processor can handle Flask streaming responses."""
        with Flask(__name__).app_context():
            response = Response(response="data: test\n\n", status=200, mimetype="text/event-stream")
            context = self.create_context(response)

            assert self.processor.can_process(response, context) is True

    def test_cannot_process_non_json_response(self):
        """Test that processor skips non-JSON responses."""
        response = "plain text"
        context = self.create_context(response)

        assert self.processor.can_process(response, context) is False

    def test_process_dict_response_success(self):
        """Test processing dict response with success status."""
        response = {"message": "test", "data": "some data"}
        context = self.create_context(response)

        result = self.processor.process(response, context)

        expected = {"returnCode": "SUC0000", "errorMsg": None, "body": response}
        assert result == expected

    def test_process_flask_response_success(self):
        """Test processing Flask response with success status."""
        with Flask(__name__).app_context():
            original_data = {"message": "test"}
            response = Response(response=json.dumps(original_data), status=200, mimetype="application/json")
            context = self.create_context(response)

            result = self.processor.process(response, context)

            assert isinstance(result, Response)
            assert result.status_code == 200
            assert result.mimetype == "application/json"

            response_data = json.loads(result.get_data(as_text=True))
            expected = {"returnCode": "SUC0000", "errorMsg": None, "body": original_data}
            assert response_data == expected

    def test_process_flask_response_error(self):
        """Test processing Flask response with error status."""
        with Flask(__name__).app_context():
            original_data = {"error": "something went wrong"}
            response = Response(response=json.dumps(original_data), status=500, mimetype="application/json")
            context = self.create_context(response)

            result = self.processor.process(response, context)

            assert isinstance(result, Response)
            assert result.status_code == 500
            assert result.mimetype == "application/json"

            response_data = json.loads(result.get_data(as_text=True))
            expected = {"returnCode": "FAIL000", "errorMsg": None, "body": original_data}
            assert response_data == expected

    def test_process_streaming_response(self):
        """Test processing streaming response."""

        def mock_generator():
            yield "data: chunk1\n\n"
            yield "data: chunk2\n\n"

        response = mock_generator()
        context = self.create_context(response)

        result = self.processor.process(response, context)

        # Collect all chunks from the generator
        chunks = list(result)

        # Should have data chunks plus final DONE chunk
        assert len(chunks) >= 3  # At least 2 data chunks + 1 DONE chunk

        # Check that final chunk is DONE type
        final_chunk_data = json.loads(chunks[-1].replace("data: ", "").strip())
        assert final_chunk_data["type"] == "DONE"
        assert final_chunk_data["returnCode"] == "SUC0000"
        assert final_chunk_data["errorMsg"] is None
        assert final_chunk_data["data"] is None

    def test_get_status_code_from_flask_response(self):
        """Test extracting status code from Flask response."""
        with Flask(__name__).app_context():
            response = Response(status=404)
            context = self.create_context(response)

            status_code = self.processor._get_status_code(response, context)
            assert status_code == 404

    def test_get_status_code_default(self):
        """Test default status code for non-Flask responses."""
        response = {"message": "test"}
        context = self.create_context(response)

        status_code = self.processor._get_status_code(response, context)
        assert status_code == 200

    def test_process_skips_unsupported_response(self):
        """Test that processor skips unsupported response types."""
        response = "plain text"
        context = self.create_context(response)

        result = self.processor.process(response, context)
        assert result == response  # Should return unchanged

    def test_streaming_response_error_handling(self):
        """Test error handling in streaming response processing."""

        def error_generator():
            yield "data: chunk1\n\n"
            raise Exception("Stream error")

        response = error_generator()
        context = self.create_context(response)

        result = self.processor.process(response, context)
        chunks = list(result)

        # Should have at least one chunk (the error chunk)
        assert len(chunks) >= 1

        # Final chunk should be an error
        final_chunk_data = json.loads(chunks[-1].replace("data: ", "").strip())
        assert final_chunk_data["returnCode"] == "FAIL000"
        assert final_chunk_data["errorMsg"] is not None
        assert final_chunk_data["type"] == "DONE"

    def test_preserve_original_headers(self):
        """Test that original headers are preserved in Flask responses."""
        with Flask(__name__).app_context():
            response = Response(
                response=json.dumps({"test": "data"}),
                status=200,
                mimetype="application/json",
                headers={"X-Custom-Header": "custom-value"},
            )
            context = self.create_context(response)

            result = self.processor.process(response, context)

            assert "X-Custom-Header" in result.headers
            assert result.headers["X-Custom-Header"] == "custom-value"

    def test_process_flask_response_invalid_json(self):
        """Test processing Flask response with invalid JSON."""
        with Flask(__name__).app_context():
            response = Response(response="invalid json {", status=200, mimetype="application/json")
            context = self.create_context(response)

            result = self.processor.process(response, context)

            # Should return standardized format with empty body when JSON parsing fails
            assert isinstance(result, Response)
            response_data = json.loads(result.get_data(as_text=True))
            expected = {"returnCode": "SUC0000", "errorMsg": None, "body": {}}
            assert response_data == expected
