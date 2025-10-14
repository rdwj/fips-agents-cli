"""Generate command for scaffolding MCP components in existing projects."""

import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from fips_agents_cli.tools.generators import (
    compute_type_hint,
    get_project_info,
    load_params_file,
    load_template,
    render_component,
    run_component_tests,
    validate_python_syntax,
    write_component_file,
)
from fips_agents_cli.tools.validation import (
    component_exists,
    find_project_root,
    is_valid_component_name,
    validate_generator_templates,
)

console = Console()


def generate_component_workflow(
    component_type: str,
    name: str,
    template_vars: dict[str, Any],
    params_path: str | None,
    dry_run: bool,
    description: str | None,
) -> None:
    """
    Common workflow for generating any component type.

    Args:
        component_type: Type of component ('tool', 'resource', 'prompt', 'middleware')
        name: Component name
        template_vars: Template variables dictionary
        params_path: Optional path to params JSON file
        dry_run: If True, only show what would be generated
        description: Component description
    """
    # Step 1: Find project root
    project_root = find_project_root()
    if not project_root:
        console.print(
            "[red]✗[/red] Not in an MCP server project directory\n"
            "[yellow]Hint:[/yellow] Run this command from within an MCP server project, "
            "or use 'fips-agents create mcp-server' to create one"
        )
        sys.exit(1)

    console.print(f"[green]✓[/green] Found project root: {project_root}")

    # Step 2: Validate component name
    is_valid, error_msg = is_valid_component_name(name)
    if not is_valid:
        console.print(f"[red]✗[/red] Invalid component name: {error_msg}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Component name '{name}' is valid")

    # Step 3: Check if component already exists
    if component_exists(project_root, component_type, name):
        console.print(
            f"[red]✗[/red] Component '{name}' already exists in src/{component_type}s/\n"
            "[yellow]Hint:[/yellow] Choose a different name or manually remove the existing file"
        )
        sys.exit(1)

    # Step 4: Validate generator templates
    is_valid, error_msg = validate_generator_templates(project_root, component_type)
    if not is_valid:
        console.print(f"[red]✗[/red] {error_msg}")
        sys.exit(1)

    console.print(f"[green]✓[/green] Generator templates found for '{component_type}'")

    # Step 5: Prompt for description if not provided
    if not description:
        description = click.prompt(
            f"Enter a description for the {component_type}",
            type=str,
            default="TODO: Add description",
        )

    template_vars["description"] = description
    template_vars["component_name"] = name

    # Step 6: Load params file if provided
    if params_path:
        try:
            params = load_params_file(Path(params_path))
            template_vars["params"] = params
            console.print(f"[green]✓[/green] Loaded {len(params)} parameter(s) from {params_path}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load parameters file: {e}")
            sys.exit(1)
    elif "params" not in template_vars:
        template_vars["params"] = []

    # Compute type hints for each parameter
    for param in template_vars.get("params", []):
        param["type_hint"] = compute_type_hint(param)

    # Step 7: Get project info
    try:
        project_info = get_project_info(project_root)
        template_vars["project_name"] = project_info["name"]
    except Exception as e:
        console.print(f"[yellow]⚠[/yellow] Could not load project info: {e}")
        template_vars["project_name"] = "unknown"

    # Step 8: Define file paths
    component_dir_map = {
        "tool": "tools",
        "resource": "resources",
        "prompt": "prompts",
        "middleware": "middleware",
    }
    component_dir = component_dir_map[component_type]

    component_file = project_root / "src" / component_dir / f"{name}.py"
    test_file = project_root / "tests" / component_dir / f"test_{name}.py"

    # Step 9: Dry run - show paths and exit
    if dry_run:
        console.print("\n[bold cyan]Dry Run - Files that would be generated:[/bold cyan]\n")
        console.print(f"  [cyan]Component:[/cyan] {component_file}")
        console.print(f"  [cyan]Test:[/cyan] {test_file}")
        console.print("\n[dim]Template variables:[/dim]")
        for key, value in template_vars.items():
            if key == "params" and isinstance(value, list):
                console.print(f"  {key}: {len(value)} parameter(s)")
            else:
                console.print(f"  {key}: {value}")
        sys.exit(0)

    # Step 10: Load and render templates
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Generating component files...", total=None)

        try:
            # Load templates
            component_template = load_template(project_root, component_type, "component.py.j2")
            test_template = load_template(project_root, component_type, "test.py.j2")

            # Render templates
            component_code = render_component(component_template, template_vars)
            test_code = render_component(test_template, template_vars)

        except Exception as e:
            console.print(f"\n[red]✗[/red] Failed to render templates: {e}")
            sys.exit(1)

    # Step 11: Validate Python syntax
    is_valid, error_msg = validate_python_syntax(component_code)
    if not is_valid:
        console.print(f"[red]✗[/red] Generated component has syntax errors: {error_msg}")
        console.print("[red]This is a bug in the template. Please report this issue.[/red]")
        sys.exit(1)

    is_valid, error_msg = validate_python_syntax(test_code)
    if not is_valid:
        console.print(f"[red]✗[/red] Generated test has syntax errors: {error_msg}")
        console.print("[red]This is a bug in the template. Please report this issue.[/red]")
        sys.exit(1)

    console.print("[green]✓[/green] Generated code passed syntax validation")

    # Step 12: Write files
    try:
        write_component_file(component_code, component_file)
        console.print(f"[green]✓[/green] Created: {component_file.relative_to(project_root)}")

        write_component_file(test_code, test_file)
        console.print(f"[green]✓[/green] Created: {test_file.relative_to(project_root)}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to write files: {e}")
        sys.exit(1)

    # Step 13: Run tests
    console.print("\n[cyan]Running generated tests...[/cyan]")
    success, output = run_component_tests(project_root, test_file)

    if success:
        console.print("[green]✓[/green] Tests passed!\n")
    else:
        console.print("[yellow]⚠[/yellow] Tests failed or had issues:\n")
        console.print(output)
        console.print(
            "\n[yellow]Note:[/yellow] Generated tests are placeholders. "
            "Update them with your actual test cases."
        )

    # Step 14: Success message
    success_message = f"""
[bold green]✓ Successfully generated {component_type} component![/bold green]

[bold cyan]Files Created:[/bold cyan]
  • {component_file.relative_to(project_root)}
  • {test_file.relative_to(project_root)}

[bold cyan]Next Steps:[/bold cyan]
  1. Review the generated code and implement the business logic
  2. Update the test file with real test cases
  3. Run tests: [dim]pytest {test_file.relative_to(project_root)}[/dim]
  4. Import and use your {component_type} in your MCP server

[bold cyan]Implementation Notes:[/bold cyan]
  • Replace TODO comments with actual implementation
  • Remove placeholder return values
  • Add proper error handling
  • Update docstrings as needed
"""

    console.print(Panel(success_message, border_style="green", padding=(1, 2)))


