"""Git operations for cloning and initializing repositories."""

import shutil
from pathlib import Path

import git
from rich.console import Console

console = Console()


def clone_template(repo_url: str, target_path: Path, branch: str = "main") -> str:
    """
    Clone a git repository template to a target path.

    Performs a shallow clone (depth=1) for faster cloning and removes the .git
    directory to allow fresh initialization.

    Args:
        repo_url: The URL of the git repository to clone
        target_path: The local path where the repository should be cloned
        branch: The branch to clone (default: "main")

    Returns:
        str: The commit hash of the cloned template

    Raises:
        git.GitCommandError: If the clone operation fails
        OSError: If there are filesystem permission issues
    """
    try:
        # Perform shallow clone for faster operation
        console.print(f"[cyan]Cloning template from {repo_url}...[/cyan]")
        repo = git.Repo.clone_from(
            repo_url,
            str(target_path),
            branch=branch,
            depth=1,
            single_branch=True,
        )

        # Get the commit hash before removing .git
        commit_hash = repo.head.commit.hexsha

        # Remove .git directory to allow fresh initialization
        git_dir = target_path / ".git"
        if git_dir.exists():
            shutil.rmtree(git_dir)
            console.print("[green]✓[/green] Template cloned successfully")

        return commit_hash

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


def add_remote(project_path: Path, name: str, url: str) -> None:
    """
    Add a remote to an existing git repository.

    Args:
        project_path: Path to the project directory
        name: Name of the remote (e.g., "origin")
        url: URL of the remote repository

    Raises:
        git.GitCommandError: If the remote operation fails
    """
    try:
        repo = git.Repo(str(project_path))
        repo.create_remote(name, url)
        console.print(f"[green]✓[/green] Added remote '{name}': {url}")
    except git.GitCommandError as e:
        console.print(f"[red]✗[/red] Failed to add remote: {e}")
        raise


def push_to_remote(
    project_path: Path,
    remote: str = "origin",
    branch: str = "main",
    set_upstream: bool = True,
) -> bool:
    """
    Push the current branch to a remote repository.

    Args:
        project_path: Path to the project directory
        remote: Name of the remote (default: "origin")
        branch: Name of the branch to push (default: "main")
        set_upstream: Whether to set the upstream tracking branch (default: True)

    Returns:
        bool: True if push was successful, False otherwise
    """
    try:
        repo = git.Repo(str(project_path))
        remote_obj = repo.remote(remote)

        console.print(f"[cyan]Pushing to {remote}/{branch}...[/cyan]")

        if set_upstream:
            remote_obj.push(branch, set_upstream=True)
        else:
            remote_obj.push(branch)

        console.print(f"[green]✓[/green] Pushed to {remote}/{branch}")
        return True
    except git.GitCommandError as e:
        console.print(f"[red]✗[/red] Failed to push: {e}")
        return False
    except Exception as e:
        console.print(f"[red]✗[/red] Unexpected error during push: {e}")
        return False
