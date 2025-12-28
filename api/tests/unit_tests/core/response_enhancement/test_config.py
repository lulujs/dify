"""Tests for configuration management."""

from unittest.mock import mock_open, patch

from core.response_enhancement.config import EndpointConfig, EnhancementConfig, GlobalConfig


class TestGlobalConfig:
    """Test the GlobalConfig dataclass."""

    def test_global_config_defaults(self):
        """Test GlobalConfig default values."""
        config = GlobalConfig()

        assert config.enabled is True
        assert config.default_processors == []
        assert config.fail_silently is True
        assert config.log_level == "INFO"

    def test_global_config_custom_values(self):
        """Test GlobalConfig with custom values."""
        config = GlobalConfig(
            enabled=False, default_processors=["metadata", "timing"], fail_silently=False, log_level="DEBUG"
        )

        assert config.enabled is False
        assert config.default_processors == ["metadata", "timing"]
        assert config.fail_silently is False
        assert config.log_level == "DEBUG"


class TestEndpointConfig:
    """Test the EndpointConfig dataclass."""

    def test_endpoint_config_required_fields(self):
        """Test EndpointConfig with required fields."""
        config = EndpointConfig(endpoint_pattern="/test-endpoint", processors=["metadata"])

        assert config.endpoint_pattern == "/test-endpoint"
        assert config.processors == ["metadata"]
        assert config.enabled is True
        assert config.conditions is None

    def test_endpoint_config_all_fields(self):
        """Test EndpointConfig with all fields."""
        conditions = {"response_type": "json"}
        config = EndpointConfig(
            endpoint_pattern="/test-endpoint", processors=["metadata", "timing"], enabled=False, conditions=conditions
        )

        assert config.endpoint_pattern == "/test-endpoint"
        assert config.processors == ["metadata", "timing"]
        assert config.enabled is False
        assert config.conditions == conditions


class TestEnhancementConfig:
    """Test the EnhancementConfig class."""

    def test_config_initialization_no_file(self):
        """Test config initialization when no config file exists."""
        with patch("os.path.exists", return_value=False):
            config = EnhancementConfig("/nonexistent/path.yaml")

            # Should use default values
            assert config.global_config.enabled is True
            assert config.global_config.default_processors == []
            assert config.endpoint_configs == []

    def test_config_initialization_with_file(self):
        """Test config initialization with valid config file."""
        config_content = """
global:
  enabled: true
  default_processors: ["metadata"]
  fail_silently: false
  log_level: "DEBUG"

endpoints:
  - pattern: "/completion-messages"
    processors: ["metadata", "timing"]
    enabled: true
  - pattern: "/chat-messages"
    processors: ["metadata"]
    enabled: false
    conditions:
      response_type: "json"
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        # Check global config
        assert config.global_config.enabled is True
        assert config.global_config.default_processors == ["metadata"]
        assert config.global_config.fail_silently is False
        assert config.global_config.log_level == "DEBUG"

        # Check endpoint configs
        assert len(config.endpoint_configs) == 2

        completion_config = config.endpoint_configs[0]
        assert completion_config.endpoint_pattern == "/completion-messages"
        assert completion_config.processors == ["metadata", "timing"]
        assert completion_config.enabled is True

        chat_config = config.endpoint_configs[1]
        assert chat_config.endpoint_pattern == "/chat-messages"
        assert chat_config.processors == ["metadata"]
        assert chat_config.enabled is False
        assert chat_config.conditions == {"response_type": "json"}

    def test_config_loading_error(self):
        """Test config loading with invalid YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=invalid_yaml)):
                config = EnhancementConfig("/test/config.yaml")

        # Should fall back to defaults on error
        assert config.global_config.enabled is True
        assert config.global_config.default_processors == []
        assert config.endpoint_configs == []

    def test_get_processors_for_endpoint_exact_match(self):
        """Test getting processors for exact endpoint match."""
        config_content = """
endpoints:
  - pattern: "/completion-messages"
    processors: ["metadata", "timing"]
    enabled: true
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        processors = config.get_processors_for_endpoint("/completion-messages")
        assert processors == ["metadata", "timing"]

    def test_get_processors_for_endpoint_wildcard_match(self):
        """Test getting processors for wildcard endpoint match."""
        config_content = """