@click.group()
def generate():
    """Generate new MCP components in existing projects."""
    pass


@generate.command("tool")
@click.argument("name")
@click.option(
    "--async/--sync",
    "is_async",
    default=True,
    help="Generate async or sync function (default: async)",
)
@click.option("--with-context", is_flag=True, help="Include FastMCP Context parameter")
@click.option("--with-auth", is_flag=True, help="Include authentication decorator")
@click.option("--description", "-d", help="Tool description")
@click.option("--params", type=click.Path(exists=True), help="JSON file with parameter definitions")
@click.option(
    "--read-only", is_flag=True, default=True, help="Mark as read-only operation (default: true)"
)
@click.option("--idempotent", is_flag=True, default=True, help="Mark as idempotent (default: true)")
@click.option("--open-world", is_flag=True, help="Mark as open-world operation")
@click.option("--return-type", default="str", help="Return type annotation (default: str)")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def tool(
    name: str,
    is_async: bool,
    with_context: bool,
    with_auth: bool,
    description: str | None,
    params: str | None,
    read_only: bool,
    idempotent: bool,
    open_world: bool,
    return_type: str,
    dry_run: bool,
):
    """
    Generate a new tool component.

    NAME is the tool name in snake_case (e.g., search_documents, fetch_data)

    Example:
        fips-agents generate tool search_documents --description "Search through documents"
        fips-agents generate tool fetch_data --params params.json --with-context
    """
    console.print("\n[bold cyan]Generating Tool Component[/bold cyan]\n")

    template_vars = {
        "async": is_async,
        "with_context": with_context,
        "with_auth": with_auth,
        "read_only": read_only,
        "idempotent": idempotent,
        "open_world": open_world,
        "return_type": return_type,
    }

    generate_component_workflow("tool", name, template_vars, params, dry_run, description)


