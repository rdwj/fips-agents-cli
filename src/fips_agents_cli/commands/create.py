"""Create command for generating new projects from templates."""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from fips_agents_cli.commands.model_car import model_car
from fips_agents_cli.tools.filesystem import resolve_target_path, validate_target_directory
from fips_agents_cli.tools.git import (
    add_remote,
    clone_template,
    init_repository,
    is_git_installed,
    push_to_remote,
)
from fips_agents_cli.tools.github import (
    check_gh_prerequisites,
    create_github_repo,
    get_github_username,
    is_gh_authenticated,
    is_gh_installed,
)
from fips_agents_cli.tools.project import (
    cleanup_template_files,
    to_module_name,
    update_project_name,
    validate_project_name,
    write_template_info,
)

console = Console()

# Template URL for MCP server projects
MCP_SERVER_TEMPLATE_URL = "https://github.com/rdwj/mcp-server-template"


@click.group()
def create():
    """Create new projects from templates."""
    pass


# Register subcommands
create.add_command(model_car)


@create.command("mcp-server")
@click.argument("project_name")
@click.option(
    "--target-dir",
    "-t",
    default=None,
    help="Target directory for the project (default: current directory)",
)
@click.option(
    "--no-git",
    is_flag=True,
    default=False,
    help="Skip git repository initialization",
)
@click.option(
    "--github",
    "use_github",
    is_flag=True,
    default=False,
    help="Create GitHub repository and push code",
)
@click.option(
    "--local",
    "use_local",
    is_flag=True,
    default=False,
    help="Create local project only (skip GitHub)",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Non-interactive mode (use defaults, skip prompts)",
)
@click.option(
    "--private",
    is_flag=True,
    default=False,
    help="Make GitHub repository private (default: public)",
)
@click.option(
    "--org",
    default=None,
    help="GitHub organization to create repository in",
)
@click.option(
    "--description",
    "-d",
    "repo_description",
    default=None,
    help="GitHub repository description",
)
@click.option(
    "--remote-only",
    is_flag=True,
    default=False,
    help="Create GitHub repo only, don't clone locally",
)
def mcp_server(
    project_name: str,
    target_dir: str | None,
    no_git: bool,
    use_github: bool,
    use_local: bool,
    yes: bool,
    private: bool,
    org: str | None,
    repo_description: str | None,
    remote_only: bool,
):
    """
    Create a new MCP server project from template.

    PROJECT_NAME must start with a lowercase letter and contain only
    lowercase letters, numbers, hyphens, and underscores.

    By default, if GitHub CLI (gh) is installed and authenticated, prompts
    to create a GitHub repository. Use --local to skip this, or --github
    to require it. Use --yes for non-interactive mode (agents/CI).

    Examples:

        fips-agents create mcp-server my-mcp-server

        fips-agents create mcp-server my-mcp-server --github --private

        fips-agents create mcp-server my-mcp-server --local

        fips-agents create mcp-server my-mcp-server --yes  # Non-interactive
    """
    try:
        # Step 1: Validate options
        if use_github and use_local:
            console.print("[red]✗[/red] Cannot use --github and --local together")
            sys.exit(1)

        if remote_only and use_local:
            console.print("[red]✗[/red] Cannot use --remote-only with --local")
            sys.exit(1)

        # Step 2: Validate project name
        console.print("\n[bold cyan]Creating MCP Server Project[/bold cyan]\n")

        is_valid, error_msg = validate_project_name(project_name)
        if not is_valid:
            console.print(f"[red]✗[/red] Invalid project name: {error_msg}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Project name '{project_name}' is valid")

        # Step 3: Determine mode (GitHub or local)
        create_github = _determine_github_mode(use_github, use_local, yes)

        # Step 4: Check prerequisites
        if not is_git_installed():
            console.print(
                "[yellow]⚠[/yellow] Git is not installed. This is required for cloning templates."
            )
            console.print("[yellow]Hint:[/yellow] Install git from https://git-scm.com/downloads")
            sys.exit(1)

        if create_github:
            ready, error_msg = check_gh_prerequisites()
            if not ready:
                console.print(f"[red]✗[/red] {error_msg}")
                sys.exit(1)

        # Step 5: Resolve and validate target directory (skip for remote-only)
        target_path = None
        if not remote_only:
            target_path = resolve_target_path(project_name, target_dir)

            is_valid, error_msg = validate_target_directory(target_path, allow_existing=False)
            if not is_valid:
                console.print(f"[red]✗[/red] {error_msg}")
                console.print(
                    "\n[yellow]Hint:[/yellow] Choose a different name or remove the existing "
                    "directory"
                )
                sys.exit(1)

            console.print(f"[green]✓[/green] Target directory: {target_path}")

        # Step 6: Create GitHub repo first (if GitHub mode)
        github_repo = None
        github_url = None
        if create_github:
            success, github_url, error_msg = create_github_repo(
                name=project_name,
                private=private,
                org=org,
                description=repo_description,
            )
            if not success:
                console.print(f"[red]✗[/red] {error_msg}")
                sys.exit(1)

            # Construct repo identifier
            owner = org if org else get_github_username()
            github_repo = f"{owner}/{project_name}"

        # Step 7: Handle remote-only mode
        if remote_only:
            _show_remote_only_success(project_name, github_url, github_repo)
            return

        # Step 8: Clone template repository
        template_commit = None
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Cloning template repository...", total=None)
            try:
                template_commit = clone_template(MCP_SERVER_TEMPLATE_URL, target_path)
            except Exception as e:
                console.print("\n[red]✗[/red] Failed to clone template repository")
                console.print(f"[red]Error:[/red] {e}")
                console.print(
                    f"\n[yellow]Hint:[/yellow] Check your internet connection and verify "
                    f"the template URL is accessible:\n{MCP_SERVER_TEMPLATE_URL}"
                )
                sys.exit(1)

        # Step 9: Customize project
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Customizing project...", total=None)
            try:
                update_project_name(target_path, project_name)
                cleanup_template_files(target_path)
                if template_commit:
                    write_template_info(
                        target_path,
                        project_name,
                        MCP_SERVER_TEMPLATE_URL,
                        template_commit,
                        github_repo=github_repo,
                        github_url=github_url,
                    )
            except Exception as e:
                console.print("\n[red]✗[/red] Failed to customize project")
                console.print(f"[red]Error:[/red] {e}")
                sys.exit(1)

        # Step 10: Initialize git repository
        if not no_git:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(description="Initializing git repository...", total=None)
                try:
                    init_repository(target_path, initial_commit=True)
                except Exception as e:
                    console.print("\n[yellow]⚠[/yellow] Failed to initialize git repository")
                    console.print(f"[yellow]Warning:[/yellow] {e}")
                    console.print(
                        "[yellow]You can initialize git manually later with:[/yellow] git init"
                    )

        # Step 11: Push to GitHub (if GitHub mode)
        if create_github and not no_git:
            try:
                add_remote(target_path, "origin", github_url)
                push_success = push_to_remote(target_path, "origin", "main")
                if not push_success:
                    console.print(
                        "\n[yellow]⚠[/yellow] Failed to push to GitHub. "
                        "You can push manually with: git push -u origin main"
                    )
            except Exception as e:
                console.print(f"\n[yellow]⚠[/yellow] Failed to set up GitHub remote: {e}")
                console.print("[yellow]You can add the remote manually with:[/yellow]")
                console.print(f"  git remote add origin {github_url}")
                console.print("  git push -u origin main")

        # Step 12: Success message
        _show_success_message(
            project_name=project_name,
            target_path=target_path,
            github_url=github_url,
            github_repo=github_repo,
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)


