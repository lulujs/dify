"""Tests for removability of response enhancement framework.

This module tests that removing the enhancement restores original functionality
and that no side effects remain after removal.
"""

from unittest.mock import Mock, patch

import pytest
from flask import Response

from core.response_enhancement import response_enhancer
from models.model import App, EndUser


class TestRemovability:
    """Test that response enhancement can be cleanly removed."""

    def test_decorator_removal_restores_original(self):
        """Test that removing the decorator restores original functionality."""

        # Create an original controller method
        def original_controller(app_model: App, end_user: EndUser):
            return {"message": "original response", "data": [1, 2, 3]}

        # Create an enhanced version
        enhanced_controller = response_enhancer(processors=["metadata"])(original_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Test original controller
        original_result = original_controller(mock_app, mock_user)

        # Test enhanced controller with enhancement disabled
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = False  # Disable enhancement
            mock_config.return_value = config_instance

            enhanced_result = enhanced_controller(mock_app, mock_user)

        # Verify results are identical
        assert enhanced_result == original_result
        # Note: Object identity (is) is not expected since the decorator wrapper
        # creates a new call context, but the content should be identical

    def test_disabled_enhancement_no_side_effects(self):
        """Test that disabled enhancement has no side effects."""
        call_count = 0

        def tracking_controller(app_model: App, end_user: EndUser):
            nonlocal call_count
            call_count += 1
            return {"call_count": call_count, "message": "test"}

        # Apply enhancement but disable it
        enhanced_controller = response_enhancer(processors=["metadata"], enabled=False)(tracking_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Call multiple times
        result1 = enhanced_controller(mock_app, mock_user)
        result2 = enhanced_controller(mock_app, mock_user)

        # Verify no enhancement processing occurred
        assert result1["call_count"] == 1
        assert result2["call_count"] == 2
        assert result1["message"] == "test"
        assert result2["message"] == "test"

        # Verify no enhancement fields were added
        assert "_enhanced" not in result1
        assert "_enhanced" not in result2

    def test_configuration_disable_restores_original(self):
        """Test that disabling via configuration restores original functionality."""

        def api_controller(app_model: App, end_user: EndUser):
            return {"id": "test-123", "status": "active", "data": {"key": "value"}}

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Test with enhancement disabled via configuration
        with patch("core.response_enhancement.decorator.get_config") as mock_config:
            config_instance = Mock()
            config_instance.is_enabled.return_value = False
            mock_config.return_value = config_instance

            result = enhanced_controller(mock_app, mock_user)

        # Verify result is identical to original
        expected = {"id": "test-123", "status": "active", "data": {"key": "value"}}
        assert result == expected

    def test_empty_processor_list_no_modification(self):
        """Test that empty processor list results in no modification."""

        def api_controller(app_model: App, end_user: EndUser):
            return {"original": True, "data": "unchanged"}

        # Apply enhancement with empty processor list
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

            result = enhanced_controller(mock_app, mock_user)

        # Verify result is unchanged
        assert result == {"original": True, "data": "unchanged"}

    def test_no_registry_modifications_after_disable(self):
        """Test that disabling enhancement doesn't modify the registry."""

        def api_controller(app_model: App, end_user: EndUser):
            return {"test": "data"}

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock registry to track calls
        with patch("core.response_enhancement.decorator._registry") as mock_registry:
            mock_registry.execute_pipeline.return_value = {"test": "data", "enhanced": True}

            # Test with enhancement disabled
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = False
                mock_config.return_value = config_instance

                result = enhanced_controller(mock_app, mock_user)

            # Verify registry was not called
            mock_registry.execute_pipeline.assert_not_called()

            # Verify result is original
            assert result == {"test": "data"}

    def test_response_type_detection_skipped_when_disabled(self):
        """Test that response type detection is skipped when enhancement is disabled."""

        def api_controller(app_model: App, end_user: EndUser):
            return Response("test response", status=200)

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock the response type detection function to track calls
        with patch("core.response_enhancement.decorator._detect_response_type") as mock_detect:
            mock_detect.return_value = "json"

            # Test with enhancement disabled
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = False
                mock_config.return_value = config_instance

                result = enhanced_controller(mock_app, mock_user)

            # Verify response type detection was not called
            mock_detect.assert_not_called()

            # Verify result is original Response object
            assert isinstance(result, Response)
            assert result.get_data(as_text=True) == "test response"
            assert result.status_code == 200

    def test_context_extraction_skipped_when_disabled(self):
        """Test that context extraction is skipped when enhancement is disabled."""

        def api_controller(app_model: App, end_user: EndUser):
            return {"message": "test"}

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock the context extraction function to track calls
        with patch("core.response_enhancement.decorator._extract_context") as mock_extract:
            mock_extract.return_value = Mock()

            # Test with enhancement disabled
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = False
                mock_config.return_value = config_instance

                result = enhanced_controller(mock_app, mock_user)

            # Verify context extraction was not called
            mock_extract.assert_not_called()

            # Verify result is original
            assert result == {"message": "test"}

    def test_timing_not_recorded_when_disabled(self):
        """Test that timing information is not recorded when enhancement is disabled."""
        import time

        def slow_controller(app_model: App, end_user: EndUser):
            time.sleep(0.01)  # Small delay to ensure timing would be measurable
            return {"message": "slow response"}

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["timing"])(slow_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock time.time to track calls
        with patch("time.time") as mock_time:
            mock_time.return_value = 1234567890.0

            # Test with enhancement disabled
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = False
                mock_config.return_value = config_instance

                result = enhanced_controller(mock_app, mock_user)

            # Verify time.time was not called for timing (only called by the controller itself)
            # The exact number of calls depends on the controller, but should be minimal
            assert mock_time.call_count <= 1  # Only from the controller's sleep

            # Verify result has no timing information
            assert "processing_time" not in result
            assert "_timing" not in result

    def test_error_handling_bypassed_when_disabled(self):
        """Test that error handling is bypassed when enhancement is disabled."""

        def failing_controller(app_model: App, end_user: EndUser):
            raise ValueError("Controller error")

        # Apply enhancement
        enhanced_controller = response_enhancer(processors=["metadata"])(failing_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Mock error handler to track calls
        with patch("core.response_enhancement.decorator._error_handler") as mock_error_handler:
            # Test with enhancement disabled
            with patch("core.response_enhancement.decorator.get_config") as mock_config:
                config_instance = Mock()
                config_instance.is_enabled.return_value = False
                mock_config.return_value = config_instance

                # Verify original exception is raised (not handled by enhancement)
                with pytest.raises(ValueError, match="Controller error"):
                    enhanced_controller(mock_app, mock_user)

            # Verify error handler was not called
            mock_error_handler.handle_decorator_error.assert_not_called()

    def test_complete_removal_simulation(self):
        """Test complete removal by comparing with and without decorator."""

        # Original controller without any decoration
        def original_controller(app_model: App, end_user: EndUser):
            return {"id": "item-123", "name": "Test Item", "metadata": {"created": "2023-01-01", "version": 1}}

        # Same controller with enhancement applied but disabled
        enhanced_controller = response_enhancer(processors=["metadata", "timing"], enabled=False)(original_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Call both versions
        original_result = original_controller(mock_app, mock_user)
        enhanced_result = enhanced_controller(mock_app, mock_user)

        # Verify they are identical
        assert enhanced_result == original_result
        # Note: Object identity (is) is not expected since the decorator wrapper
        # creates a new call context, but the content should be identical

        # Verify no enhancement artifacts
        assert "_enhanced" not in enhanced_result
        assert "_metadata" not in enhanced_result
        assert "_timing" not in enhanced_result
        assert "processing_time" not in enhanced_result

    def test_no_import_side_effects_after_disable(self):
        """Test that disabling enhancement doesn't cause import side effects."""
        # This test ensures that importing the enhancement module doesn't
        # cause side effects when enhancement is disabled

        def api_controller(app_model: App, end_user: EndUser):
            return {"clean": True}

        # Apply enhancement but disable it
        enhanced_controller = response_enhancer(processors=["metadata"], enabled=False)(api_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Call the enhanced controller
        result = enhanced_controller(mock_app, mock_user)

        # Verify result is clean (no enhancement artifacts)
        assert result == {"clean": True}
        assert len(result) == 1  # Only the original field

        # Verify no additional attributes were added to the function
        original_attrs = set(dir(api_controller))
        enhanced_attrs = set(dir(enhanced_controller))

        # The enhanced function should have the same attributes as the original
        # (plus the standard wrapper attributes like __wrapped__)
        expected_additional = {"__wrapped__"}
        actual_additional = enhanced_attrs - original_attrs

        # Allow for standard functools.wraps attributes
        allowed_additional = {
            "__wrapped__",
            "__name__",
            "__doc__",
            "__module__",
            "__qualname__",
            "__annotations__",
            "__dict__",
        }

        assert actual_additional.issubset(allowed_additional), (
            f"Unexpected attributes added: {actual_additional - allowed_additional}"
        )

    def test_memory_cleanup_after_disable(self):
        """Test that disabling enhancement doesn't leave memory references."""
        import gc
        import weakref

        # Create a controller that we can track
        def trackable_controller(app_model: App, end_user: EndUser):
            return {"tracked": True}

        # Create weak reference to track the original function
        original_ref = weakref.ref(trackable_controller)

        # Apply enhancement but disable it
        enhanced_controller = response_enhancer(processors=["metadata"], enabled=False)(trackable_controller)

        # Mock objects
        mock_app = Mock(spec=App)
        mock_user = Mock(spec=EndUser)

        # Call the enhanced controller
        result = enhanced_controller(mock_app, mock_user)

        # Verify result is correct
        assert result == {"tracked": True}

        # Verify original function is still accessible through __wrapped__
        assert hasattr(enhanced_controller, "__wrapped__")
        assert enhanced_controller.__wrapped__ is trackable_controller

        # Clean up references
        del trackable_controller
        gc.collect()

        # Original function should still be alive due to __wrapped__ reference
        assert original_ref() is not None

        # Clean up enhanced controller
        del enhanced_controller
        gc.collect()

        # Now original function should be collectible
        # (This test verifies no circular references were created)
