from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
stderr_console = Console(file=sys.stderr)


def create_progress() -> Progress:
    """
    Create a rich progress indicator for long-running operations.

    Returns:
        Configured progress indicator

    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=stderr_console,
    )


def print_error(message: str, suggestions: list[str] | None = None):
    """
    Print error message with optional suggestions.

    Args:
        message: Error message
        suggestions: List of suggestions to fix the error

    """
    error_panel = Panel(
        f"[red]{message}[/red]", title="[bold red]Error[/bold red]", border_style="red"
    )
    stderr_console.print(error_panel)

    if suggestions:
        stderr_console.print("\n[bold]Suggestions:[/bold]")
        for suggestion in suggestions:
            stderr_console.print(f"  • {suggestion}")


def print_success(message: str):
    """
    Print success message.

    Args:
        message: Success message

    """
    success_panel = Panel(
        f"[green]{message}[/green]",
        title="[bold green]Success[/bold green]",
        border_style="green",
    )
    stderr_console.print(success_panel)


def print_info(message: str):
    """
    Print informational message.

    Args:
        message: Informational message

    """
    info_panel = Panel(
        f"[blue]{message}[/blue]",
        title="[bold blue]Info[/bold blue]",
        border_style="blue",
    )
    stderr_console.print(info_panel)
