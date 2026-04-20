"""Project customization and configuration utilities."""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import tomlkit
from rich.console import Console

from fips_agents_cli.version import __version__

console = Console()


def validate_project_name(name: str) -> tuple[bool, str | None]:
    """
    Validate project name according to Python package naming conventions.

    Project names must:
    - Start with a lowercase letter
    - Contain only lowercase letters, numbers, hyphens, and underscores
    - Not be empty

    Args:
        name: The project name to validate

    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if valid, False otherwise
               error_message is None if valid, otherwise contains the error description
    """
    if not name:
        return False, "Project name cannot be empty"

    if not re.match(r"^[a-z][a-z0-9\-_]*$", name):
        return False, (
            "Project name must start with a lowercase letter and contain only "
            "lowercase letters, numbers, hyphens, and underscores"
        )

    return True, None


def to_module_name(project_name: str) -> str:
    """
    Convert a project name to a valid Python module name.

    Replaces hyphens with underscores to ensure compatibility with Python imports.

    Args:
        project_name: The project name (may contain hyphens)

    Returns:
        str: A valid Python module name (hyphens replaced with underscores)
    """
    return project_name.replace("-", "_")


def update_project_name(project_path: Path, new_name: str) -> None:
    """
    Update the project name in pyproject.toml and rename the source directory.

    This function:
    1. Updates the 'name' field in pyproject.toml
    2. Updates the entry point script name if present
    3. Renames the source directory from the template name to the new module name

    Args:
        project_path: Path to the project root directory
        new_name: The new project name (with hyphens allowed)

    Raises:
        FileNotFoundError: If pyproject.toml or source directory doesn't exist
        ValueError: If pyproject.toml is malformed
    """
    try:
        console.print(f"[cyan]Customizing project for '{new_name}'...[/cyan]")

        pyproject_path = project_path / "pyproject.toml"

        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        # Read and parse pyproject.toml
        with open(pyproject_path) as f:
            pyproject = tomlkit.parse(f.read())

        # Get the old project name from pyproject.toml
        old_name = pyproject.get("project", {}).get("name", "fastmcp-unified-template")
        old_module_name = to_module_name(old_name)
        new_module_name = to_module_name(new_name)

        # Update project name
        if "project" in pyproject:
            pyproject["project"]["name"] = new_name

            # Update entry point script name if it exists
            if "scripts" in pyproject["project"]:
                # Find and update any entry points that reference the old name
                scripts = pyproject["project"]["scripts"]
                old_scripts = dict(scripts)

                for script_name, script_path in old_scripts.items():
                    # Replace old module name with new module name in the path
                    # (but only if it's actually in the path - new template uses src.main:main)
                    new_script_path = script_path.replace(old_module_name, new_module_name)

                    # Update the script name to match the new project name
                    if script_name == old_name or script_name == old_module_name:
                        del scripts[script_name]
                        scripts[new_name] = new_script_path
                    else:
                        # Keep the same script name but update the path if needed
                        scripts[script_name] = new_script_path

        # Write updated pyproject.toml
        with open(pyproject_path, "w") as f:
            f.write(tomlkit.dumps(pyproject))

        console.print("[green]✓[/green] Updated pyproject.toml")

        # Rename source directory (for templates with single-module structure)
        src_dir = project_path / "src"
        old_src_path = src_dir / old_module_name
        new_src_path = src_dir / new_module_name

        if old_src_path.exists() and old_src_path != new_src_path:
            shutil.move(str(old_src_path), str(new_src_path))
            console.print(f"[green]✓[/green] Renamed source directory to '{new_module_name}'")
        elif not old_src_path.exists():
            # Template uses multi-module structure (core/, tools/, etc.)
            console.print(
                "[dim]Note: Template uses multi-module structure, no directory rename needed[/dim]"
            )

        console.print("[green]✓[/green] Project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize project: {e}")
        raise


def _replace_in_file(path: Path, old: str, new: str) -> None:
    """Replace all occurrences of a string in a file, if the file exists."""
    if path.exists():
        text = path.read_text()
        path.write_text(text.replace(old, new))


