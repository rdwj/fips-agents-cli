"""Project customization and configuration utilities."""

import re
import shutil
from pathlib import Path

import tomlkit
from rich.console import Console

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
        old_name = pyproject.get("project", {}).get("name", "mcp-server-template")
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
                    new_script_path = script_path.replace(old_module_name, new_module_name)

                    # If the script name was based on the old project name, update it
                    if script_name == old_name or script_name == old_module_name:
                        del scripts[script_name]
                        scripts[new_name] = new_script_path
                    else:
                        scripts[script_name] = new_script_path

        # Write updated pyproject.toml
        with open(pyproject_path, "w") as f:
            f.write(tomlkit.dumps(pyproject))

        console.print("[green]✓[/green] Updated pyproject.toml")

        # Rename source directory
        src_dir = project_path / "src"
        old_src_path = src_dir / old_module_name
        new_src_path = src_dir / new_module_name

        if old_src_path.exists() and old_src_path != new_src_path:
            shutil.move(str(old_src_path), str(new_src_path))
            console.print(f"[green]✓[/green] Renamed source directory to '{new_module_name}'")
        elif not old_src_path.exists():
            # Template might have a different structure, log a warning
            console.print(
                f"[yellow]⚠[/yellow] Source directory 'src/{old_module_name}' not found, "
                "skipping rename"
            )

        console.print("[green]✓[/green] Project customization complete")

    except FileNotFoundError as e:
        console.print(f"[red]✗[/red] {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to customize project: {e}")
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
