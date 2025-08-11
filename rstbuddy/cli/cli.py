from __future__ import annotations

import json
import os
import sys
from importlib.metadata import Distribution
from unittest.mock import Mock

import click
from rich.table import Table

import rstbuddy

from ..settings import Settings
from .utils import console, print_error, print_info, print_success


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output except errors")
@click.option(
    "--config-file", type=click.Path(exists=True), help="Custom configuration file path"
)
@click.option(
    "--output",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format",
)
@click.pass_context
def cli(
    ctx: click.Context, verbose: bool, quiet: bool, config_file: str | None, output: str
):
    """
    rstbuddy command line interface.
    """  # noqa: D403
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["output"] = output
    ctx.obj["config_file"] = config_file

    if config_file:
        # This will be picked up by the Settings class's
        # settings_customize_sources method
        os.environ["RSTBUDDY_CONFIG_FILE"] = config_file

    # Load settings
    try:
        settings = Settings()
        ctx.obj["settings"] = settings
    except Exception as e:  # noqa: BLE001
        print_error(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Add console to context for commands to use
    ctx.obj["console"] = console

    # Add utils object to context for commands that need utility functions
    ctx.obj["utils"] = type(
        "Utils",
        (),
        {
            "print_info": print_info,
            "print_error": print_error,
            "print_success": print_success,
            "print_header": lambda msg: print_info(f"=== {msg} ==="),
            "print_warning": lambda msg: print_info(f"Warning: {msg}"),
            "show_progress": lambda desc: type(
                "Progress",
                (),
                {
                    "__enter__": lambda self: self,
                    "__exit__": lambda self, *args: None,
                    "add_task": lambda self, desc, total: Mock(),
                },
            )(),
        },
    )()

    # Configure console based on quiet mode
    if quiet:
        console.quiet = True


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

    table.add_row("rstbuddy", str(rstbuddy.__version__))
    table.add_row("click", str(click.__version__))
    table.add_row("rich", str(Distribution.from_name("rich").version))

    output_console.print(table)


@cli.command("settings")
@click.pass_context
def show_settings(ctx: click.Context):
    """
    Settings-related commands.
    """
    output_format = ctx.obj.get("output", "table")
    verbose = ctx.obj.get("verbose", False)
    output_console = ctx.obj.get("console", console)

    # Use settings from context if available, otherwise create new instance
    settings = ctx.obj.get("settings")
    if not settings:
        # Create a fresh Settings instance to avoid test state crossover
        # If a config file was specified, use it
        config_file = ctx.obj.get("config_file")

        if config_file:
            os.environ["RSTBUDDY_CONFIG_FILE"] = config_file
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

    if verbose:
        print_info(f"Found {len(settings.model_dump())} settings")
