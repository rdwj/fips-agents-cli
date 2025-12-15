"""GitHub CLI integration utilities for creating and managing repositories."""

import json
import subprocess
from typing import Any

from rich.console import Console

console = Console()


def is_gh_installed() -> bool:
    """
    Check if the GitHub CLI (gh) is installed and available.

    Returns:
        bool: True if gh is installed, False otherwise
    """
    try:
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_gh_authenticated() -> bool:
    """
    Check if the GitHub CLI is authenticated.

    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_github_username() -> str | None:
    """
    Get the authenticated GitHub username.

    Returns:
        str | None: GitHub username or None if not authenticated
    """
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def create_github_repo(
    name: str,
    private: bool = False,
    org: str | None = None,
    description: str | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Create a new GitHub repository using the gh CLI.

    Args:
        name: Repository name (without owner prefix)
        private: Whether the repository should be private (default: public)
        org: Organization to create the repository in (default: user account)
        description: Repository description

    Returns:
        tuple: (success, repo_url, error_message)
               - success: True if repository was created
               - repo_url: Full URL to the repository (e.g., https://github.com/user/repo)
               - error_message: Error message if creation failed, None otherwise
    """
    # Build the repo name with optional org prefix
    repo_name = f"{org}/{name}" if org else name

    # Build the command
    cmd = ["gh", "repo", "create", repo_name]

    # Add visibility flag
    if private:
        cmd.append("--private")
    else:
        cmd.append("--public")

    # Add description if provided
    if description:
        cmd.extend(["--description", description])

    # Request JSON output for reliable parsing
    cmd.extend(["--json", "url,name,owner"])

    try:
        console.print(f"[cyan]Creating GitHub repository: {repo_name}...[/cyan]")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            # Parse JSON output
            try:
                repo_info = json.loads(result.stdout)
                repo_url = repo_info.get("url", "")
                console.print(f"[green]✓[/green] Repository created: {repo_url}")
                return True, repo_url, None
            except json.JSONDecodeError:
                # Fallback: construct URL from name
                owner = org if org else get_github_username()
                repo_url = f"https://github.com/{owner}/{name}"
                console.print(f"[green]✓[/green] Repository created: {repo_url}")
                return True, repo_url, None
        else:
            error_msg = result.stderr.strip()

            # Check for common error patterns
            if "already exists" in error_msg.lower():
                return False, None, f"Repository '{repo_name}' already exists on GitHub"
            elif "not found" in error_msg.lower() and org:
                return False, None, f"Organization '{org}' not found or you don't have access"
            elif "authentication" in error_msg.lower() or "login" in error_msg.lower():
                return False, None, "GitHub authentication required. Run 'gh auth login' first"
            else:
                return False, None, f"Failed to create repository: {error_msg}"

    except FileNotFoundError:
        return False, None, "GitHub CLI (gh) is not installed"
    except subprocess.TimeoutExpired:
        return False, None, "Timed out while creating repository"


def get_repo_info(repo: str) -> dict[str, Any] | None:
    """
    Get information about a GitHub repository.

    Args:
        repo: Repository in "owner/name" format

    Returns:
        dict | None: Repository information or None if not found
    """
    try:
        result = subprocess.run(
            ["gh", "repo", "view", repo, "--json", "name,owner,url,description,isPrivate"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return None


def check_gh_prerequisites() -> tuple[bool, str | None]:
    """
    Check all GitHub CLI prerequisites for creating repositories.

    Returns:
        tuple: (ready, error_message)
               - ready: True if all prerequisites are met
               - error_message: Description of what's missing, None if ready
    """
    if not is_gh_installed():
        return False, (
            "GitHub CLI (gh) is not installed.\n" "Install it from: https://cli.github.com/"
        )

    if not is_gh_authenticated():
        return False, ("GitHub CLI is not authenticated.\n" "Run 'gh auth login' to authenticate.")

    return True, None
