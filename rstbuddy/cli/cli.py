from __future__ import annotations  # noqa: I001

import json
import os
import subprocess
import sys
from pathlib import Path

import click
from rich.table import Table

from ..settings import Settings
from .utils import console, create_progress, print_error, print_info, print_success


def print_header(msg: str) -> None:
    """Print header message."""
    console.print(f"[bold cyan]=== {msg} ===[/bold cyan]")


def print_warning(msg: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]⚠[/yellow] Warning: {msg}")


def get_package_version(package_name: str) -> str:
    """Get package version safely."""
    try:
        import importlib.metadata

        return importlib.metadata.version(package_name)
    except ImportError:
        try:
            import pkg_resources

            return pkg_resources.get_distribution(package_name).version
        except Exception:
            return "unknown"


@click.group()
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress output (useful for scripts)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Enable verbose output",
)
@click.option(
    "--output",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format for commands that support it",
)
@click.option(
    "--config-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def cli(
    ctx: click.Context,
    quiet: bool,
    verbose: bool,
    output: str,
    config_file: Path | None,
) -> None:
    """
    RSTBuddy - A tool for working with RST documentation.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Load configuration
    try:
        if config_file:
            os.environ["RSTBUDDY_CONFIG_FILE"] = str(config_file)
        settings = Settings()
        ctx.obj["settings"] = settings
    except Exception as e:
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Add console to context for commands to use
    ctx.obj["console"] = console

    # Add utils object to context for commands that need utility functions
    class Utils:
        def __init__(self):
            self.print_info = print_info
            self.print_error = print_error
            self.print_success = print_success
            self.print_header = print_header
            self.print_warning = print_warning
            self.show_progress = create_progress

    ctx.obj["utils"] = Utils()

    # Configure console based on quiet mode
    if quiet:
        console.quiet = True

    # Store global options in context for commands to use
    ctx.obj["verbose"] = verbose
    ctx.obj["output_format"] = output


@cli.command(name="version", help="Print some version info.")
@click.pass_context
def version(ctx: click.Context) -> None:
    """
    Print the some version info of this package,
    """
    # Use context console if available, fallback to global console
    output_console = ctx.obj.get("console", console)

    table = Table(title="rstbuddy Version Info")
    table.add_column("Package", justify="left", style="cyan", no_wrap=True)
    table.add_column("Version", justify="left", style="yellow", no_wrap=True)

    table.add_row("rstbuddy", get_package_version("rstbuddy"))
    table.add_row("python", str(sys.version))
    table.add_row("click", get_package_version("click"))
    table.add_row("rich", get_package_version("rich"))
    table.add_row("openai", get_package_version("openai"))
    table.add_row("mdformat", get_package_version("mdformat"))

    # Get pandoc version
    try:
        pandoc_version = (
            subprocess.check_output(["pandoc", "--version"])
            .decode("utf-8")
            .split("\n")[0]
            .split(" ")[1]
        )
        table.add_row("pandoc", pandoc_version)
    except subprocess.CalledProcessError:
        table.add_row("pandoc", "not found")

    output_console.print(table)


@cli.command("settings")
@click.option(
    "--output",
    type=click.Choice(["json", "table", "text"]),
    help="Output format (overrides global --output option)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output (overrides global --verbose option)",
)
@click.pass_context
def show_settings(ctx: click.Context, output: str | None, verbose: bool):
    """
    Settings-related commands.
    """
    output_console = ctx.obj.get("console", console)

    # Use local options if provided, otherwise fall back to global options
    output_format = (
        output if output is not None else ctx.obj.get("output_format", "table")
    )
    is_verbose = verbose or ctx.obj.get("verbose", False)

    # Use settings from context if available, otherwise create new instance
    settings = ctx.obj.get("settings")
    if not settings:
        # Create a fresh Settings instance to avoid test state crossover
        # If a config file was specified, use it
        config_file = ctx.obj.get("config_file")

        if config_file:
            os.environ["RSTBUDDY_CONFIG_FILE"] = str(config_file)
        settings = Settings()

    if output_format == "json":
        click.echo(json.dumps(settings.model_dump()))
    elif output_format == "table":
        table = Table(title="Settings", show_header=True, header_style="bold magenta")
        table.add_column("Setting Name", style="cyan")
        table.add_column("Value", style="green")

        for setting_name, setting_value in settings.model_dump().items():
            table.add_row(setting_name, str(setting_value))

        output_console.print(table)
    else:  # text format
        for setting_name, setting_value in settings.model_dump().items():
            click.echo(f"{setting_name}: {setting_value}")
            click.echo()

    if is_verbose:
        print_info(f"Found {len(settings.model_dump())} settings")
