"""Validation utilities for MCP component generation."""

import keyword
import re
from pathlib import Path

import tomlkit
from rich.console import Console

console = Console()


def find_project_root() -> Path | None:
    """
    Find the project root by walking up from current directory.

    Looks for pyproject.toml with fastmcp dependency to identify MCP server projects.

    Returns:
        Path: Project root path if found
        None: If no valid MCP project root is found

    Example:
        >>> root = find_project_root()
        >>> if root:
        ...     print(f"Found project at {root}")
    """
    current_path = Path.cwd()

    # Walk up the directory tree
    for parent in [current_path] + list(current_path.parents):
        pyproject_path = parent / "pyproject.toml"

        if pyproject_path.exists():
            try:
                with open(pyproject_path) as f:
                    pyproject = tomlkit.parse(f.read())

                # Check if this is an MCP server project
                dependencies = pyproject.get("project", {}).get("dependencies", [])

                # Check for fastmcp dependency
                for dep in dependencies:
                    if isinstance(dep, str) and "fastmcp" in dep.lower():
                        return parent

            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Could not parse {pyproject_path}: {e}")
                continue

    return None


def is_valid_component_name(name: str) -> tuple[bool, str]:
    """
    Validate component name as a valid Python identifier.

    Component names must:
    - Be valid Python identifiers (snake_case)
    - Not be Python keywords
    - Not be empty
    - Start with a letter or underscore
    - Contain only letters, numbers, and underscores

    Args:
        name: The component name to validate

    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if valid, False otherwise
               error_message is empty string if valid, otherwise contains error description

    Examples:
        >>> is_valid_component_name("my_tool")
        (True, '')
        >>> is_valid_component_name("123invalid")
        (False, 'Component name must start with a letter or underscore')
    """
    if not name:
        return False, "Component name cannot be empty"

    # Check if it's a valid Python identifier
    if not name.isidentifier():
        if name[0].isdigit():
            return False, "Component name must start with a letter or underscore"
        return False, (
            "Component name must be a valid Python identifier (use snake_case: "
            "letters, numbers, underscores only)"
        )

    # Check if it's a Python keyword
    if keyword.iskeyword(name):
        return False, f"Component name '{name}' is a Python keyword and cannot be used"

    # Recommend snake_case
    if not re.match(r"^[a-z_][a-z0-9_]*$", name):
        return False, (
            "Component name should use snake_case (lowercase letters, numbers, " "underscores only)"
        )

    return True, ""


def component_exists(project_root: Path, component_type: str, name: str) -> bool:
    """
    Check if a component file already exists.

    Args:
        project_root: Path to the project root directory
        component_type: Type of component ('tool', 'resource', 'prompt', 'middleware')
        name: Component name (will check for {name}.py)

    Returns:
        bool: True if component file exists, False otherwise

    Example:
        >>> root = Path("/path/to/project")
        >>> component_exists(root, "tool", "my_tool")
        False
    """
    # Map component types to their directory locations
    component_dirs = {
        "tool": "tools",
        "resource": "resources",
        "prompt": "prompts",
        "middleware": "middleware",
    }

    if component_type not in component_dirs:
        return False

    component_dir = component_dirs[component_type]
    component_file = project_root / "src" / component_dir / f"{name}.py"

    return component_file.exists()


def validate_generator_templates(project_root: Path, component_type: str) -> tuple[bool, str]:
    """
    Validate that generator templates exist for the component type.

    Args:
        project_root: Path to the project root directory
        component_type: Type of component ('tool', 'resource', 'prompt', 'middleware')

    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if templates exist, False otherwise
               error_message is empty string if valid, otherwise contains error description

    Example:
        >>> root = Path("/path/to/project")
        >>> is_valid, msg = validate_generator_templates(root, "tool")
        >>> if is_valid:
        ...     print("Templates found!")
    """
    generators_dir = project_root / ".fips-agents-cli" / "generators" / component_type

    if not generators_dir.exists():
        return False, (
            f"Generator templates not found for '{component_type}'\n"
            f"Expected: {generators_dir}\n"
            "Was this project created with fips-agents create mcp-server?"
        )

    # Check for required template files
    component_template = generators_dir / "component.py.j2"
    test_template = generators_dir / "test.py.j2"

    missing_files = []
    if not component_template.exists():
        missing_files.append("component.py.j2")
    if not test_template.exists():
        missing_files.append("test.py.j2")

    if missing_files:
        return False, (
            f"Missing template files for '{component_type}':\n"
            f"  {', '.join(missing_files)}\n"
            f"Expected location: {generators_dir}"
        )

    return True, ""
