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

    # Step 2: Parse name to handle subdirectories
    # Support names like "country-profiles/japan" or "checklists/first_trip"
    name_parts = name.split("/")
    subdirs = name_parts[:-1]  # Everything except the last part
    component_name = name_parts[-1]  # Last part is the actual component name

    # Validate component name (just the filename, not the path)
    is_valid, error_msg = is_valid_component_name(component_name)
    if not is_valid:
        console.print(f"[red]✗[/red] Invalid component name: {error_msg}")
        sys.exit(1)

    # Validate subdirectory names (should be valid Python identifiers)
    for subdir in subdirs:
        if not subdir.replace("-", "_").replace("_", "").isidentifier():
            console.print(
                f"[red]✗[/red] Invalid subdirectory name: '{subdir}'\n"
                "[yellow]Hint:[/yellow] Use snake_case or kebab-case (letters, numbers, hyphens, underscores)"
            )
            sys.exit(1)

    if subdirs:
        console.print(
            f"[green]✓[/green] Component '{component_name}' will be created in {'/'.join(subdirs)}/"
        )
    else:
        console.print(f"[green]✓[/green] Component name '{component_name}' is valid")

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
    template_vars["component_name"] = component_name

    # Build the full module path for imports (e.g., "country_profiles.japan" or just "japan")
    # Convert hyphens to underscores for valid Python module names
    if subdirs:
        subdir_parts = [s.replace("-", "_") for s in subdirs]
        template_vars["module_path"] = ".".join(subdir_parts + [component_name])
    else:
        template_vars["module_path"] = component_name

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

    # Build component path with subdirectories
    component_base = project_root / "src" / component_dir
    test_base = project_root / "tests" / component_dir

    # Handle subdirectories
    if subdirs:
        # Create subdirectory path (convert hyphens to underscores for valid Python package names)
        subdir_parts_normalized = [s.replace("-", "_") for s in subdirs]
        subdir_path = Path(*subdir_parts_normalized)
        component_file = component_base / subdir_path / f"{component_name}.py"
        test_file = test_base / subdir_path / f"test_{component_name}.py"
    else:
        component_file = component_base / f"{component_name}.py"
        test_file = test_base / f"test_{component_name}.py"

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

    # Step 12: Create subdirectories and __init__.py files if needed
    if subdirs:
        # Normalize subdirectory names (convert hyphens to underscores)
        subdirs_normalized = [s.replace("-", "_") for s in subdirs]

        # Create subdirectories in src/
        src_subdir = component_base
        for subdir in subdirs_normalized:
            src_subdir = src_subdir / subdir
            src_subdir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py if it doesn't exist
            init_file = src_subdir / "__init__.py"
            if not init_file.exists():
                init_file.write_text(f'"""{subdir.replace("_", " ").title()} package."""\n')
                console.print(f"[green]✓[/green] Created: {init_file.relative_to(project_root)}")

        # Create subdirectories in tests/
        test_subdir = test_base
        for subdir in subdirs_normalized:
            test_subdir = test_subdir / subdir
            test_subdir.mkdir(parents=True, exist_ok=True)

            # Create __init__.py if it doesn't exist
            init_file = test_subdir / "__init__.py"
            if not init_file.exists():
                init_file.write_text(f'"""{subdir.replace("_", " ").title()} tests."""\n')
                console.print(f"[green]✓[/green] Created: {init_file.relative_to(project_root)}")

    # Step 13: Write files
    try:
        write_component_file(component_code, component_file)
        console.print(f"[green]✓[/green] Created: {component_file.relative_to(project_root)}")

        write_component_file(test_code, test_file)
        console.print(f"[green]✓[/green] Created: {test_file.relative_to(project_root)}")

    except Exception as e:
        console.print(f"[red]✗[/red] Failed to write files: {e}")
        sys.exit(1)

    # Step 14: Run tests
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

    # Step 15: Success message
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
@click.option(
    "--scopes",
    help='Required OAuth scopes (comma-separated, e.g., "read:data,write:data")',
)
@click.option("--with-elicitation", is_flag=True, help="Include elicitation example code")
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
    scopes: str | None,
    with_elicitation: bool,
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

    Examples:
        # Basic tool
        fips-agents generate tool search_documents --description "Search through documents"

        # Tool with context and parameters
        fips-agents generate tool fetch_data --params params.json --with-context

        # Interactive tool with elicitation
        fips-agents generate tool delete_resources --with-elicitation --with-context

        # Protected tool with authentication
        fips-agents generate tool delete_data --with-auth --scopes "write:data,admin"

        # Protected tool (interactive scope prompting)
        fips-agents generate tool get_profile --with-auth
    """
    console.print("\n[bold cyan]Generating Tool Component[/bold cyan]\n")

    # Handle scope prompting for authenticated tools
    required_scopes = []
    if with_auth:
        if scopes:
            # Parse comma-separated scopes from CLI
            required_scopes = [s.strip() for s in scopes.split(",") if s.strip()]
        else:
            # Interactive prompting with default
            scopes_input = click.prompt(
                "Enter required OAuth scopes (comma-separated)",
                type=str,
                default="read:data",
            )
            required_scopes = [s.strip() for s in scopes_input.split(",") if s.strip()]

        console.print(f"[green]✓[/green] Required scopes: {', '.join(required_scopes)}")

    template_vars = {
        "async": is_async,
        "with_context": with_context,
        "with_auth": with_auth,
        "required_scopes": required_scopes,  # Pass as list for template
        "with_elicitation": with_elicitation,
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

    NAME is the resource name in snake_case (e.g., config_data, user_profile).
    Subdirectories are supported using forward slashes (e.g., country-profiles/japan).

    Examples:
        # Simple resource in resources/ directory
        fips-agents generate resource config_data --description "Application configuration"

        # Resource with URI template (parameters automatically extracted)
        fips-agents generate resource user_profile --uri "resource://users/{id}"

        # Resource in subdirectory (creates country_profiles/japan.py)
        fips-agents generate resource country-profiles/japan --description "Japan country profile"

        # Multiple levels of subdirectories
        fips-agents generate resource checklists/travel/first_trip --description "First trip checklist"
    """
    import re

    console.print("\n[bold cyan]Generating Resource Component[/bold cyan]\n")

    # Extract component name from path (without subdirs) for URI default
    component_name = name.split("/")[-1]

    # Default URI if not provided
    if not uri:
        uri = f"resource://{component_name}"

    # Extract URI template parameters (e.g., {country_code}, {id})
    uri_params = re.findall(r"\{(\w+)\}", uri)

    # Convert URI parameters to function parameters
    # Each URI parameter becomes a string parameter in the function signature
    params_list = [
        {
            "name": param,
            "type": "str",
            "type_hint": "str",
            "description": f"URI parameter: {param}",
            "required": True,
        }
        for param in uri_params
    ]

    template_vars = {
        "async": is_async,
        "with_context": with_context,
        "uri": uri,
        "mime_type": mime_type,
        "return_type": "str",  # Resources typically return strings
        "params": params_list,  # Add URI parameters
        "uri_params": uri_params,  # Also pass raw param names for template
    }

    generate_component_workflow("resource", name, template_vars, None, dry_run, description)