def customize_agent_project(
    project_path: Path,
    new_name: str,
    github_repo: str | None = None,
) -> None:
    """
    Customize an agent project with the new project name.

    Replaces 'agent-template' with the new project name across configuration
    files, Helm templates, and deploy scripts. Unlike MCP server projects,
    agent projects don't rename source directories (base_agent is a framework
    component, not the project module).

    Args:
        project_path: Path to the project root directory
        new_name: The new project name (with hyphens allowed)
        github_repo: GitHub repo in "owner/name" format for Containerfile label

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    try:
        console.print(f"[cyan]Customizing agent project for '{new_name}'...[/cyan]")

        # 1. Update pyproject.toml name field (use tomlkit to preserve formatting)
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        with open(pyproject_path) as f:
            pyproject = tomlkit.parse(f.read())

        if "project" in pyproject:
            pyproject["project"]["name"] = new_name

        with open(pyproject_path, "w") as f:
            f.write(tomlkit.dumps(pyproject))

        console.print("[green]✓[/green] Updated pyproject.toml")

        # 2. String-replace "agent-template" in supporting files and Helm templates
        files_to_update = [
            project_path / "chart" / "Chart.yaml",
            project_path / "chart" / "values.yaml",
            project_path / "chart" / "templates" / "_helpers.tpl",
            project_path / "chart" / "templates" / "deployment.yaml",
            project_path / "chart" / "templates" / "service.yaml",
            project_path / "chart" / "templates" / "configmap.yaml",
            project_path / "chart" / "templates" / "route.yaml",
            project_path / "chart" / "templates" / "NOTES.txt",
            project_path / "AGENTS.md",
            project_path / "Containerfile",
            project_path / "Makefile",
            project_path / "deploy.sh",
        ]

        for file_path in files_to_update:
            _replace_in_file(file_path, "agent-template", new_name)

        console.print("[green]✓[/green] Updated configuration files")

        # 3. Replace OWNER/REPO placeholder in Containerfile image source label
        repo_value = github_repo if github_repo else f"OWNER/{new_name}"
        _replace_in_file(project_path / "Containerfile", "OWNER/REPO", repo_value)

        console.print("[green]✓[/green] Agent project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize agent project: {e}")
        raise


def customize_workflow_project(
    project_path: Path,
    new_name: str,
    github_repo: str | None = None,
) -> None:
    """
    Customize a workflow project with the new project name.

    Replaces 'workflow-template' with the new project name across configuration
    files, Helm templates, and deploy scripts. Also removes the monorepo-specific
    base-agent install line from the Makefile since cloned projects get fipsagents
    from PyPI.

    Args:
        project_path: Path to the project root directory
        new_name: The new project name (with hyphens allowed)
        github_repo: GitHub repo in "owner/name" format for Containerfile label

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    try:
        console.print(f"[cyan]Customizing workflow project for '{new_name}'...[/cyan]")

        # 1. Update pyproject.toml name field (use tomlkit to preserve formatting)
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        with open(pyproject_path) as f:
            pyproject = tomlkit.parse(f.read())

        if "project" in pyproject:
            pyproject["project"]["name"] = new_name

        with open(pyproject_path, "w") as f:
            f.write(tomlkit.dumps(pyproject))

        console.print("[green]✓[/green] Updated pyproject.toml")

        # 2. String-replace "workflow-template" in supporting files and Helm templates
        files_to_update = [
            project_path / "chart" / "Chart.yaml",
            project_path / "chart" / "values.yaml",
            project_path / "chart" / "templates" / "_helpers.tpl",
            project_path / "chart" / "templates" / "deployment.yaml",
            project_path / "chart" / "templates" / "service.yaml",
            project_path / "chart" / "templates" / "configmap.yaml",
            project_path / "chart" / "templates" / "route.yaml",
            project_path / "chart" / "templates" / "NOTES.txt",
            project_path / "AGENTS.md",
            project_path / "Containerfile",
            project_path / "Makefile",
            project_path / "deploy.sh",
        ]

        for file_path in files_to_update:
            _replace_in_file(file_path, "workflow-template", new_name)

        console.print("[green]✓[/green] Updated configuration files")

        # 3. Remove monorepo-specific base-agent install line from Makefile
        # Cloned projects get fipsagents from PyPI, not a local path
        makefile_path = project_path / "Makefile"
        if makefile_path.exists():
            text = makefile_path.read_text()
            # Remove the monorepo install line and its comments
            lines = text.splitlines(keepends=True)
            filtered = []
            skip_block = False
            for line in lines:
                if "In the monorepo" in line:
                    skip_block = True
                    continue
                if skip_block and ("fips-agents" in line or "scaffolding step" in line):
                    continue
                if skip_block and ("$(PIP) install -e" in line and "packages/" in line):
                    skip_block = False
                    continue
                skip_block = False
                filtered.append(line)
            makefile_path.write_text("".join(filtered))

        console.print("[green]✓[/green] Cleaned up Makefile for standalone use")

        # 4. Replace OWNER/REPO placeholder in Containerfile image source label
        repo_value = github_repo if github_repo else f"OWNER/{new_name}"
        _replace_in_file(project_path / "Containerfile", "OWNER/REPO", repo_value)

        console.print("[green]✓[/green] Workflow project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize workflow project: {e}")
        raise


