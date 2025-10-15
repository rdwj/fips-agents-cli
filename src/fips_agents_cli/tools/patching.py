"""Utilities for patching projects with template updates."""

import difflib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.syntax import Syntax

from fips_agents_cli.tools.git import clone_template

console = Console()

# File categories for patching
FILE_CATEGORIES = {
    "generators": {
        "description": "Code generator templates (Jinja2)",
        "patterns": [
            ".fips-agents-cli/generators/**/*",
        ],
        "ask_before_patch": False,  # Safe to overwrite
    },
    "core": {
        "description": "Core infrastructure (loaders, server, etc)",
        "patterns": [
            "src/core/loaders.py",
            "src/core/server.py",
            "src/*/__ init__.py",  # Package __init__ files
            "conftest.py",
        ],
        "ask_before_patch": True,  # May be customized
    },
    "docs": {
        "description": "Documentation and examples",
        "patterns": [
            "docs/**/*",
            "*/examples/**/*",  # Examples in any directory
            "CLAUDE.md",
            "ARCHITECTURE.md",
            "TESTING.md",
        ],
        "ask_before_patch": False,  # Usually safe to update
    },
    "build": {
        "description": "Build and deployment files",
        "patterns": [
            "Makefile",
            "Containerfile",
            "openshift.yaml",
            "deploy.sh",
            "remove_examples.sh",
        ],
        "ask_before_patch": True,  # May be customized
    },
}

# Files to NEVER patch (user code)
NEVER_PATCH = [
    "src/tools/*.py",
    "src/resources/*.py",
    "src/prompts/*.py",
    "src/middleware/*.py",
    "tests/**/*.py",
    ".env*",
    "README.md",
    "pyproject.toml",  # User may have added dependencies
    "src/core/app.py",  # User settings
    "src/core/auth.py",  # Custom auth
    "src/core/logging.py",  # Custom logging
]


def get_template_info(project_path: Path) -> dict[str, Any] | None:
    """
    Read template metadata from .template-info file.

    Args:
        project_path: Path to the project root

    Returns:
        dict: Template metadata or None if not found
    """
    info_file = project_path / ".template-info"
    if not info_file.exists():
        return None

    try:
        with open(info_file) as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Failed to read template info: {e}")
        return None


def get_available_categories() -> list[str]:
    """Get list of available patch categories."""
    return list(FILE_CATEGORIES.keys())


def check_for_updates(project_path: Path, template_info: dict[str, Any]) -> dict[str, Any]:
    """
    Check what files have changed in template since project creation.

    Args:
        project_path: Path to the project root
        template_info: Template metadata from .template-info

    Returns:
        dict: Dictionary of categories with changed files
    """
    template_url = template_info["template"]["url"]
    # original_commit = template_info["template"]["full_commit"]  # For future use

    console.print(f"[cyan]Fetching latest template from {template_url}...[/cyan]")

    # Clone latest template to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        clone_template(template_url, temp_path)

        # Get latest commit
        # (For now, we'll just compare files - can enhance to get actual latest commit)

        updates = {}

        for category, config in FILE_CATEGORIES.items():
            changed_files = []

            for pattern in config["patterns"]:
                # Find matching files in template
                for template_file in temp_path.glob(pattern):
                    if template_file.is_file():
                        # Get relative path
                        rel_path = template_file.relative_to(temp_path)
                        project_file = project_path / rel_path

                        # Check if file exists and is different
                        if not project_file.exists():
                            changed_files.append(str(rel_path))
                        elif not _files_identical(template_file, project_file):
                            changed_files.append(str(rel_path))

            if changed_files:
                updates[category] = {
                    "description": config["description"],
                    "files": changed_files,
                    "ask_before_patch": config["ask_before_patch"],
                }

        return updates


