"""Create command for generating new projects from templates."""

import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from fips_agents_cli.tools.filesystem import resolve_target_path, validate_target_directory
from fips_agents_cli.tools.git import clone_template, init_repository, is_git_installed
from fips_agents_cli.tools.project import (
    cleanup_template_files,
    to_module_name,
    update_project_name,
    validate_project_name,
)

console = Console()

# Template URL for MCP server projects
MCP_SERVER_TEMPLATE_URL = "https://github.com/rdwj/mcp-server-template"


@click.group()
def create():
    """Create new projects from templates."""
    pass


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
def mcp_server(project_name: str, target_dir: str | None, no_git: bool):
    """
    Create a new MCP server project from template.

    PROJECT_NAME must start with a lowercase letter and contain only
    lowercase letters, numbers, hyphens, and underscores.

    Example:
        fips-agents create mcp-server my-mcp-server
        fips-agents create mcp-server my-mcp-server --target-dir ~/projects
    """
    try:
        # Step 1: Validate project name
        console.print("\n[bold cyan]Creating MCP Server Project[/bold cyan]\n")

        is_valid, error_msg = validate_project_name(project_name)
        if not is_valid:
            console.print(f"[red]✗[/red] Invalid project name: {error_msg}")
            sys.exit(1)

        console.print(f"[green]✓[/green] Project name '{project_name}' is valid")

        # Step 2: Resolve and validate target directory
        target_path = resolve_target_path(project_name, target_dir)

        is_valid, error_msg = validate_target_directory(target_path, allow_existing=False)
        if not is_valid:
            console.print(f"[red]✗[/red] {error_msg}")
            console.print(
                "\n[yellow]Hint:[/yellow] Choose a different name or remove the existing directory"
            )
            sys.exit(1)

        console.print(f"[green]✓[/green] Target directory: {target_path}")

        # Step 3: Check if git is installed
        if not is_git_installed():
            console.print(
                "[yellow]⚠[/yellow] Git is not installed. This is required for cloning templates."
            )
            console.print("[yellow]Hint:[/yellow] Install git from https://git-scm.com/downloads")
            sys.exit(1)

        # Step 4: Clone template repository
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Cloning template repository...", total=None)
            try:
                clone_template(MCP_SERVER_TEMPLATE_URL, target_path)
            except Exception as e:
                console.print("\n[red]✗[/red] Failed to clone template repository")
                console.print(f"[red]Error:[/red] {e}")
                console.print(
                    f"\n[yellow]Hint:[/yellow] Check your internet connection and verify "
                    f"the template URL is accessible:\n{MCP_SERVER_TEMPLATE_URL}"
                )
                sys.exit(1)

        # Step 5: Customize project
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(description="Customizing project...", total=None)
            try:
                update_project_name(target_path, project_name)
                cleanup_template_files(target_path)
            except Exception as e:
                console.print("\n[red]✗[/red] Failed to customize project")
                console.print(f"[red]Error:[/red] {e}")
                sys.exit(1)

        # Step 6: Initialize git repository
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

        # Step 7: Success message with next steps
        module_name = to_module_name(project_name)

        success_message = f"""
[bold green]✓ Successfully created MCP server project![/bold green]

[bold cyan]Project Details:[/bold cyan]
  • Name: {project_name}
  • Module: {module_name}
  • Location: {target_path}

[bold cyan]Next Steps:[/bold cyan]

  1. Navigate to your project:
     [dim]cd {target_path.name}[/dim]

  2. Create and activate a virtual environment:
     [dim]python -m venv venv[/dim]
     [dim]source venv/bin/activate[/dim]  # On Windows: venv\\Scripts\\activate

  3. Install the project in editable mode:
     [dim]pip install -e .[dev][/dim]

  4. Start developing your MCP server!
     [dim]Edit src/{module_name}/ files to add your functionality[/dim]

  5. Run tests:
     [dim]pytest[/dim]

[bold cyan]Documentation:[/bold cyan]
  • Check the README.md in your project for detailed instructions
  • MCP Protocol docs: https://modelcontextprotocol.io/

Happy coding! 🚀
"""

        console.print(Panel(success_message, border_style="green", padding=(1, 2)))

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠[/yellow] Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]✗[/red] Unexpected error: {e}")
        sys.exit(1)
