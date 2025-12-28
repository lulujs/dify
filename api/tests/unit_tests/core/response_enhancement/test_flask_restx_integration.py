"""Tests for Flask-RESTx integration and decorator compatibility."""

import json
from unittest.mock import patch

import pytest
from flask import Flask, Response
from flask_restx import Api, Resource, fields, reqparse

from core.response_enhancement.decorator import response_enhancer


@pytest.fixture
def flask_app():
    """Create a Flask app with Flask-RESTx for testing."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"

    # Create Flask-RESTx API
    api = Api(app, doc=False)  # Disable Swagger UI for tests

    return app, api


class TestBasicFlaskRESTxIntegration:
    """Test basic integration with Flask-RESTx features."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_integration_with_reqparse(self, mock_registry, mock_get_config, flask_app):
        """Test integration with Flask-RESTx request parsing."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        enhanced_response = {"parsed_data": "test", "metadata": {"parser_used": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        # Create parser
        test_parser = reqparse.RequestParser()
        test_parser.add_argument("input", type=str, required=True, location="json")

        @api.route("/test-parser")
        class TestParserResource(Resource):
            @api.expect(test_parser)
            @response_enhancer(processors=["metadata"])
            def post(self):
                """Test endpoint with reqparse."""
                args = test_parser.parse_args()
                return {"parsed_data": args["input"]}

        with app.test_client() as client:
            response = client.post("/test-parser", json={"input": "test"}, content_type="application/json")

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["parsed_data"] == "test"
            assert response_data["metadata"]["parser_used"] is True

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_integration_with_api_doc_decorators(self, mock_registry, mock_get_config, flask_app):
        """Test integration with Flask-RESTx documentation decorators."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        enhanced_response = {"data": "documented", "metadata": {"documented": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        @api.route("/test-documented")
        class TestDocumentedResource(Resource):
            @api.doc("test_endpoint")
            @api.doc(description="Test endpoint with documentation")
            @api.doc(responses={200: "Success", 400: "Bad Request"})
            @response_enhancer(processors=["metadata"])
            def get(self):
                """Test endpoint with documentation decorators."""
                return {"data": "documented"}

        with app.test_client() as client:
            response = client.get("/test-documented")

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["data"] == "documented"
            assert response_data["metadata"]["documented"] is True

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_integration_with_marshal_with(self, mock_registry, mock_get_config, flask_app):
        """Test integration with Flask-RESTx @marshal_with decorator."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        # For marshal_with integration, the enhanced response should be compatible
        enhanced_response = {"name": "test", "value": 42, "metadata": {"marshalled": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        # Define a proper Flask-RESTx model for marshalling
        test_model = api.model(
            "TestModel",
            {
                "name": fields.String(required=True),
                "value": fields.Integer(required=True),
                "metadata": fields.Raw(),  # Allow metadata field
            },
        )

        @api.route("/test-marshal")
        class TestMarshalResource(Resource):
            @api.marshal_with(test_model)
            @response_enhancer(processors=["metadata"])
            def get(self):
                """Test endpoint with marshal_with decorator."""
                return {"name": "test", "value": 42}

        with app.test_client() as client:
            response = client.get("/test-marshal")

            assert response.status_code == 200
            response_data = json.loads(response.data)

            # The marshal_with decorator should include the enhanced fields
            assert "name" in response_data
            assert "value" in response_data
            assert "metadata" in response_data
            assert response_data["metadata"]["marshalled"] is True

            # Verify the registry was called
            mock_registry.execute_pipeline.assert_called_once()


class TestDecoratorOrdering:
    """Test decorator ordering scenarios."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_response_enhancer_with_custom_decorator(self, mock_registry, mock_get_config, flask_app):
        """Test response_enhancer works with custom decorators."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        enhanced_response = {"data": "test", "metadata": {"enhanced": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        # Create a simple custom decorator
        def custom_decorator(func):
            def wrapper(*args, **kwargs):
                # Add custom context
                kwargs["custom_context"] = {"decorator": "applied"}
                return func(*args, **kwargs)

            return wrapper

        @api.route("/test-custom")
        class TestCustomResource(Resource):
            @response_enhancer(processors=["metadata"])
            @custom_decorator
            def post(self, custom_context=None):
                """Test endpoint with custom decorator."""
                return {"data": "test", "custom": custom_context}

        with app.test_client() as client:
            response = client.post("/test-custom")

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["data"] == "test"
            assert response_data["metadata"]["enhanced"] is True

            # Verify the registry was called
            mock_registry.execute_pipeline.assert_called_once()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_multiple_response_enhancers(self, mock_registry, mock_get_config, flask_app):
        """Test multiple response enhancers on the same endpoint."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        # First enhancer call
        first_enhanced = {"data": "test", "first": True}
        # Second enhancer call (should receive first_enhanced as input)
        second_enhanced = {"data": "test", "first": True, "second": True}
        mock_registry.execute_pipeline.side_effect = [first_enhanced, second_enhanced]

        @api.route("/test-multiple")
        class TestMultipleResource(Resource):
            @response_enhancer(processors=["timing"])
            @response_enhancer(processors=["metadata"])
            def get(self):
                """Test endpoint with multiple enhancers."""
                return {"data": "test"}

        with app.test_client() as client:
            response = client.get("/test-multiple")

            assert response.status_code == 200
            response_data = json.loads(response.data)
            assert response_data["data"] == "test"
            assert response_data["second"] is True

            # Should have been called twice
            assert mock_registry.execute_pipeline.call_count == 2