def customize_sandbox_project(
    project_path: Path,
    new_name: str,
    github_repo: str | None = None,
) -> None:
    """
    Customize a sandbox project with the new project name.

    Replaces 'code-sandbox' with the new project name across configuration
    files, Helm templates, and build files. The Python package directory
    (sandbox/) is NOT renamed -- it stays as 'sandbox' regardless of
    project name.

    Args:
        project_path: Path to the project root directory
        new_name: The new project name (with hyphens allowed)
        github_repo: GitHub repo in "owner/name" format for Containerfile label

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
    """
    try:
        console.print(f"[cyan]Customizing sandbox project for '{new_name}'...[/cyan]")

        # 1. Update pyproject.toml name field (use tomlkit to preserve formatting)
        pyproject_path = project_path / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

        with open(pyproject_path) as f:
            pyproject = tomlkit.parse(f.read())

        if "project" in pyproject:
            pyproject["project"]["name"] = new_name

        with open(pyproject_path, "w") as f:
            f.write(tomlkit.dumps(pyproject))

        console.print("[green]✓[/green] Updated pyproject.toml")

        # 2. String-replace "code-sandbox" in supporting files and Helm templates
        files_to_update = [
            project_path / "chart" / "Chart.yaml",
            project_path / "chart" / "values.yaml",
            project_path / "Makefile",
            project_path / "README.md",
            project_path / "CLAUDE.md",
            project_path / "Containerfile",
        ]

        # Also update all files in chart/templates/
        chart_templates_dir = project_path / "chart" / "templates"
        if chart_templates_dir.exists():
            for template_file in chart_templates_dir.iterdir():
                if template_file.is_file():
                    files_to_update.append(template_file)

        for file_path in files_to_update:
            _replace_in_file(file_path, "code-sandbox", new_name)

        console.print("[green]✓[/green] Updated configuration files")

        # 3. Replace OWNER/REPO placeholder in Containerfile image source label
        if github_repo:
            _replace_in_file(project_path / "Containerfile", "OWNER/REPO", github_repo)

        console.print("[green]✓[/green] Sandbox project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize sandbox project: {e}")
        raise


def customize_go_project(project_path: Path, new_name: str, sentinel: str) -> None:
    """
    Customize a Go-based template project with the new project name.

    Replaces the sentinel string with the new project name across configuration
    and build files. Unlike Python projects, Go projects don't have pyproject.toml
    or source directory renaming -- customization is purely string replacement.

    Args:
        project_path: Path to the project root directory
        new_name: The new project name (with hyphens allowed)
        sentinel: The template's placeholder string to replace (e.g. "gateway-template")
    """
    try:
        console.print(f"[cyan]Customizing Go project for '{new_name}'...[/cyan]")

        # go.mod is required -- fail if missing
        go_mod = project_path / "go.mod"
        if not go_mod.exists():
            raise FileNotFoundError(f"go.mod not found at {go_mod}")

        _replace_in_file(go_mod, sentinel, new_name)
        console.print("[green]✓[/green] Updated go.mod")

        # Configuration and build files (optional -- tolerate missing)
        optional_files = [
            project_path / "chart" / "Chart.yaml",
            project_path / "chart" / "values.yaml",
            project_path / "chart" / "templates" / "_helpers.tpl",
            project_path / "Containerfile",
            project_path / "Makefile",
            project_path / "README.md",
            project_path / "CLAUDE.md",
        ]

        for file_path in optional_files:
            _replace_in_file(file_path, sentinel, new_name)

        # Check HTML files in static/ for sentinels (e.g. <title> tags in UI templates)
        static_dir = project_path / "static"
        if static_dir.exists():
            for html_file in static_dir.glob("*.html"):
                _replace_in_file(html_file, sentinel, new_name)

        console.print("[green]✓[/green] Updated configuration files")
        console.print("[green]✓[/green] Go project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize Go project: {e}")
        raise


def cleanup_template_files(project_path: Path) -> None:
    """
    Remove template-specific files that shouldn't be in the new project.

    Args:
        project_path: Path to the project root directory
    """
    # Files to remove (commonly found in templates)
    files_to_remove = [
        ".github/workflows/template-cleanup.yml",  # Template-specific workflows
    ]

    for file_path in files_to_remove:
        full_path = project_path / file_path
        if full_path.exists():
            try:
                full_path.unlink()
                console.print(f"[green]✓[/green] Removed template file: {file_path}")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Could not remove {file_path}: {e}")


def write_template_info(
    project_path: Path,
    project_name: str,
    template_url: str,
    template_commit: str,
    github_repo: str | None = None,
    github_url: str | None = None,
) -> None:
    """
    Write template generation metadata to .template-info file.

    Args:
        project_path: Path to the project root directory
        project_name: Name of the generated project
        template_url: URL of the template repository
        template_commit: Git commit hash of the template
        github_repo: GitHub repository in "owner/name" format (optional)
        github_url: Full URL to the GitHub repository (optional)
    """
    try:
        template_info = {
            "generator": {"tool": "fips-agents-cli", "version": __version__},
            "template": {
                "url": template_url,
                "commit": template_commit[:12],  # Short hash
                "full_commit": template_commit,
            },
            "project": {
                "name": project_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        }

        # Add GitHub metadata if provided
        if github_repo or github_url:
            template_info["github"] = {}
            if github_repo:
                template_info["github"]["repo"] = github_repo
            if github_url:
                template_info["github"]["url"] = github_url

        info_file = project_path / ".template-info"
        with open(info_file, "w") as f:
            json.dump(template_info, f, indent=2)
            f.write("\n")  # Add trailing newline

        console.print("[green]✓[/green] Created template metadata file")

    except Exception as e:
        # Don't fail the entire operation if this fails
        console.print(f"[yellow]⚠[/yellow] Could not write template info: {e}")