@generate.command("prompt")
@click.argument("name")
@click.option(
    "--async/--sync",
    "is_async",
    default=False,
    help="Generate async or sync function (default: sync)",
)
@click.option("--with-context", is_flag=True, help="Include FastMCP Context parameter")
@click.option("--description", "-d", help="Prompt description")
@click.option("--params", type=click.Path(exists=True), help="JSON file with parameter definitions")
@click.option(
    "--return-type",
    type=click.Choice(["str", "PromptMessage", "PromptResult", "list[PromptMessage]"]),
    default="str",
    help="Return type annotation (default: str)",
)
@click.option("--with-schema", is_flag=True, help="Include JSON schema example in prompt body")
@click.option("--prompt-name", help="Override decorator name (default: use function name)")
@click.option("--title", help="Human-readable title for the prompt")
@click.option("--tags", help="Comma-separated tags for categorization")
@click.option("--disabled", is_flag=True, help="Generate prompt in disabled state")
@click.option("--meta", help='JSON string of metadata (e.g., \'{"version": "1.0"}\')')
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def prompt(
    name: str,
    is_async: bool,
    with_context: bool,
    description: str | None,
    params: str | None,
    return_type: str,
    with_schema: bool,
    prompt_name: str | None,
    title: str | None,
    tags: str | None,
    disabled: bool,
    meta: str | None,
    dry_run: bool,
):
    """
    Generate a new prompt component.

    NAME is the prompt name in snake_case (e.g., code_review, summarize_text)

    Examples:
        # Basic string prompt
        fips-agents generate prompt code_review --description "Review code for best practices"

        # Async prompt with Context
        fips-agents generate prompt fetch_data --async --with-context --return-type PromptMessage

        # Prompt with parameters and schema
        fips-agents generate prompt analyze_data --params params.json --with-schema

        # Advanced: custom name, tags, metadata
        fips-agents generate prompt generate_report \\
            --prompt-name "report_generator" \\
            --title "Report Generator" \\
            --tags "reporting,analysis" \\
            --meta '{"version": "2.0", "author": "data-team"}'
    """
    console.print("\n[bold cyan]Generating Prompt Component[/bold cyan]\n")

    # Parse tags
    tags_list = [t.strip() for t in tags.split(",")] if tags else None

    # Parse metadata
    meta_dict = None
    if meta:
        try:
            import json

            meta_dict = json.loads(meta)
        except json.JSONDecodeError as e:
            console.print(f"[red]✗[/red] Invalid JSON in --meta: {e}")
            sys.exit(1)

    # Determine if prompt imports are needed
    needs_prompt_imports = return_type in ["PromptMessage", "PromptResult", "list[PromptMessage]"]

    template_vars = {
        "async": is_async,
        "with_context": with_context,
        "return_type": return_type,
        "with_schema": with_schema,
        "prompt_name": prompt_name,
        "title": title,
        "tags": tags_list,
        "enabled": not disabled,
        "meta": meta_dict,
        "needs_prompt_imports": needs_prompt_imports,
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
