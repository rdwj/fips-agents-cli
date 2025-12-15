"""Patch command for updating projects from template changes."""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from fips_agents_cli.tools.patching import (
    check_for_updates,
    get_available_categories,
    get_template_info,
    patch_category,
)
from fips_agents_cli.tools.validation import find_project_root

console = Console()


@click.group()
def patch():
    """Update project files from template repository changes."""
    pass


@patch.command("check")
def check():
    """
    Check for available updates from the template repository.

    Shows what files have changed in the template since project creation.
    """
    console.print("\n[bold cyan]Checking for Template Updates[/bold cyan]\n")

    # Find project root
    project_root = find_project_root()
    if not project_root:
        console.print(
            "[red]✗[/red] Not in a project directory\n"
            "[yellow]Hint:[/yellow] Run this command from within a project created by fips-agents"
        )
        sys.exit(1)

    # Get template info
    template_info = get_template_info(project_root)
    if not template_info:
        console.print(
            "[red]✗[/red] No template metadata found\n"
            "[yellow]Hint:[/yellow] This project may not have been created by fips-agents-cli"
        )
        sys.exit(1)

    console.print("[green]✓[/green] Project created from template")
    console.print(f"  Template: {template_info['template']['url']}")
    console.print(f"  Template commit: {template_info['template']['commit']}")
    console.print(f"  Created: {template_info['project']['created_at']}\n")

    # Check for updates
    updates = check_for_updates(project_root, template_info)

    if not updates:
        console.print("[green]✓[/green] Project is up to date with latest template!")
        sys.exit(0)

    # Display available updates by category
    table = Table(title="Available Updates")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Files Changed", style="yellow")
    table.add_column("Description", style="dim")

    for category, info in updates.items():
        table.add_row(category, str(len(info["files"])), info["description"])

    console.print(table)
    console.print("\n[dim]Run [cyan]fips-agents patch <category>[/cyan] to apply updates[/dim]")


@patch.command("generators")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def generators(dry_run: bool):
    """
    Update code generator templates from the latest template repository.

    This includes Jinja2 templates in .fips-agents-cli/generators/
    """
    _patch_category("generators", dry_run)


@patch.command("core")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def core(dry_run: bool):
    """
    Update core infrastructure files (loaders, server bootstrap, etc).

    Shows diffs and asks for confirmation before applying changes.
    """
    _patch_category("core", dry_run)


@patch.command("docs")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def docs(dry_run: bool):
    """
    Update documentation files and examples.
    """
    _patch_category("docs", dry_run)


@patch.command("build")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
def build(dry_run: bool):
    """
    Update build and deployment files (Makefile, Containerfile, etc).

    Shows diffs and asks for confirmation before applying changes.
    """
    _patch_category("build", dry_run)


@patch.command("all")
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be updated without making changes",
)
@click.option(
    "--skip-confirmation",
    is_flag=True,
    help="Skip confirmation prompts (use with caution)",
)
def all_categories(dry_run: bool, skip_confirmation: bool):
    """
    Update all patchable files from the template repository.

    This will interactively show diffs for files that may be customized.
    """
    console.print("\n[bold cyan]Patching All Categories[/bold cyan]\n")

    if not skip_confirmation:
        confirm = click.confirm("This will update multiple files. Continue?", default=True)
        if not confirm:
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)

    categories = get_available_categories()
    for category in categories:
        console.print(f"\n[bold]Processing category: {category}[/bold]")
        _patch_category(category, dry_run, skip_confirmation=skip_confirmation)


def _patch_category(category: str, dry_run: bool, skip_confirmation: bool = False):
    """
    Internal helper to patch a specific category.

    Args:
        category: Category name (generators, core, docs, etc.)
        dry_run: If True, only show what would be changed
        skip_confirmation: If True, don't ask for confirmation
    """
    # Find project root
    project_root = find_project_root()
    if not project_root:
        console.print(
            "[red]✗[/red] Not in a project directory\n"
            "[yellow]Hint:[/yellow] Run this command from within a project created by fips-agents"
        )
        sys.exit(1)

    # Get template info
    template_info = get_template_info(project_root)
    if not template_info:
        console.print(
            "[red]✗[/red] No template metadata found\n"
            "[yellow]Hint:[/yellow] This project may not have been created by fips-agents-cli"
        )
        sys.exit(1)

    # Perform patch
    success, message = patch_category(
        project_root, template_info, category, dry_run, skip_confirmation
    )

    if success:
        if dry_run:
            console.print(f"\n[cyan]Dry run completed for '{category}'[/cyan]")
        else:
            console.print(Panel(message, border_style="green", padding=(1, 2)))
    else:
        console.print(f"\n[red]✗[/red] {message}")
        sys.exit(1)
