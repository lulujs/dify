"""Tests for service layer isolation in response enhancement framework.

This module tests that the response enhancement framework does not require
any changes to the service layer code and that business logic remains
completely unchanged.
"""

import inspect
from unittest.mock import Mock, patch

import pytest

from core.response_enhancement import response_enhancer
from models.model import App, AppMode, EndUser
from services.app_generate_service import AppGenerateService


class TestServiceLayerIsolation:
    """Test that service layer remains isolated from response enhancement."""

    def test_service_layer_unchanged_with_enhancement(self):
        """Test that service layer code remains unchanged when enhancement is applied."""
        # Create a mock service method that represents typical service layer code
        original_service_method = Mock(return_value={"result": "success", "data": "test"})

        # Create a mock controller method that uses the service
        def mock_controller_method(app_model: App, end_user: EndUser):
            # This simulates how controllers typically call service layer
            return original_service_method(app_model, end_user)

        # Apply response enhancement to the controller method
        enhanced_controller = response_enhancer(processors=["metadata"])(mock_controller_method)

        # Create mock objects
        mock_app = Mock(spec=App)
        mock_app.mode = AppMode.COMPLETION
        mock_user = Mock(spec=EndUser)

        # Mock the configuration to enable enhancement
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = ["metadata"]
            config_instance.get_global_config.return_value = Mock(fail_silently=True)
            mock_config.return_value = config_instance

            # Mock the registry to avoid actual processor execution
            with patch("core.response_enhancement.decorator._registry") as mock_registry:
                mock_registry.execute_pipeline.return_value = {
                    "result": "success",
                    "data": "test",
                    "metadata": {"timestamp": "2023-01-01"},
                }

                # Call the enhanced controller method
                result = enhanced_controller(mock_app, mock_user)

        # Verify that the service method was called with the same arguments
        original_service_method.assert_called_once_with(mock_app, mock_user)

        # Verify that the service layer method signature and behavior is unchanged
        assert original_service_method.call_count == 1
        assert original_service_method.call_args[0] == (mock_app, mock_user)

    def test_app_generate_service_unchanged(self):
        """Test that AppGenerateService.generate method remains unchanged."""
        # This test verifies that the actual service layer method signatures
        # and behavior are not affected by the response enhancement framework

        # Get the original method
        original_generate = AppGenerateService.generate

        # Verify the method exists and is callable
        assert callable(original_generate), "AppGenerateService.generate should be callable"

        # Verify the method is still a classmethod
        assert isinstance(inspect.getattr_static(AppGenerateService, "generate"), classmethod)

        # Verify the method has the core parameters we expect
        sig = inspect.signature(original_generate)
        param_names = list(sig.parameters.keys())

        # Check that essential parameters exist (the exact signature may vary)
        essential_params = {"user", "args", "invoke_from"}
        actual_params = set(param_names[1:])  # Skip 'cls'

        assert essential_params.issubset(actual_params), (
            f"Missing essential parameters. Expected {essential_params}, got {actual_params}"
        )

        # Verify the method still accepts the parameters we need
        assert "user" in param_names, "Service method should accept 'user' parameter"
        assert "args" in param_names, "Service method should accept 'args' parameter"
        assert "invoke_from" in param_names, "Service method should accept 'invoke_from' parameter"

    def test_service_layer_no_enhancement_dependencies(self):
        """Test that service layer has no dependencies on response enhancement."""
        # Import the service module and check it doesn't import response enhancement
        import services.app_generate_service as service_module

        # Get all imported modules in the service
        service_source = inspect.getsource(service_module)

        # Verify no response enhancement imports
        enhancement_imports = ["response_enhancement", "PostProcessor", "ProcessingContext", "response_enhancer"]

        for import_name in enhancement_imports:
            assert import_name not in service_source, f"Service layer should not import {import_name}"

    def test_business_logic_isolation(self):
        """Test that business logic execution is completely isolated from enhancement."""
        # Create a mock business logic function
        business_logic_calls = []

        def mock_business_logic(app_model, end_user):
            business_logic_calls.append((app_model, end_user))
            return {"business_result": "processed"}

        # Create controller that uses business logic
        def controller_method(app_model: App, end_user: EndUser):
            return mock_business_logic(app_model, end_user)

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=[])(controller_method)

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

        # Verify business logic was called exactly once with correct arguments
        assert len(business_logic_calls) == 1
        assert business_logic_calls[0] == (mock_app, mock_user)

        # Verify result is unchanged when no processors are applied
        assert result == {"business_result": "processed"}

    def test_service_layer_error_handling_unchanged(self):
        """Test that service layer error handling remains unchanged."""

        # Create a service method that raises an exception
        def failing_service_method(app_model, end_user):
            raise ValueError("Service layer error")

        def controller_method(app_model: App, end_user: EndUser):
            return failing_service_method(app_model, end_user)

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=[])(controller_method)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock configuration
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = True
            config_instance.get_processors_for_endpoint.return_value = []
            mock_config.return_value = config_instance

            # Verify that service layer exceptions propagate unchanged
            with pytest.raises(ValueError, match="Service layer error"):
                enhanced_controller(mock_app, mock_user)

    def test_service_method_call_patterns_unchanged(self):
        """Test that typical service method call patterns remain unchanged."""
        # Test various common service layer call patterns

        # Pattern 1: Service method with keyword arguments
        service_calls = []

        def service_with_kwargs(app_model, user, streaming=True, invoke_from=None):
            service_calls.append(
                {"app_model": app_model, "user": user, "streaming": streaming, "invoke_from": invoke_from}
            )
            return {"result": "success"}

        def controller_method(app_model: App, end_user: EndUser):
            from core.app.entities.app_invoke_entities import InvokeFrom

            return service_with_kwargs(
                app_model=app_model, user=end_user, streaming=False, invoke_from=InvokeFrom.SERVICE_API
            )

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=[])(controller_method)

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

        # Verify service was called with correct arguments
        assert len(service_calls) == 1
        call = service_calls[0]
        assert call["app_model"] == mock_app
        assert call["user"] == mock_user
        assert call["streaming"] is False
        assert call["invoke_from"] is not None  # InvokeFrom.SERVICE_API

    def test_no_service_layer_modifications_required(self):
        """Test that existing service layer code works without any modifications."""
        # This test simulates the exact pattern used in the actual codebase

        # Mock the actual service method signature and behavior
        with patch.object(AppGenerateService, "generate") as mock_generate:
            mock_generate.return_value = {"message": "Hello", "conversation_id": "123"}

            # Create a controller method that mimics the actual completion controller
            def completion_controller(app_model: App, end_user: EndUser):
                from core.app.entities.app_invoke_entities import InvokeFrom

                args = {"inputs": {"query": "test"}, "response_mode": "blocking", "auto_generate_name": False}

                # This is the exact pattern used in the actual controller
                # Note: We'll call with the parameters that the service actually accepts
                response = AppGenerateService.generate(
                    user=end_user,
                    args=args,
                    invoke_from=InvokeFrom.SERVICE_API,
                    streaming=False,
                )

                return response

            # Apply enhancement
            enhanced_controller = response_enhancer(processors=[])(completion_controller)

            # Mock objects
            mock_app = Mock(spec=App)
            mock_app.mode = AppMode.COMPLETION
            mock_user = Mock(spec=EndUser)

            # Mock configuration
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = True
                config_instance.get_processors_for_endpoint.return_value = []
                mock_config.return_value = config_instance

                # Call enhanced controller
                result = enhanced_controller(mock_app, mock_user)

            # Verify service was called with the expected arguments
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args

            assert call_args[1]["user"] == mock_user
            assert call_args[1]["streaming"] is False
            assert "invoke_from" in call_args[1]
            assert "args" in call_args[1]

            # Verify result is unchanged
            assert result == {"message": "Hello", "conversation_id": "123"}