@generate.command("resource")
@click.argument("name")
@click.option(
    "--async/--sync",
    "is_async",
    default=True,
    help="Generate async or sync function (default: async)",
)
@click.option("--with-context", is_flag=True, help="Include FastMCP Context parameter")
@click.option("--description", "-d", help="Resource description")
@click.option("--uri", help="Resource URI (default: resource://<name>)")
@click.option(
    "--mime-type", default="text/plain", help="MIME type for resource (default: text/plain)"
)
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def resource(
    name: str,
    is_async: bool,
    with_context: bool,
    description: str | None,
    uri: str | None,
    mime_type: str,
    dry_run: bool,
):
    """
    Generate a new resource component.

    NAME is the resource name in snake_case (e.g., config_data, user_profile)

    Example:
        fips-agents generate resource config_data --description "Application configuration"
        fips-agents generate resource user_profile --uri "resource://users/{id}"
    """
    console.print("\n[bold cyan]Generating Resource Component[/bold cyan]\n")

    # Default URI if not provided
    if not uri:
        uri = f"resource://{name}"

    template_vars = {
        "async": is_async,
        "with_context": with_context,
        "uri": uri,
        "mime_type": mime_type,
        "return_type": "str",  # Resources typically return strings
    }

    generate_component_workflow("resource", name, template_vars, None, dry_run, description)


@generate.command("prompt")
@click.argument("name")
@click.option("--description", "-d", help="Prompt description")
@click.option("--params", type=click.Path(exists=True), help="JSON file with parameter definitions")
@click.option("--with-schema", is_flag=True, help="Include JSON schema in prompt")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def prompt(
    name: str,
    description: str | None,
    params: str | None,
    with_schema: bool,
    dry_run: bool,
):
    """
    Generate a new prompt component.

    NAME is the prompt name in snake_case (e.g., code_review, summarize_text)

    Example:
        fips-agents generate prompt code_review --description "Review code for best practices"
        fips-agents generate prompt summarize_text --params params.json
    """
    console.print("\n[bold cyan]Generating Prompt Component[/bold cyan]\n")

    template_vars = {
        "with_schema": with_schema,
        "async": False,  # Prompts are typically not async
        "return_type": "list[PromptMessage]",
    }

    generate_component_workflow("prompt", name, template_vars, params, dry_run, description)


@generate.command("middleware")
@click.argument("name")
@click.option(
    "--async/--sync",
    "is_async",
    default=True,
    help="Generate async or sync function (default: async)",
)
@click.option("--description", "-d", help="Middleware description")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def middleware(
    name: str,
    is_async: bool,
    description: str | None,
    dry_run: bool,
):
    """
    Generate a new middleware component.

    NAME is the middleware name in snake_case (e.g., auth_middleware, rate_limiter)

    Example:
        fips-agents generate middleware auth_middleware --description "Authentication middleware"
        fips-agents generate middleware rate_limiter --sync
    """
    console.print("\n[bold cyan]Generating Middleware Component[/bold cyan]\n")

    template_vars = {
        "async": is_async,
        "return_type": "None",  # Middleware typically doesn't return values
    }

    generate_component_workflow("middleware", name, template_vars, None, dry_run, description)
