"""Filesystem utilities for project operations."""

from pathlib import Path

from rich.console import Console

console = Console()


def ensure_directory_exists(path: Path, create: bool = False) -> bool:
    """
    Check if a directory exists, optionally creating it.

    Args:
        path: The directory path to check
        create: Whether to create the directory if it doesn't exist

    Returns:
        bool: True if directory exists (or was created), False otherwise
    """
    if path.exists():
        return path.is_dir()

    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to create directory {path}: {e}")
            return False

    return False


def check_directory_empty(path: Path) -> bool:
    """
    Check if a directory is empty.

    Args:
        path: The directory path to check

    Returns:
        bool: True if directory is empty, False otherwise
    """
    if not path.exists():
        return True

    if not path.is_dir():
        return False

    return not any(path.iterdir())


def validate_target_directory(
    target_path: Path, allow_existing: bool = False
) -> tuple[bool, str | None]:
    """
    Validate that a target directory is suitable for project creation.

    Args:
        target_path: The target directory path
        allow_existing: Whether to allow existing directories (must be empty)

    Returns:
        tuple: (is_valid, error_message)
               is_valid is True if valid, False otherwise
               error_message is None if valid, otherwise contains the error description
    """
    # Check if parent directory exists
    parent = target_path.parent
    if not parent.exists():
        return False, f"Parent directory does not exist: {parent}"

    # Check if target already exists
    if target_path.exists():
        if not allow_existing:
            return False, f"Directory already exists: {target_path}"

        if not target_path.is_dir():
            return False, f"Path exists but is not a directory: {target_path}"

        if not check_directory_empty(target_path):
            return False, f"Directory is not empty: {target_path}"

    return True, None


def resolve_target_path(project_name: str, target_dir: str | None = None) -> Path:
    """
    Resolve the target path for project creation.

    Args:
        project_name: The name of the project
        target_dir: Optional target directory (defaults to current directory)

    Returns:
        Path: The resolved absolute path for the project
    """
    if target_dir:
        base = Path(target_dir).resolve()
    else:
        base = Path.cwd()

    return base / project_name


def get_relative_path(path: Path, base: Path | None = None) -> str:
    """
    Get a relative path string for display purposes.

    Args:
        path: The path to convert
        base: Base path for relative calculation (defaults to current directory)

    Returns:
        str: Relative path string, or absolute if relative calculation fails
    """
    if base is None:
        base = Path.cwd()

    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)
