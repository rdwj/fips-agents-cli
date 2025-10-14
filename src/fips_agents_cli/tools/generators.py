"""Generator utilities for rendering MCP component templates."""

import ast
import json
import subprocess
from pathlib import Path
from typing import Any

import jinja2
import tomlkit
from rich.console import Console

console = Console()


def get_project_info(project_root: Path) -> dict[str, Any]:
    """
    Extract project metadata from pyproject.toml.

    Args:
        project_root: Path to the project root directory

    Returns:
        dict: Project metadata including:
            - name: Project name
            - module_name: Module name (with underscores)
            - version: Project version

    Raises:
        FileNotFoundError: If pyproject.toml doesn't exist
        ValueError: If pyproject.toml is malformed

    Example:
        >>> info = get_project_info(Path("/path/to/project"))
        >>> print(info["name"])
        'my-mcp-server'
    """
    pyproject_path = project_root / "pyproject.toml"

    if not pyproject_path.exists():
        raise FileNotFoundError(f"pyproject.toml not found at {pyproject_path}")

    try:
        with open(pyproject_path) as f:
            pyproject = tomlkit.parse(f.read())

        project_name = pyproject.get("project", {}).get("name", "unknown")
        project_version = pyproject.get("project", {}).get("version", "0.1.0")
        module_name = project_name.replace("-", "_")

        return {
            "name": project_name,
            "module_name": module_name,
            "version": project_version,
        }

    except Exception as e:
        raise ValueError(f"Failed to parse pyproject.toml: {e}") from e


def load_template(project_root: Path, component_type: str, template_name: str) -> jinja2.Template:
    """
    Load a Jinja2 template from the project's generator templates.

    Args:
        project_root: Path to the project root directory
        component_type: Type of component ('tool', 'resource', 'prompt', 'middleware')
        template_name: Name of the template file (e.g., 'component.py.j2')

    Returns:
        jinja2.Template: Loaded Jinja2 template

    Raises:
        FileNotFoundError: If template file doesn't exist
        jinja2.TemplateError: If template is malformed

    Example:
        >>> template = load_template(root, "tool", "component.py.j2")
        >>> rendered = template.render(component_name="my_tool")
    """
    template_path = (
        project_root / ".fips-agents-cli" / "generators" / component_type / template_name
    )

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    try:
        with open(template_path) as f:
            template_content = f.read()

        # Create a Jinja2 environment with the template directory as the loader path
        template_dir = template_path.parent
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        return env.from_string(template_content)

    except jinja2.TemplateError as e:
        raise jinja2.TemplateError(f"Failed to load template {template_name}: {e}") from e


def validate_type_annotation(type_str: str) -> tuple[bool, str]:
    """
    Validate that a type annotation is properly formatted for FastMCP.

    Args:
        type_str: Type annotation string (e.g., "dict[str, str]")

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_type_annotation("dict")  # Invalid
        (False, "Bare 'dict' type not allowed. Use dict[str, str] or dict[str, Any]")

        >>> validate_type_annotation("dict[str, str]")  # Valid
        (True, "")
    """
    # Check for bare dict/list without parameters
    if type_str in ["dict", "list"]:
        return (
            False,
            f"Bare '{type_str}' type not allowed. "
            f"Use {type_str}[...] with type parameters for FastMCP 2.9.0+ compatibility",
        )

    # Validate dict types have parameters
    if type_str.startswith("dict[") or type_str.startswith("dict |"):
        if not ("[" in type_str and "]" in type_str):
            return False, "Dict types must include type parameters: dict[key_type, value_type]"

    return True, ""


def compute_type_hint(param: dict[str, Any]) -> str:
    """
    Compute the full type hint for a parameter, handling optional types.

    Args:
        param: Parameter definition dictionary

    Returns:
        Complete type hint string (e.g., "str", "dict[str, str]", "str | None")

    Examples:
        >>> compute_type_hint({"type": "str", "optional": False})
        "str"

        >>> compute_type_hint({"type": "dict[str, str]", "optional": True})
        "dict[str, str] | None"
    """
    base_type = param["type"]
    is_optional = param.get("optional", False) or param.get("required", True) is False

    if is_optional and " | None" not in base_type:
        return f"{base_type} | None"

    return base_type


