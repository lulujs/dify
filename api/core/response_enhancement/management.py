"""Management interface for response enhancement configuration."""

import logging
from typing import Any, Optional

from .config import get_config

logger = logging.getLogger(__name__)


class ResponseEnhancementManager:
    """Management interface for response enhancement configuration.

    Provides a high-level interface for controlling response enhancement
    settings at runtime without directly manipulating the configuration.
    """

    def __init__(self):
        """Initialize the management interface."""
        self._config = get_config()

    def enable_globally(self) -> None:
        """Enable response enhancement globally."""
        self._config.set_global_enabled(True)
        logger.info("Response enhancement enabled globally")

    def disable_globally(self) -> None:
        """Disable response enhancement globally."""
        self._config.set_global_enabled(False)
        logger.info("Response enhancement disabled globally")

    def enable_for_endpoint(self, endpoint: str) -> None:
        """Enable response enhancement for a specific endpoint.

        Args:
            endpoint: The endpoint path to enable
        """
        self._config.set_endpoint_enabled(endpoint, True)
        logger.info("Response enhancement enabled for endpoint: %s", endpoint)

    def disable_for_endpoint(self, endpoint: str) -> None:
        """Disable response enhancement for a specific endpoint.

        Args:
            endpoint: The endpoint path to disable
        """
        self._config.set_endpoint_enabled(endpoint, False)
        logger.info("Response enhancement disabled for endpoint: %s", endpoint)

    def reset_global_setting(self) -> None:
        """Reset global setting to configuration file value."""
        self._config.clear_global_enabled_override()
        logger.info("Reset global response enhancement setting to config file value")

    def reset_endpoint_setting(self, endpoint: str) -> None:
        """Reset endpoint setting to configuration file value.

        Args:
            endpoint: The endpoint path to reset
        """
        self._config.clear_endpoint_enabled_override(endpoint)
        logger.info("Reset response enhancement setting for endpoint: %s", endpoint)

    def reset_all_settings(self) -> None:
        """Reset all settings to configuration file values."""
        self._config.clear_all_overrides()
        logger.info("Reset all response enhancement settings to config file values")

    def get_status(self) -> dict[str, Any]:
        """Get current response enhancement status.

        Returns:
            Dictionary containing current status information
        """
        global_config = self._config.get_global_config()
        runtime_overrides = self._config.get_runtime_overrides()

        return {
            "global_enabled": self._config.is_enabled(),
            "global_enabled_by_config": global_config.enabled,
            "global_enabled_override": runtime_overrides["global_enabled"],
            "default_processors": global_config.default_processors,
            "fail_silently": global_config.fail_silently,
            "log_level": global_config.log_level,
            "endpoint_overrides": runtime_overrides["endpoint_overrides"],
            "config_file_path": self._config.config_path,
            "hot_reload_active": self._config.is_monitoring_active(),
        }

    def check_endpoint_status(self, endpoint: str) -> dict[str, Any]:
        """Check status for a specific endpoint.

        Args:
            endpoint: The endpoint path to check

        Returns:
            Dictionary containing endpoint status information
        """
        processors = self._config.get_processors_for_endpoint(endpoint)
        enabled = self._config.is_enabled(endpoint)
        enabled_by_config = self._config.is_endpoint_enabled_by_config(endpoint)
        runtime_overrides = self._config.get_runtime_overrides()

        return {
            "endpoint": endpoint,
            "enabled": enabled,
            "enabled_by_config": enabled_by_config,
            "enabled_override": runtime_overrides["endpoint_overrides"].get(endpoint),
            "processors": processors,
            "matching_patterns": self._get_matching_patterns(endpoint),
        }

    def _get_matching_patterns(self, endpoint: str) -> list[str]:
        """Get configuration patterns that match the given endpoint.

        Args:
            endpoint: The endpoint path to check

        Returns:
            List of matching patterns
        """
        matching_patterns = []
        endpoint_configs = self._config.get_endpoint_configs()

        for endpoint_config in endpoint_configs:
            if self._config.matches_pattern(endpoint, endpoint_config.endpoint_pattern):
                matching_patterns.append(endpoint_config.endpoint_pattern)

        return matching_patterns

    def reload_configuration(self) -> None:
        """Manually reload configuration from file."""
        self._config.reload()
        logger.info("Manually reloaded response enhancement configuration")

    def validate_configuration_file(self) -> dict[str, Any]:
        """Validate the current configuration file.

        Returns:
            Dictionary containing validation results
        """
        import json
        import os

        import yaml
        from jsonschema import ValidationError

        if not os.path.exists(self._config.config_path):
            return {"valid": False, "error": "Configuration file not found", "path": self._config.config_path}

        try:
            with open(self._config.config_path, encoding="utf-8") as f:
                if self._config.config_path.endswith(".json"):
                    config_data = json.load(f)
                else:
                    config_data = yaml.safe_load(f) or {}

            # Validate using the same method as the config loader
            self._config.validate_config(config_data)

            return {"valid": True, "path": self._config.config_path, "data": config_data}

        except ValidationError as e:
            return {
                "valid": False,
                "error": f"Validation error: {e.message}",
                "path": self._config.config_path,
                "error_path": " -> ".join(str(p) for p in e.absolute_path),
            }
        except Exception as e:
            return {"valid": False, "error": f"Error reading configuration: {str(e)}", "path": self._config.config_path}


# Global manager instance
_manager_instance: Optional[ResponseEnhancementManager] = None


def get_manager() -> ResponseEnhancementManager:
    """Get the global response enhancement manager instance.

    Returns:
        Global manager instance
    """
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = ResponseEnhancementManager()

    return _manager_instance
