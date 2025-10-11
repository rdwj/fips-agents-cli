"""Git operations for cloning and initializing repositories."""

import shutil
from pathlib import Path

import git
from rich.console import Console

console = Console()


def clone_template(repo_url: str, target_path: Path, branch: str = "main") -> None:
    """
    Clone a git repository template to a target path.

    Performs a shallow clone (depth=1) for faster cloning and removes the .git
    directory to allow fresh initialization.

    Args:
        repo_url: The URL of the git repository to clone
        target_path: The local path where the repository should be cloned
        branch: The branch to clone (default: "main")

    Raises:
        git.GitCommandError: If the clone operation fails
        OSError: If there are filesystem permission issues
    """
    try:
        # Perform shallow clone for faster operation
        console.print(f"[cyan]Cloning template from {repo_url}...[/cyan]")
        git.Repo.clone_from(
            repo_url,
            str(target_path),
            branch=branch,
            depth=1,
            single_branch=True,
        )

        # Remove .git directory to allow fresh initialization
        git_dir = target_path / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
            console.print("[green]✓[/green] Template cloned successfully")

    except git.GitCommandError as e:
        console.print(f"[red]✗[/red] Failed to clone template: {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error during clone: {e}")
        raise


def init_repository(project_path: Path, initial_commit: bool = True) -> None:
    """
    Initialize a new git repository in the project directory.

    Args:
        project_path: Path to the project directory
        initial_commit: Whether to create an initial commit (default: True)

    Raises:
        git.GitCommandError: If git operations fail
    """
    try:
        console.print("[cyan]Initializing git repository...[/cyan]")

        # Initialize repository
        repo = git.Repo.init(str(project_path))

        if initial_commit:
            # Add all files
            repo.index.add("*")

            # Create initial commit
            repo.index.commit("Initial commit from fips-agents-cli")

            console.print("[green]✓[/green] Git repository initialized with initial commit")
        else:
            console.print("[green]✓[/green] Git repository initialized")

    except git.GitCommandError as e:
        console.print(f"[red]✗[/red] Failed to initialize git repository: {e}")
        raise
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error during git init: {e}")
        raise


def is_git_installed() -> bool:
    """
    Check if git is installed and available in the system PATH.

    Returns:
        bool: True if git is installed, False otherwise
    """
    try:
        git.Git().version()
        return True
    except (git.GitCommandNotFound, git.GitCommandError):
        return False