def patch_category(
    project_path: Path,
    template_info: dict[str, Any],
    category: str,
    dry_run: bool = False,
    skip_confirmation: bool = False,
) -> tuple[bool, str]:
    """
    Patch files for a specific category.

    Args:
        project_path: Path to the project root
        template_info: Template metadata
        category: Category to patch
        dry_run: If True, only show what would change
        skip_confirmation: If True, don't ask for approval

    Returns:
        tuple: (success, message)
    """
    if category not in FILE_CATEGORIES:
        return False, f"Unknown category: {category}"

    config = FILE_CATEGORIES[category]
    template_url = template_info["template"]["url"]

    console.print(f"\n[bold cyan]Patching Category: {category}[/bold cyan]")
    console.print(f"[dim]{config['description']}[/dim]\n")

    # Clone template
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        console.print(f"[cyan]Fetching template from {template_url}...[/cyan]")
        clone_template(template_url, temp_path)
        console.print("[green]✓[/green] Template fetched\n")

        files_patched = 0
        files_skipped = 0

        for pattern in config["patterns"]:
            for template_file in temp_path.glob(pattern):
                if not template_file.is_file():
                    continue

                rel_path = template_file.relative_to(temp_path)
                project_file = project_path / rel_path

                # Check if file should be patched
                if _should_never_patch(rel_path):
                    console.print(f"[dim]Skipping (user code): {rel_path}[/dim]")
                    files_skipped += 1
                    continue

                # Check if file is different
                if project_file.exists() and _files_identical(template_file, project_file):
                    continue  # No changes

                # Show diff and ask for approval if needed
                if config["ask_before_patch"] and not skip_confirmation:
                    if not _show_diff_and_ask(template_file, project_file, rel_path, dry_run):
                        console.print(f"[yellow]Skipped: {rel_path}[/yellow]")
                        files_skipped += 1
                        continue

                # Patch the file
                if not dry_run:
                    project_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(template_file, project_file)
                    console.print(f"[green]✓[/green] Patched: {rel_path}")
                else:
                    console.print(f"[cyan]Would patch: {rel_path}[/cyan]")

                files_patched += 1

        summary = f"""
[bold green]✓ Patch Complete![/bold green]

[bold cyan]Category:[/bold cyan] {category}
[bold cyan]Files patched:[/bold cyan] {files_patched}
[bold cyan]Files skipped:[/bold cyan] {files_skipped}

{'[yellow]Dry run - no changes were made[/yellow]' if dry_run else '[green]Changes have been applied to your project[/green]'}
"""

        return True, summary


def _files_identical(file1: Path, file2: Path) -> bool:
    """Check if two files have identical content."""
    try:
        return file1.read_bytes() == file2.read_bytes()
    except Exception:
        return False


def _should_never_patch(file_path: Path) -> bool:
    """Check if a file should never be patched."""
    file_str = str(file_path)
    for pattern in NEVER_PATCH:
        if Path(file_str).match(pattern):
            return True
    return False


def _show_diff_and_ask(
    template_file: Path, project_file: Path, rel_path: Path, dry_run: bool
) -> bool:
    """
    Show diff between template and project file, ask user if they want to apply.

    Args:
        template_file: Path to template file
        project_file: Path to project file
        rel_path: Relative path for display
        dry_run: If True, don't actually ask (just show diff)

    Returns:
        bool: True if user wants to apply the patch
    """
    console.print(f"\n[bold yellow]File may be customized: {rel_path}[/bold yellow]")

    # Read file contents
    if project_file.exists():
        project_lines = project_file.read_text().splitlines(keepends=True)
        template_lines = template_file.read_text().splitlines(keepends=True)

        # Generate diff
        diff = difflib.unified_diff(
            project_lines,
            template_lines,
            fromfile=f"current/{rel_path}",
            tofile=f"template/{rel_path}",
            lineterm="",
        )

        diff_text = "\n".join(diff)

        if diff_text:
            console.print("\n[bold]Diff:[/bold]")
            syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
            console.print(syntax)
    else:
        console.print("[yellow]⚠[/yellow] File does not exist in project (new file)")
        # Show the new file content (first 20 lines)
        template_content = template_file.read_text()
        lines = template_content.split("\n")[:20]
        preview = "\n".join(lines)
        if len(template_content.split("\n")) > 20:
            preview += "\n... (truncated)"

        syntax = Syntax(preview, "python", theme="monokai", line_numbers=True)
        console.print(syntax)

    if dry_run:
        return True  # In dry run, pretend user said yes

    return click.confirm(f"\nApply this change to {rel_path}?", default=False)