def _determine_github_mode(use_github: bool, use_local: bool, yes: bool) -> bool:
    """
    Determine whether to create a GitHub repository.

    Args:
        use_github: --github flag was set
        use_local: --local flag was set
        yes: --yes flag was set (non-interactive mode)

    Returns:
        bool: True if GitHub repository should be created
    """
    # Explicit flags take precedence
    if use_local:
        console.print("[dim]Mode: Local only (--local)[/dim]")
        return False

    if use_github:
        console.print("[dim]Mode: GitHub (--github)[/dim]")
        return True

    # Check if gh is available
    if not is_gh_installed():
        console.print("[dim]Mode: Local only (GitHub CLI not installed)[/dim]")
        return False

    if not is_gh_authenticated():
        console.print("[dim]Mode: Local only (GitHub CLI not authenticated)[/dim]")
        return False

    # gh is available - decide based on interactive mode
    if yes:
        # Non-interactive: default to GitHub
        console.print("[dim]Mode: GitHub (--yes with gh available)[/dim]")
        return True

    # Interactive: prompt user
    console.print("[cyan]GitHub CLI detected and authenticated.[/cyan]")
    return click.confirm("Create GitHub repository?", default=True)


def _show_success_message(
    project_name: str,
    target_path,
    github_url: str | None,
    github_repo: str | None,
) -> None:
    """Display success message with next steps."""
    module_name = to_module_name(project_name)

    # Build project details section
    details = f"""  • Name: {project_name}
  • Module: {module_name}
  • Location: {target_path}"""

    if github_url:
        details += f"\n  • GitHub: {github_url}"

    # Build next steps based on mode
    if github_url:
        next_steps = f"""
  1. Navigate to your project:
     [dim]cd {target_path.name}[/dim]

  2. Create and activate a virtual environment:
     [dim]python -m venv venv[/dim]
     [dim]source venv/bin/activate[/dim]  # On Windows: venv\\Scripts\\activate

  3. Install the project in editable mode:
     [dim]pip install -e .[dev][/dim]

  4. Start developing your MCP server!
     [dim]Your code is already pushed to GitHub[/dim]

  5. Run tests:
     [dim]pytest[/dim]"""
    else:
        next_steps = f"""
  1. Navigate to your project:
     [dim]cd {target_path.name}[/dim]

  2. Create and activate a virtual environment:
     [dim]python -m venv venv[/dim]
     [dim]source venv/bin/activate[/dim]  # On Windows: venv\\Scripts\\activate

  3. Install the project in editable mode:
     [dim]pip install -e .[dev][/dim]

  4. Start developing your MCP server!
     [dim]Edit src/ files to add your functionality[/dim]

  5. Run tests:
     [dim]pytest[/dim]"""

    success_message = f"""
[bold green]✓ Successfully created MCP server project![/bold green]

[bold cyan]Project Details:[/bold cyan]
{details}

[bold cyan]Next Steps:[/bold cyan]
{next_steps}

[bold cyan]Documentation:[/bold cyan]
  • Check the README.md in your project for detailed instructions
  • MCP Protocol docs: https://modelcontextprotocol.io/
"""

    console.print(Panel(success_message, border_style="green", padding=(1, 2)))


def _show_remote_only_success(
    project_name: str,
    github_url: str,
    github_repo: str,
) -> None:
    """Display success message for remote-only mode."""
    success_message = f"""
[bold green]✓ Successfully created GitHub repository![/bold green]

[bold cyan]Repository Details:[/bold cyan]
  • Name: {project_name}
  • GitHub: {github_url}

[bold cyan]Next Steps:[/bold cyan]

  1. Clone the repository:
     [dim]git clone {github_url}[/dim]
     [dim]cd {project_name}[/dim]

  2. The repository contains the MCP server template.
     Customize it for your project.

[bold cyan]Note:[/bold cyan]
  The repository contains the raw template.
  You may want to customize project names and paths.
"""

    console.print(Panel(success_message, border_style="green", padding=(1, 2)))