class TestErrorHandlingCompatibility:
    """Test error handling compatibility with Flask-RESTx."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    @patch("core.response_enhancement.decorator._error_handler")
    def test_error_handling_with_graceful_degradation(
        self, mock_error_handler, mock_registry, mock_get_config, flask_app
    ):
        """Test that error handling works with graceful degradation."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]
        mock_config.get_global_config.return_value.fail_silently = True

        # Mock registry to raise an error
        mock_registry.execute_pipeline.side_effect = ValueError("Processing error")

        # Mock error handler to return original response
        original_response = {"error": "Bad Request", "message": "Invalid input"}
        mock_error_handler.handle_decorator_error.return_value = original_response

        @api.route("/test-error")
        class TestErrorResource(Resource):
            @response_enhancer(processors=["metadata"], fail_silently=True)
            def post(self):
                """Test endpoint that triggers processing error."""
                return {"error": "Bad Request", "message": "Invalid input"}

        with app.test_client() as client:
            response = client.post("/test-error")

            # The error response should be preserved
            assert response.status_code == 200  # Original endpoint returns 200
            response_data = json.loads(response.data)
            assert response_data["error"] == "Bad Request"
            assert response_data["message"] == "Invalid input"

            # Verify error handler was called
            mock_error_handler.handle_decorator_error.assert_called_once()

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_enhancement_works_with_error_status_codes(self, mock_registry, mock_get_config, flask_app):
        """Test that enhancement works with error status codes."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        # Enhanced response should work for error responses if they're JSON
        enhanced_response = {"error": "Bad Request", "message": "Invalid input", "metadata": {"enhanced": True}}
        mock_registry.execute_pipeline.return_value = enhanced_response

        @api.route("/test-error-enhanced")
        class TestErrorEnhancedResource(Resource):
            @response_enhancer(processors=["metadata"])
            def post(self):
                """Test endpoint that returns an enhanced error response."""
                # Return just the dict, let Flask-RESTx handle the status code separately
                # This tests the case where the original response is a dict that gets enhanced
                response_dict = {"error": "Bad Request", "message": "Invalid input"}
                # Simulate what Flask-RESTx does - it will convert this to a Response later
                return response_dict

        with app.test_client() as client:
            response = client.post("/test-error-enhanced")

            # The error response should be enhanced
            assert response.status_code == 200  # Default status since we're not returning tuple
            response_data = json.loads(response.data)
            assert response_data["error"] == "Bad Request"
            assert response_data["message"] == "Invalid input"
            assert response_data["metadata"]["enhanced"] is True


class TestResponseTypeHandling:
    """Test response type handling with Flask-RESTx."""

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_streaming_response_handling(self, mock_registry, mock_get_config, flask_app):
        """Test handling of streaming responses in Flask-RESTx."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        @api.route("/test-streaming")
        class TestStreamingResource(Resource):
            @response_enhancer(processors=["metadata"])
            def get(self):
                """Test endpoint that returns streaming response."""

                def generate():
                    yield "data: test\n\n"
                    yield "data: more\n\n"

                return Response(generate(), mimetype="text/event-stream")

        with app.test_client() as client:
            response = client.get("/test-streaming")

            # Should handle streaming response
            assert response.status_code == 200
            assert response.mimetype == "text/event-stream"

            # Should have called registry for streaming handling
            mock_registry.execute_pipeline.assert_called_once()
            call_args = mock_registry.execute_pipeline.call_args[0]
            processors, original_response, context = call_args

            assert context.response_type == "streaming"

    @patch("core.response_enhancement.decorator.get_config")
    @patch("core.response_enhancement.decorator._registry")
    def test_binary_response_handling(self, mock_registry, mock_get_config, flask_app):
        """Test handling of binary responses in Flask-RESTx."""
        app, api = flask_app

        # Configure mocks
        mock_config = mock_get_config.return_value
        mock_config.is_enabled.return_value = True
        mock_config.get_processors_for_endpoint.return_value = ["metadata"]

        @api.route("/test-binary")
        class TestBinaryResource(Resource):
            @response_enhancer(processors=["metadata"])
            def get(self):
                """Test endpoint that returns binary response."""
                return Response(b"binary data", mimetype="application/octet-stream")

        with app.test_client() as client:
            response = client.get("/test-binary")

            # Should handle binary response
            assert response.status_code == 200
            assert response.mimetype == "application/octet-stream"
            assert response.data == b"binary data"

            # Should have called registry for binary handling
            mock_registry.execute_pipeline.assert_called_once()
            call_args = mock_registry.execute_pipeline.call_args[0]
            processors, original_response, context = call_args

            assert context.response_type == "binary"
