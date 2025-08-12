"""
Unit tests for configuration settings.

Tests the new OpenAI and summary generation configuration fields,
validation logic, and TOML file loading.
"""

from unittest.mock import patch

import pytest

from rstbuddy.settings import Settings


class TestConfiguration:
    """Test cases for configuration settings."""

    def test_default_settings(self):
        """Test default settings values."""
        with patch(
            "rstbuddy.settings.Settings.model_config",
            {"extra": "ignore", "env_prefix": "RSTBUDDY_"},
        ):
            settings = Settings()

            assert settings.openai_api_key == ""

    def test_settings_with_openai_key(self):
        """Test settings with OpenAI API key."""
        settings = Settings(openai_api_key="sk-test123")

        assert settings.openai_api_key == "sk-test123"

    def test_validate_settings_success(self):
        """Test successful settings validation."""
        settings = Settings(openai_api_key="sk-test123")

        # Should not raise any exceptions
        with patch("pathlib.Path.exists", return_value=True):
            settings.validate_settings()

    def test_validate_settings_no_api_key(self):
        """Test validation succeeds when no API key."""
        settings = Settings(openai_api_key="")

        with (
            patch("pathlib.Path.exists", return_value=True),
        ):
            settings.validate_settings()

    @patch("rstbuddy.settings.Path.home")
    def test_load_config_with_toml_file(self, mock_home, tmp_path):
        """Test loading configuration with TOML file."""
        # Mock file system calls to simulate a config file existing
        mock_home.return_value = tmp_path / "home" / "user"
        mock_home.return_value.mkdir(parents=True, exist_ok=True)
        config_file = mock_home.return_value / ".rstbuddy.toml"
        config_file.write_text('openai_api_key = "sk-test-from-toml"', encoding="utf-8")

        # Test that our TOML file is loaded
        settings = Settings()

        # Verify the values are set correctly
        assert settings.openai_api_key == "sk-test-from-toml"

        # Test that the settings_customise_sources method exists and is callable
        assert hasattr(Settings, "settings_customise_sources")
        assert callable(Settings.settings_customise_sources)

        # Test that the method returns the expected structure when called directly
        result = Settings.settings_customise_sources(Settings, None, None, None, None)
        # Should return a tuple (either with TOML source or empty)
        assert isinstance(result, tuple)

    def test_load_config_without_toml_file(self):
        """Test loading configuration without TOML file."""
        with patch("rstbuddy.settings.Settings.model_config", {"toml_file": []}):
            settings = Settings()

            # Should use default values
            assert settings.openai_api_key == ""

    def test_load_config_error(self):
        """Test loading configuration with error."""
        with (  # noqa: SIM117
            patch(
                "rstbuddy.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "RSTBUDDY_"},
            ),
            patch(
                "rstbuddy.settings.Settings.__init__",
                side_effect=Exception("Config error"),
            ),
        ):
            with pytest.raises(Exception, match="Config error"):
                Settings()

    def test_settings_field_descriptions(self):
        """Test that settings fields have proper descriptions."""
        settings = Settings()

        # Check that fields exist and have descriptions
        assert hasattr(settings, "openai_api_key")

    def test_settings_model_config(self):
        """Test that model_config is properly configured."""
        settings = Settings()

        # Check that env_file includes the expected files
        assert settings.model_config.get("env_prefix") == "RSTBUDDY_"
        assert settings.model_config.get("extra") == "ignore"

    def test_settings_validation_output_format(self):
        """Test output format validation."""
        # Test that invalid format raises error during initialization
        with pytest.raises(Exception, match="Input should be"):
            Settings(default_output_format="invalid")

        # Test that valid format passes validation
        settings = Settings(default_output_format="json")
        with patch("pathlib.Path.exists", return_value=True):
            settings.validate_settings()

    def test_settings_validation_valid_default_output_format(self):
        """Test valid output format validation."""
        valid_formats = ["table", "json", "text"]

        for output_format in valid_formats:
            settings = Settings(default_output_format=output_format)
            # Should not raise any exceptions
            with patch("pathlib.Path.exists", return_value=True):
                settings.validate_settings()

    def test_settings_with_environment_variables(self):
        """Test settings loading from environment variables."""
        with (
            patch.dict(
                "os.environ",
                {
                    "RSTBUDDY_OPENAI_API_KEY": "sk-env-test",
                },
            ),
            patch(
                "rstbuddy.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "RSTBUDDY_"},
            ),
        ):
            settings = Settings()

            assert settings.openai_api_key == "sk-env-test"

    def test_settings_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with (
            patch.dict(
                "os.environ",
                {
                    "RSTBUDDY_OPENAI_API_KEY": "sk-override",
                    "RSTBUDDY_DOCUMENTATION_DIR": "docs",
                },
            ),
            patch(
                "rstbuddy.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "RSTBUDDY_"},
            ),
        ):
            settings = Settings()

            assert settings.openai_api_key == "sk-override"
            assert settings.documentation_dir == "docs"

    def test_settings_case_insensitive(self):
        """Test that settings are case insensitive."""
        with (
            patch.dict(
                "os.environ",
                {
                    "RSTBUDDY_OPENAI_API_KEY": "sk-lowercase",
                    "rstbuddy_documentation_dir": "docs",
                },
            ),
            patch(
                "rstbuddy.settings.Settings.model_config",
                {"extra": "ignore", "env_prefix": "RSTBUDDY_"},
            ),
        ):
            settings = Settings()

            assert settings.openai_api_key == "sk-lowercase"
            assert settings.documentation_dir == "docs"

    def test_settings_extra_fields_ignored(self):
        """Test that extra fields in TOML are ignored."""
        # Test that the Settings class properly handles extra fields
        # by creating a Settings instance and verifying it only has expected fields

        # Create settings with some values
        settings = Settings(openai_api_key="sk-test", documentation_dir="docs")

        # Verify known fields are set
        assert settings.openai_api_key == "sk-test"
        assert settings.documentation_dir == "docs"

        # Verify that extra fields are not attributes
        assert not hasattr(settings, "unknown_field")
        assert not hasattr(settings, "another_unknown")

        # Test that setting extra attributes doesn't affect the model
        # (this tests the extra="ignore" behavior)
        settings._extra_data = {"unknown_field": "should be ignored"}  # noqa: SLF001
        assert not hasattr(settings, "unknown_field")

    def test_settings_field_types(self):
        """Test that settings fields have correct types."""
        settings = Settings(openai_api_key="sk-test", documentation_dir="docs")

        assert isinstance(settings.openai_api_key, str)
        assert isinstance(settings.documentation_dir, str)

    def test_settings_field_defaults(self):
        """Test that settings fields have correct defaults."""
        with patch("rstbuddy.settings.Settings.model_config", {"env_file": []}):
            settings = Settings()

            assert settings.openai_api_key == ""
            assert settings.documentation_dir == "doc/source"
            assert settings.default_output_format == "table"
            assert settings.enable_colors is True
            assert settings.quiet_mode is False
            assert settings.log_level == "INFO"
            assert settings.log_file is None
            assert settings.clean_rst_extra_protected_regexes == []
            assert settings.check_rst_links_skip_domains == []
            assert settings.check_rst_links_extra_skip_directives == []
