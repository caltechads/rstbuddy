"""
Settings management for rstbuddy.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from .exc import ConfigurationError


class Settings(BaseSettings):
    """
    Application settings with cascading TOML config file support,
    and support for environment variables.

    Configuration precedence:

    1. CLI arguments
    2. Environment variables
    3. Local config file (``./rstbuddy.toml``)
    4. Your config file (``~/.rstbuddy.toml``)
    4. Global config file (``/etc//.rstbuddy.toml/``)
    5. Defaults

    Note:
        The app_name and app_version fields are readonly (frozen=True) and
        cannot be overridden via configuration files or environment variables.
        Other fields remain configurable as normal.

    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="RSTBUDDY_",
    )

    # Application settings (readonly - cannot be overridden via configuration)
    app_name: str = Field(
        default="rstbuddy",
        description="Application name",
        frozen=True,
    )
    app_version: str = Field(
        default="0.3.1", description="Application version", frozen=True
    )

    # Write-able settings
    documentation_dir: str = Field(
        default="doc/source",
        description="Top-level directory for RST files to be processed",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(
        default="", description="OpenAI API key for summary generation"
    )

    # RST Cleaning Settings
    clean_rst_extra_protected_regexes: list[str] = Field(
        default_factory=list,
        description=(
            "List of regex patterns; if a line matches any, the "
            "rstbuddy will not modify that line"
        ),
    )

    # RST Link Checking Settings
    check_rst_links_skip_domains: list[str] = Field(
        default_factory=list,
        description=(
            "List of domain substrings to skip during external link "
            "validation for check-links"
        ),
    )
    check_rst_links_extra_skip_directives: list[str] = Field(
        default_factory=list,
        description=(
            "Additional directive names whose content should be "
            "ignored when scanning links (e.g., custom code-like directives)"
        ),
    )

    # Output settings
    default_output_format: Literal["table", "json", "text"] = Field(
        default="table", description="Default output format"
    )
    enable_colors: bool = Field(default=True, description="Enable colored output")
    quiet_mode: bool = Field(default=False, description="Enable quiet mode")

    # Logging settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    log_file: str | None = Field(default=None, description="Log file path")

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Load settings from file with cascading configuration.

        Args:
            settings_cls: The settings class to load
            init_settings: Settings from initialization
            env_settings: Settings from environment variables
            dotenv_settings: Settings from .env file
            file_secret_settings: Settings from file secrets

        Returns:
            Loaded settings instance

        """
        # Define configuration file paths in order of precedence
        config_paths = []

        # Global configuration
        if os.name == "nt":  # Windows
            global_config = (
                Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "rstbuddy.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/rstbuddy.toml")

        if global_config.exists():
            config_paths.append(global_config)

        # User home configuration
        user_config = Path.home() / ".rstbuddy.toml"
        if user_config.exists():
            config_paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".rstbuddy.toml"
        if local_config.exists():
            config_paths.append(local_config)

        config_file = os.environ.get("RSTBUDDY_CONFIG_FILE")
        # Explicit configuration file (highest precedence)
        if config_file:
            explicit_config = Path(config_file)
            if explicit_config.exists():
                config_paths.append(explicit_config)

        # Load settings with file configuration
        if config_paths:
            # Use the last (highest precedence) config file
            config_file_path = config_paths[-1]
            return (TomlConfigSettingsSource(settings_cls, config_file_path.resolve()),)

        # Fall back to environment variables and defaults
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

    def get_config_paths(self) -> list[Path]:
        """
        Get list of configuration file paths that were loaded.
        Use this for debugging.

        Returns:
            List of configuration file paths

        """
        paths = []

        # Global configuration
        if os.name == "nt":  # Windows
            global_config = (
                Path(os.environ.get("PROGRAMDATA", "C:/ProgramData")) / "rstbuddy.toml"
            )
        else:  # Unix-like
            global_config = Path("/etc/rstbuddy.toml")

        if global_config.exists():
            paths.append(global_config)

        # User home configuration
        user_config = Path.home() / ".rstbuddy.toml"
        if user_config.exists():
            paths.append(user_config)

        # Local configuration
        local_config = Path.cwd() / ".rstbuddy.toml"
        if local_config.exists():
            paths.append(local_config)

        return paths

    def validate_settings(self) -> None:
        """
        Validate settings and ensure required directories exist.

        Raises:
            ConfigurationError: If settings are invalid

        """
        # Validate output format
        if self.default_output_format not in ["table", "json", "text"]:
            msg = f"Invalid output format: {self.default_output_format}"
            raise ConfigurationError(msg)

        # Ensure output directories exist
        if not Path(self.documentation_dir).exists():
            msg = f"Documentation dir '{self.documentation_dir}' does not exist"
            raise ConfigurationError(msg)