def load_params_file(params_path: Path) -> list[dict[str, Any]]:
    """
    Load and validate parameter definitions from a JSON file.

    Expected schema:
    [
      {
        "name": "query",
        "type": "str",
        "description": "Search query",
        "required": true,
        "min_length": 1,
        "max_length": 100
      }
    ]

    Args:
        params_path: Path to the JSON parameter file

    Returns:
        list: List of parameter definition dictionaries

    Raises:
        FileNotFoundError: If params file doesn't exist
        ValueError: If JSON is invalid or schema is incorrect

    Example:
        >>> params = load_params_file(Path("params.json"))
        >>> print(params[0]["name"])
        'query'
    """
    if not params_path.exists():
        raise FileNotFoundError(f"Parameters file not found: {params_path}")

    try:
        with open(params_path) as f:
            params = json.load(f)

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in parameters file: {e}") from e

    # Validate schema
    if not isinstance(params, list):
        raise ValueError("Parameters file must contain a JSON array of parameter definitions")

    for i, param in enumerate(params):
        if not isinstance(param, dict):
            raise ValueError(f"Parameter {i} must be a JSON object")

        # Check required fields
        required_fields = ["name", "type", "description"]
        for field in required_fields:
            if field not in param:
                raise ValueError(f"Parameter {i} missing required field: {field}")

        # Validate name is a valid Python identifier
        if not param["name"].isidentifier():
            raise ValueError(f"Parameter {i} has invalid name: {param['name']}")

        # Validate type
        valid_types = [
            # Simple types
            "str",
            "int",
            "float",
            "bool",
            # List types (parameterized)
            "list[str]",
            "list[int]",
            "list[float]",
            "list[bool]",
            # Dict types (parameterized - REQUIRED for FastMCP 2.9.0+)
            "dict[str, str]",
            "dict[str, Any]",
            "dict[str, int]",
            "dict[str, float]",
            "dict[str, bool]",
            # Optional simple types
            "str | None",
            "int | None",
            "float | None",
            "bool | None",
            # Optional complex types
            "list[str] | None",
            "list[int] | None",
            "dict[str, str] | None",
            "dict[str, Any] | None",
        ]
        if param["type"] not in valid_types:
            raise ValueError(
                f"Parameter {i} has invalid type: {param['type']}. "
                f"Valid types: {', '.join(valid_types)}"
            )

        # Validate type formatting for FastMCP compliance
        is_valid, error_msg = validate_type_annotation(param["type"])
        if not is_valid:
            raise ValueError(f"Parameter {i} '{param['name']}': {error_msg}")

    return params


def render_component(template: jinja2.Template, variables: dict[str, Any]) -> str:
    """
    Render a Jinja2 template with the provided variables.

    Args:
        template: Jinja2 template object
        variables: Dictionary of template variables

    Returns:
        str: Rendered template as a string

    Raises:
        jinja2.TemplateError: If rendering fails

    Example:
        >>> template = load_template(root, "tool", "component.py.j2")
        >>> code = render_component(template, {"component_name": "my_tool"})
    """
    try:
        return template.render(**variables)
    except jinja2.TemplateError as e:
        raise jinja2.TemplateError(f"Failed to render template: {e}") from e


def validate_python_syntax(code: str) -> tuple[bool, str]:
    """
    Validate Python code syntax using ast.parse().

    Args:
        code: Python code as a string

    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if syntax is valid, False otherwise
               error_message is empty string if valid, otherwise contains error description

    Example:
        >>> code = "def my_func():\\n    return 42"
        >>> is_valid, msg = validate_python_syntax(code)
        >>> print(is_valid)
        True
    """
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Failed to validate syntax: {e}"


def write_component_file(content: str, file_path: Path) -> None:
    """
    Write component content to a file, creating parent directories if needed.

    Args:
        content: File content as a string
        file_path: Path where the file should be written

    Raises:
        OSError: If file cannot be written (permissions, etc.)

    Example:
        >>> write_component_file("print('hello')", Path("src/tools/my_tool.py"))
    """
    try:
        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(file_path, "w") as f:
            f.write(content)

    except OSError as e:
        raise OSError(f"Failed to write file {file_path}: {e}") from e


def run_component_tests(project_root: Path, test_file: Path) -> tuple[bool, str]:
    """
    Run pytest on a generated test file and capture output.

    Args:
        project_root: Path to the project root directory
        test_file: Path to the test file to run (relative or absolute)

    Returns:
        tuple: (success, output)
               success is True if tests passed, False if failed
               output is the pytest output as a string

    Example:
        >>> success, output = run_component_tests(root, Path("tests/tools/test_my_tool.py"))
        >>> if success:
        ...     print("Tests passed!")
    """
    try:
        # Make test_file relative to project_root if it's absolute
        if test_file.is_absolute():
            try:
                test_file = test_file.relative_to(project_root)
            except ValueError:
                # test_file is not relative to project_root, use as-is
                pass

        # Run pytest with minimal output
        result = subprocess.run(
            ["pytest", str(test_file), "-v", "--tb=short"],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = result.stdout + result.stderr
        success = result.returncode == 0

        return success, output

    except subprocess.TimeoutExpired:
        return False, "Test execution timed out after 30 seconds"
    except FileNotFoundError:
        return False, "pytest not found. Install with: pip install pytest"
    except Exception as e:
        return False, f"Failed to run tests: {e}"
