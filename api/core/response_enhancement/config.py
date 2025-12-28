"""Configuration management for response enhancement."""

import json
import logging
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

import yaml
from jsonschema import ValidationError, validate

logger = logging.getLogger(__name__)

# JSON Schema for configuration validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "global": {
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean"},
                "default_processors": {"type": "array", "items": {"type": "string"}},
                "fail_silently": {"type": "boolean"},
                "log_level": {"type": "string", "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
            },
            "additionalProperties": False,
        },
        "endpoints": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string"},
                    "processors": {"type": "array", "items": {"type": "string"}},
                    "enabled": {"type": "boolean"},
                    "conditions": {
                        "type": "object",
                        "properties": {
                            "response_type": {"type": "string", "enum": ["json", "streaming", "binary", "text"]},
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "user_type": {"type": "string", "enum": ["authenticated", "anonymous"]},
                        },
                        "additionalProperties": True,
                    },
                },
                "required": ["pattern"],
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


@dataclass
class EndpointConfig:
    """Configuration for a specific endpoint pattern.

    Attributes:
        endpoint_pattern: Pattern to match endpoint paths (supports wildcards)
        processors: List of processor names to apply
        enabled: Whether processing is enabled for this endpoint
        conditions: Additional conditions for processing (optional)
    """

    endpoint_pattern: str
    processors: list[str]
    enabled: bool = True
    conditions: Optional[dict[str, Any]] = None


@dataclass
class GlobalConfig:
    """Global configuration for response enhancement.

    Attributes:
        enabled: Whether response enhancement is globally enabled
        default_processors: Default processors to apply when none specified
        fail_silently: Whether to continue on processor errors
        log_level: Logging level for enhancement operations
    """

    enabled: bool = True
    default_processors: list[str] = field(default_factory=list)
    fail_silently: bool = True
    log_level: str = "INFO"


