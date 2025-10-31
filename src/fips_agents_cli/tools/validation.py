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

    Supports subdirectory paths (e.g., "country-profiles/japan").

    Args:
        project_root: Path to the project root directory
        component_type: Type of component ('tool', 'resource', 'prompt', 'middleware')
        name: Component name, may include subdirectory path (e.g., "my_tool" or "subdir/my_tool")

    Returns:
        bool: True if component file exists, False otherwise

    Example:
        >>> root = Path("/path/to/project")
        >>> component_exists(root, "tool", "my_tool")
        False
        >>> component_exists(root, "resource", "country-profiles/japan")
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

    # Parse name to handle subdirectories
    name_parts = name.split("/")
    subdirs = name_parts[:-1]
    component_name = name_parts[-1]

    # Build path with subdirectories
    component_base = project_root / "src" / component_dir
    if subdirs:
        subdir_path = Path(*subdirs)
        component_file = component_base / subdir_path / f"{component_name}.py"
    else:
        component_file = component_base / f"{component_name}.py"

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


def parse_huggingface_repo(url_or_repo: str) -> tuple[str | None, str]:
    """
    Parse HuggingFace repository ID from URL or repo ID format.

    Accepts both full URLs and repo IDs:
    - https://huggingface.co/ibm-granite/granite-3.1-2b-instruct
    - ibm-granite/granite-3.1-2b-instruct

    Args:
        url_or_repo: HuggingFace URL or repo ID

    Returns:
        tuple: (repo_id, error_message)
               repo_id is the extracted org/model format if valid, None otherwise
               error_message is empty string if valid, otherwise contains error description

    Examples:
        >>> parse_huggingface_repo("https://huggingface.co/ibm-granite/granite-3.1-2b-instruct")
        ('ibm-granite/granite-3.1-2b-instruct', '')
        >>> parse_huggingface_repo("ibm-granite/granite-3.1-2b-instruct")
        ('ibm-granite/granite-3.1-2b-instruct', '')
        >>> parse_huggingface_repo("invalid")
        (None, 'Invalid HuggingFace repository format...')
    """
    # Remove trailing slashes
    url_or_repo = url_or_repo.rstrip("/")

    # Check if it's a URL
    if url_or_repo.startswith("http://") or url_or_repo.startswith("https://"):
        # Extract repo ID from URL
        # Expected format: https://huggingface.co/org/model
        match = re.match(r"https?://(?:www\.)?huggingface\.co/([^/]+/[^/]+)(?:/.*)?$", url_or_repo)
        if match:
            return match.group(1), ""
        else:
            return None, (
                "Invalid HuggingFace URL format.\n"
                "Expected: https://huggingface.co/org/model-name"
            )
    else:
        # Assume it's a repo ID in org/model format
        # Validate format
        if "/" not in url_or_repo:
            return None, (
                "Invalid HuggingFace repository ID format.\n"
                "Expected: org/model-name (e.g., ibm-granite/granite-3.1-2b-instruct)"
            )

        # Basic validation: should have exactly one slash
        parts = url_or_repo.split("/")
        if len(parts) != 2:
            return None, (
                "Invalid HuggingFace repository ID format.\n"
                "Expected: org/model-name (e.g., ibm-granite/granite-3.1-2b-instruct)"
            )

        org, model = parts
        if not org or not model:
            return None, (
                "Invalid HuggingFace repository ID format.\n"
                "Organization and model name cannot be empty."
            )

        return url_or_repo, ""


def validate_quay_uri(uri: str) -> tuple[bool, str, dict[str, str]]:
    """
    Validate Quay container registry URI with tag.

    Expected format: registry.com/org/repo:tag
    Optionally accepts: https://registry.com/org/repo:tag

    Args:
        uri: Quay container registry URI

    Returns:
        tuple: (is_valid, error_message, components)
               is_valid is True if valid, False otherwise
               error_message is empty string if valid, otherwise contains error description
               components is dict with 'registry', 'repo', 'tag' keys if valid

    Examples:
        >>> validate_quay_uri("quay.io/wjackson/models:granite-3.1-2b")
        (True, '', {'registry': 'quay.io', 'repo': 'wjackson/models', 'tag': 'granite-3.1-2b'})
        >>> validate_quay_uri("https://quay.io/wjackson/models:granite-3.1-2b")
        (True, '', {'registry': 'quay.io', 'repo': 'wjackson/models', 'tag': 'granite-3.1-2b'})
        >>> validate_quay_uri("quay.io/wjackson/models")
        (False, 'Missing tag...', {})
    """
    # Strip protocol if present
    if uri.startswith("https://"):
        uri = uri[8:]  # Remove "https://"
    elif uri.startswith("http://"):
        uri = uri[7:]  # Remove "http://"

    # Check for tag
    if ":" not in uri:
        return (
            False,
            (
                "Missing tag in container URI.\n"
                "Expected format: registry.com/org/repo:tag\n"
                "Example: quay.io/wjackson/models:granite-3.1-2b-instruct"
            ),
            {},
        )

    # Split registry and tag
    uri_without_tag, tag = uri.rsplit(":", 1)

    if not tag:
        return (
            False,
            (
                "Empty tag in container URI.\n"
                "Expected format: registry.com/org/repo:tag\n"
                "Example: quay.io/wjackson/models:granite-3.1-2b-instruct"
            ),
            {},
        )

    # Validate registry format (should contain at least one dot)
    if "/" not in uri_without_tag:
        return (
            False,
            (
                "Invalid container URI format.\n"
                "Expected format: registry.com/org/repo:tag\n"
                "Example: quay.io/wjackson/models:granite-3.1-2b-instruct"
            ),
            {},
        )

    # Split registry and repository
    parts = uri_without_tag.split("/", 1)
    if len(parts) != 2:
        return (
            False,
            (
                "Invalid container URI format.\n"
                "Expected format: registry.com/org/repo:tag\n"
                "Example: quay.io/wjackson/models:granite-3.1-2b-instruct"
            ),
            {},
        )

    registry, repo = parts

    # Basic registry validation (should look like a domain)
    if "." not in registry:
        return (
            False,
            (
                "Invalid registry format (should be a domain like quay.io).\n"
                "Expected format: registry.com/org/repo:tag\n"
                "Example: quay.io/wjackson/models:granite-3.1-2b-instruct"
            ),
            {},
        )

    return True, "", {"registry": registry, "repo": repo, "tag": tag}


def check_registry_login(registry: str) -> tuple[bool, str]:
    """
    Check if user is logged into a container registry.

    Uses `podman login --get-login` to check authentication status.

    Args:
        registry: Registry domain (e.g., 'quay.io')

    Returns:
        tuple: (is_logged_in, username_or_error)
               is_logged_in is True if authenticated, False otherwise
               username_or_error is the username if logged in, error message otherwise

    Examples:
        >>> check_registry_login("quay.io")
        (True, 'myusername')
        >>> check_registry_login("notloggedin.io")
        (False, 'Not logged in')
    """
    import subprocess

    try:
        result = subprocess.run(
            ["podman", "login", "--get-login", registry],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            username = result.stdout.strip()
            if username:
                return True, username
            else:
                return False, "Not logged in to registry"
        else:
            # Check if podman is not installed
            if "command not found" in result.stderr.lower() or "not found" in result.stderr.lower():
                return False, "Podman not installed"
            return False, "Not logged in to registry"

    except subprocess.TimeoutExpired:
        return False, "Registry check timed out"
    except FileNotFoundError:
        return False, "Podman not installed"
    except Exception as e:
        return False, f"Error checking login: {str(e)}"
