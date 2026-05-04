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

# File categories for MCP server projects
MCP_FILE_CATEGORIES = {
    "generators": {
        "description": "Code generator templates (Jinja2)",
        "patterns": [
            ".fips-agents-cli/generators/**/*",
        ],
        "ask_before_patch": False,  # Safe to overwrite
    },
    "core": {
        "description": "Core infrastructure (server, auth, etc)",
        "patterns": [
            "src/core/server.py",
            "src/core/auth.py",
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

# Files to NEVER patch in MCP server projects (user code)
MCP_NEVER_PATCH = [
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

# File categories for agent and workflow projects (same template repo,
# same directory layout — both ship with chart/, docs/, build files,
# and .claude/commands/, none of which match the MCP layout)
AGENT_FILE_CATEGORIES = {
    "chart": {
        "description": "Helm chart templates",
        "patterns": [
            "chart/templates/**/*",
            "chart/Chart.yaml",
        ],
        "ask_before_patch": True,  # User may have customized
    },
    "docs": {
        "description": "Documentation files",
        "patterns": [
            "CLAUDE.md",
            "AGENTS.md",
            "docs/**/*",
        ],
        "ask_before_patch": False,  # Usually safe to update
    },
    "build": {
        "description": "Build and deployment files",
        "patterns": [
            "Makefile",
            "Containerfile",
            "deploy.sh",
            "redeploy.sh",
        ],
        "ask_before_patch": True,  # May be customized
    },
    "claude": {
        "description": "Claude Code slash commands shipped with the template",
        "patterns": [
            ".claude/commands/**/*",
        ],
        "ask_before_patch": False,  # Safe to overwrite
    },
}

# Files to NEVER patch in agent / workflow projects (user code)
AGENT_NEVER_PATCH = [
    "src/agent.py",  # User's agent implementation
    "agent.yaml",  # User's agent config
    "chart/values.yaml",  # User's deploy values
    "src/fipsagents/**",  # Vendored — managed by `fips-agents vendor --update`
    "tests/**/*.py",
    ".env*",
    "README.md",
    "pyproject.toml",  # User may have added dependencies
]


def get_categories_for_type(project_type: str) -> tuple[dict, list[str]]:
    """
    Return the (categories, never_patch) tuple for a given project type.

    Args:
        project_type: One of 'mcp-server', 'agent', 'workflow'. Other types
            (gateway, ui, sandbox) are not patchable yet and raise ValueError.

    Returns:
        tuple: (file_categories_dict, never_patch_list)

    Raises:
        ValueError: If the project type does not support patching.
    """
    if project_type == "mcp-server":
        return MCP_FILE_CATEGORIES, MCP_NEVER_PATCH
    if project_type in ("agent", "workflow"):
        return AGENT_FILE_CATEGORIES, AGENT_NEVER_PATCH
    raise ValueError(
        f"Patching is not supported for project type '{project_type}'. "
        "Supported types: mcp-server, agent, workflow."
    )


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


def get_project_type(template_info: dict[str, Any]) -> str:
    """
    Read the project type from template-info, defaulting to 'mcp-server'.

    Projects scaffolded before .template-info gained the `template.type`
    field (v0.8.x and earlier) are all MCP servers — that was the only
    patchable type at the time.
    """
    return template_info.get("template", {}).get("type", "mcp-server")


def get_available_categories(project_type: str = "mcp-server") -> list[str]:
    """Get list of available patch categories for a given project type."""
    categories, _ = get_categories_for_type(project_type)
    return list(categories.keys())


def _clone_template_for_patch(template_info: dict[str, Any], temp_path: Path) -> Path:
    """
    Clone the template repo and return the comparison root.

    For standalone repos (mcp-server, gateway, ui, sandbox), the comparison
    root is the clone root itself. For monorepo subdirs (agent, workflow),
    it's `temp_path / subdir`.

    Args:
        template_info: Template metadata read from .template-info
        temp_path: Pre-created temp directory the caller manages

    Returns:
        Path: The directory whose layout mirrors the project — use this
        as the root for glob/compare operations, not `temp_path`.

    Raises:
        FileNotFoundError: If `template.subdir` is set but does not exist
            in the cloned repo.
    """
    template_block = template_info["template"]
    template_url = template_block["url"]
    subdir = template_block.get("subdir")

    clone_template(template_url, temp_path)

    if not subdir:
        return temp_path

    template_root = temp_path / subdir
    if not template_root.is_dir():
        raise FileNotFoundError(
            f"Template subdir '{subdir}' not found in cloned repo {template_url}"
        )
    return template_root


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
    project_type = get_project_type(template_info)
    file_categories, _ = get_categories_for_type(project_type)

    console.print(f"[cyan]Fetching latest template from {template_url}...[/cyan]")

    # Clone latest template to temp directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        template_root = _clone_template_for_patch(template_info, temp_path)

        updates = {}

        for category, config in file_categories.items():
            changed_files = []

            for pattern in config["patterns"]:
                # Find matching files in template
                for template_file in template_root.glob(pattern):
                    if template_file.is_file():
                        # Get relative path
                        rel_path = template_file.relative_to(template_root)
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
    project_type = get_project_type(template_info)
    file_categories, never_patch = get_categories_for_type(project_type)

    if category not in file_categories:
        available = ", ".join(file_categories.keys()) or "(none)"
        return (
            False,
            f"Category '{category}' is not valid for {project_type} projects. "
            f"Available: {available}",
        )

    config = file_categories[category]
    template_url = template_info["template"]["url"]

    console.print(f"\n[bold cyan]Patching Category: {category}[/bold cyan]")
    console.print(f"[dim]{config['description']}[/dim]\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        console.print(f"[cyan]Fetching template from {template_url}...[/cyan]")
        template_root = _clone_template_for_patch(template_info, temp_path)
        console.print("[green]✓[/green] Template fetched\n")

        files_patched = 0
        files_skipped = 0

        for pattern in config["patterns"]:
            for template_file in template_root.glob(pattern):
                if not template_file.is_file():
                    continue

                rel_path = template_file.relative_to(template_root)
                project_file = project_path / rel_path

                # Check if file should be patched
                if _should_never_patch(rel_path, never_patch):
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


def _should_never_patch(file_path: Path, never_patch: list[str]) -> bool:
    """Check if a file should never be patched, given the rule list."""
    file_str = str(file_path)
    for pattern in never_patch:
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