class EnhancementConfig:
    """Configuration manager for response enhancement framework.

    This class handles loading, parsing, and providing access to configuration
    settings for the response enhancement system. It supports both global
    settings and endpoint-specific configurations with hot-reload capability.
    """

    def __init__(self, config_path: Optional[str] = None, enable_hot_reload: bool = False):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file. If None, uses default path.
            enable_hot_reload: Whether to enable automatic configuration reloading.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.global_config = GlobalConfig()
        self.endpoint_configs: list[EndpointConfig] = []
        self._last_modified: Optional[float] = None
        self._reload_callbacks: list[Callable[[], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()
        self._config_lock = threading.RLock()

        # Runtime overrides (take precedence over config file)
        self._runtime_global_enabled: Optional[bool] = None
        self._runtime_endpoint_overrides: dict[str, bool] = {}

        self._load_config()

        if enable_hot_reload:
            self.start_monitoring()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Look for config file in the api directory
        api_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

        # Try YAML first, then JSON
        yaml_path = os.path.join(api_dir, "configs", "response_enhancement.yaml")
        json_path = os.path.join(api_dir, "configs", "response_enhancement.json")

        if os.path.exists(yaml_path):
            return yaml_path
        elif os.path.exists(json_path):
            return json_path
        else:
            return yaml_path  # Default to YAML path for creation

    def _load_config(self) -> None:
        """Load configuration from file."""
        with self._config_lock:
            if not os.path.exists(self.config_path):
                logger.info("Configuration file not found at %s, using defaults", self.config_path)
                self._last_modified = None
                return

            try:
                # Check if file has been modified (skip for non-existent files in tests)
                try:
                    current_modified = os.path.getmtime(self.config_path)
                    if self._last_modified is not None and current_modified <= self._last_modified:
                        return  # No changes detected
                except (OSError, FileNotFoundError):
                    # File doesn't exist or can't be accessed, continue with loading
                    current_modified = time.time()

                with open(self.config_path, encoding="utf-8") as f:
                    # Determine file format based on extension
                    if self.config_path.endswith(".json"):
                        config_data = json.load(f)
                    else:
                        config_data = yaml.safe_load(f) or {}

                # Validate configuration against schema
                try:
                    validate(instance=config_data, schema=CONFIG_SCHEMA)
                except ValidationError as e:
                    logger.exception("Configuration validation failed: %s", e.message)
                    logger.exception("Invalid configuration at path: %s", " -> ".join(str(p) for p in e.absolute_path))
                    raise ValueError(f"Invalid configuration: {e.message}") from e

                # Load global configuration
                global_data = config_data.get("global", {})
                self.global_config = GlobalConfig(
                    enabled=global_data.get("enabled", True),
                    default_processors=global_data.get("default_processors", []),
                    fail_silently=global_data.get("fail_silently", True),
                    log_level=global_data.get("log_level", "INFO"),
                )

                # Load endpoint configurations
                endpoints_data = config_data.get("endpoints", [])
                self.endpoint_configs = []
                for endpoint_data in endpoints_data:
                    endpoint_config = EndpointConfig(
                        endpoint_pattern=endpoint_data["pattern"],
                        processors=endpoint_data.get("processors", []),
                        enabled=endpoint_data.get("enabled", True),
                        conditions=endpoint_data.get("conditions"),
                    )
                    self.endpoint_configs.append(endpoint_config)

                self._last_modified = current_modified
                logger.info("Loaded configuration from %s", self.config_path)

                # Apply environment variable overrides
                self._apply_environment_overrides()

                # Notify callbacks of configuration change
                self._notify_reload_callbacks()

            except Exception:
                logger.exception("Error loading configuration from %s", self.config_path)
                # Keep default configuration on error

    def get_processors_for_endpoint(self, endpoint: str) -> list[str]:
        """Get the list of processors for a specific endpoint.

        Args:
            endpoint: The endpoint path to match

        Returns:
            List of processor names to apply to this endpoint
        """
        with self._config_lock:
            if not self.global_config.enabled:
                return []

            # Find matching endpoint configuration
            for endpoint_config in self.endpoint_configs:
                if self._matches_pattern(endpoint, endpoint_config.endpoint_pattern):
                    if endpoint_config.enabled:
                        return endpoint_config.processors
                    else:
                        return []

            # Return default processors if no specific configuration found
            return self.global_config.default_processors

    def is_enabled(self, endpoint: Optional[str] = None) -> bool:
        """Check if response enhancement is enabled.

        Args:
            endpoint: Optional endpoint to check. If None, checks global setting.

        Returns:
            True if enhancement is enabled, False otherwise
        """
        with self._config_lock:
            # Check runtime global override first
            if self._runtime_global_enabled is not None:
                if not self._runtime_global_enabled:
                    return False
            elif not self.global_config.enabled:
                return False

            if endpoint is None:
                return True

            # Check runtime endpoint override
            if endpoint in self._runtime_endpoint_overrides:
                return self._runtime_endpoint_overrides[endpoint]

            # Check endpoint-specific configuration
            for endpoint_config in self.endpoint_configs:
                if self._matches_pattern(endpoint, endpoint_config.endpoint_pattern):
                    return endpoint_config.enabled

            # Default to enabled if no specific configuration found
            return True

    def _matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if an endpoint matches a pattern.

        Simple pattern matching that supports wildcards (*).

        Args:
            endpoint: The endpoint path to check
            pattern: The pattern to match against

        Returns:
            True if endpoint matches pattern, False otherwise
        """
        if pattern == "*":
            return True

        if "*" not in pattern:
            return endpoint == pattern

        # Simple wildcard matching
        import fnmatch

        return fnmatch.fnmatch(endpoint, pattern)

    def reload(self) -> None:
        """Reload configuration from file."""
        logger.info("Reloading response enhancement configuration")
        self._load_config()

    def get_global_config(self) -> GlobalConfig:
        """Get the global configuration."""
        with self._config_lock:
            return self.global_config

    def get_endpoint_configs(self) -> list[EndpointConfig]:
        """Get all endpoint configurations."""
        with self._config_lock:
            return self.endpoint_configs.copy()

    def start_monitoring(self) -> None:
        """Start monitoring configuration file for changes."""
        if self._monitor_thread is not None and self._monitor_thread.is_alive():
            logger.warning("Configuration monitoring is already running")
            return

        self._stop_monitoring.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_config_file, name="config-monitor", daemon=True)
        self._monitor_thread.start()
        logger.info("Started configuration file monitoring for %s", self.config_path)

    def stop_monitoring(self) -> None:
        """Stop monitoring configuration file for changes."""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            return

        self._stop_monitoring.set()
        self._monitor_thread.join(timeout=5.0)
        logger.info("Stopped configuration file monitoring")

    def add_reload_callback(self, callback: Callable[[], None]) -> None:
        """Add a callback to be called when configuration is reloaded.

        Args:
            callback: Function to call when configuration changes
        """
        self._reload_callbacks.append(callback)

    def remove_reload_callback(self, callback: Callable[[], None]) -> None:
        """Remove a reload callback.

        Args:
            callback: Function to remove from callbacks
        """
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)

    def is_monitoring_active(self) -> bool:
        """Check if configuration file monitoring is active.

        Returns:
            True if monitoring thread is running, False otherwise
        """
        return self._monitor_thread is not None and self._monitor_thread.is_alive()

    def matches_pattern(self, endpoint: str, pattern: str) -> bool:
        """Check if an endpoint matches a pattern.

        Args:
            endpoint: The endpoint path to check
            pattern: The pattern to match against

        Returns:
            True if the endpoint matches the pattern, False otherwise
        """
        return self._matches_pattern(endpoint, pattern)

    def _monitor_config_file(self) -> None:
        """Monitor configuration file for changes in a background thread."""
        check_interval = 1.0  # Check every second

        while not self._stop_monitoring.is_set():
            try:
                if os.path.exists(self.config_path):
                    current_modified = os.path.getmtime(self.config_path)
                    if self._last_modified is None or current_modified > self._last_modified:
                        logger.info("Configuration file changed, reloading...")
                        self._load_config()

                self._stop_monitoring.wait(check_interval)

            except Exception:
                logger.exception("Error monitoring configuration file")
                self._stop_monitoring.wait(check_interval)

    def _notify_reload_callbacks(self) -> None:
        """Notify all registered callbacks that configuration has been reloaded."""
        for callback in self._reload_callbacks:
            try:
                callback()
            except Exception:
                logger.exception("Error calling reload callback")

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop_monitoring()

    def set_global_enabled(self, enabled: bool) -> None:
        """Set global enable/disable state at runtime.

        This override takes precedence over configuration file settings.

        Args:
            enabled: Whether to enable response enhancement globally
        """
        with self._config_lock:
            self._runtime_global_enabled = enabled
            logger.info("Set global response enhancement enabled: %s", enabled)

    def clear_global_enabled_override(self) -> None:
        """Clear the runtime global enable/disable override.

        This will revert to using the configuration file setting.
        """
        with self._config_lock:
            self._runtime_global_enabled = None
            logger.info("Cleared global response enhancement override")

    def set_endpoint_enabled(self, endpoint: str, enabled: bool) -> None:
        """Set enable/disable state for a specific endpoint at runtime.

        This override takes precedence over configuration file settings.

        Args:
            endpoint: The endpoint path to control
            enabled: Whether to enable response enhancement for this endpoint
        """
        with self._config_lock:
            self._runtime_endpoint_overrides[endpoint] = enabled
            logger.info("Set endpoint %s response enhancement enabled: %s", endpoint, enabled)

    def clear_endpoint_enabled_override(self, endpoint: str) -> None:
        """Clear the runtime enable/disable override for a specific endpoint.

        This will revert to using the configuration file setting.

        Args:
            endpoint: The endpoint path to clear override for
        """
        with self._config_lock:
            if endpoint in self._runtime_endpoint_overrides:
                del self._runtime_endpoint_overrides[endpoint]
                logger.info("Cleared endpoint %s response enhancement override", endpoint)

    def clear_all_overrides(self) -> None:
        """Clear all runtime overrides.

        This will revert all settings to use configuration file values.
        """
        with self._config_lock:
            self._runtime_global_enabled = None
            self._runtime_endpoint_overrides.clear()
            logger.info("Cleared all response enhancement runtime overrides")

    def get_runtime_overrides(self) -> dict[str, Any]:
        """Get current runtime overrides.

        Returns:
            Dictionary containing current runtime overrides
        """
        with self._config_lock:
            return {
                "global_enabled": self._runtime_global_enabled,
                "endpoint_overrides": self._runtime_endpoint_overrides.copy(),
            }

    def is_globally_enabled_by_config(self) -> bool:
        """Check if response enhancement is enabled globally by configuration file.

        This ignores runtime overrides and only checks the configuration file.

        Returns:
            True if globally enabled by config, False otherwise
        """
        with self._config_lock:
            return self.global_config.enabled

    def is_endpoint_enabled_by_config(self, endpoint: str) -> bool:
        """Check if an endpoint is enabled by configuration file.

        This ignores runtime overrides and only checks the configuration file.

        Args:
            endpoint: The endpoint path to check

        Returns:
            True if enabled by config, False otherwise
        """
        with self._config_lock:
            # Check endpoint-specific configuration
            for endpoint_config in self.endpoint_configs:
                if self._matches_pattern(endpoint, endpoint_config.endpoint_pattern):
                    return endpoint_config.enabled

            # Default to enabled if no specific configuration found
            return True

    def validate_config(self, config_data: dict[str, Any]) -> None:
        """Validate configuration data against schema.

        Args:
            config_data: Configuration data to validate

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            validate(instance=config_data, schema=CONFIG_SCHEMA)
        except ValidationError as e:
            logger.exception("Configuration validation failed: %s", e.message)
            logger.exception("Invalid configuration at path: %s", " -> ".join(str(p) for p in e.absolute_path))
            raise ValueError(f"Invalid configuration: {e.message}") from e

    def _apply_environment_overrides(self) -> None:
        """Apply environment variable overrides to configuration."""
        # Global configuration overrides
        if os.getenv("RESPONSE_ENHANCEMENT_ENABLED") is not None:
            self.global_config.enabled = os.getenv("RESPONSE_ENHANCEMENT_ENABLED", "true").lower() == "true"

        if os.getenv("RESPONSE_ENHANCEMENT_FAIL_SILENTLY") is not None:
            self.global_config.fail_silently = os.getenv("RESPONSE_ENHANCEMENT_FAIL_SILENTLY", "true").lower() == "true"

        if os.getenv("RESPONSE_ENHANCEMENT_LOG_LEVEL") is not None:
            log_level = os.getenv("RESPONSE_ENHANCEMENT_LOG_LEVEL", "INFO").upper()
            if log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
                self.global_config.log_level = log_level

        if os.getenv("RESPONSE_ENHANCEMENT_DEFAULT_PROCESSORS") is not None:
            processors_str = os.getenv("RESPONSE_ENHANCEMENT_DEFAULT_PROCESSORS", "")
            self.global_config.default_processors = [p.strip() for p in processors_str.split(",") if p.strip()]


# Global configuration instance
_config_instance: Optional[EnhancementConfig] = None
_config_lock = threading.Lock()


def get_config(config_path: Optional[str] = None, enable_hot_reload: bool = True) -> EnhancementConfig:
    """Get the global configuration instance.

    Args:
        config_path: Path to configuration file (only used on first call)
        enable_hot_reload: Whether to enable hot reload (only used on first call)

    Returns:
        Global configuration instance
    """
    global _config_instance

    with _config_lock:
        if _config_instance is None:
            _config_instance = EnhancementConfig(config_path=config_path, enable_hot_reload=enable_hot_reload)
        return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance (mainly for testing)."""
    global _config_instance

    with _config_lock:
        if _config_instance is not None:
            _config_instance.stop_monitoring()
            _config_instance = None