endpoints:
  - pattern: "/api/*"
    processors: ["metadata"]
    enabled: true
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        processors = config.get_processors_for_endpoint("/api/test")
        assert processors == ["metadata"]

    def test_get_processors_for_endpoint_disabled(self):
        """Test getting processors for disabled endpoint."""
        config_content = """
endpoints:
  - pattern: "/disabled-endpoint"
    processors: ["metadata"]
    enabled: false
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        processors = config.get_processors_for_endpoint("/disabled-endpoint")
        assert processors == []

    def test_get_processors_for_endpoint_default(self):
        """Test getting default processors when no endpoint match."""
        config_content = """
global:
  default_processors: ["default_processor"]
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        processors = config.get_processors_for_endpoint("/unknown-endpoint")
        assert processors == ["default_processor"]

    def test_is_enabled_global(self):
        """Test global enable/disable check."""
        config_content = """
global:
  enabled: false
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        assert config.is_enabled() is False
        assert config.is_enabled("/any-endpoint") is False

    def test_is_enabled_endpoint_specific(self):
        """Test endpoint-specific enable/disable check."""
        config_content = """
global:
  enabled: true
endpoints:
  - pattern: "/disabled-endpoint"
    processors: ["metadata"]
    enabled: false
  - pattern: "/enabled-endpoint"
    processors: ["metadata"]
    enabled: true
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        assert config.is_enabled("/disabled-endpoint") is False
        assert config.is_enabled("/enabled-endpoint") is True
        assert config.is_enabled("/unknown-endpoint") is True  # Default to enabled

    def test_pattern_matching(self):
        """Test pattern matching functionality."""
        config = EnhancementConfig()

        # Exact match
        assert config._matches_pattern("/test", "/test") is True
        assert config._matches_pattern("/test", "/other") is False

        # Wildcard match
        assert config._matches_pattern("/api/test", "/api/*") is True
        assert config._matches_pattern("/api/test/sub", "/api/*") is True
        assert config._matches_pattern("/other/test", "/api/*") is False

        # Global wildcard
        assert config._matches_pattern("/anything", "*") is True

    def test_reload_config(self):
        """Test configuration reloading."""
        initial_config = """
global:
  enabled: true
  default_processors: ["initial"]
"""

        updated_config = """
global:
  enabled: false
  default_processors: ["updated"]
"""

        with patch("os.path.exists", return_value=True):
            # Initial load
            with patch("builtins.open", mock_open(read_data=initial_config)):
                config = EnhancementConfig("/test/config.yaml")

            assert config.global_config.enabled is True
            assert config.global_config.default_processors == ["initial"]

            # Reload with updated content
            with patch("builtins.open", mock_open(read_data=updated_config)):
                config.reload()

            assert config.global_config.enabled is False
            assert config.global_config.default_processors == ["updated"]

    def test_get_global_config(self):
        """Test getting global configuration."""
        config = EnhancementConfig()
        global_config = config.get_global_config()

        assert isinstance(global_config, GlobalConfig)
        assert global_config is config.global_config

    def test_get_endpoint_configs(self):
        """Test getting endpoint configurations."""
        config_content = """
endpoints:
  - pattern: "/test1"
    processors: ["proc1"]
  - pattern: "/test2"
    processors: ["proc2"]
"""

        with patch("os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=config_content)):
                config = EnhancementConfig("/test/config.yaml")

        endpoint_configs = config.get_endpoint_configs()

        assert len(endpoint_configs) == 2
        assert endpoint_configs[0].endpoint_pattern == "/test1"
        assert endpoint_configs[1].endpoint_pattern == "/test2"

        # Should return a copy, not the original list
        assert endpoint_configs is not config.endpoint_configs
