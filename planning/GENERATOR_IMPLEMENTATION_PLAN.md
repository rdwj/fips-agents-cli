# Generator Implementation Plan

## Overview

Implement `fips-agents generate` commands to scaffold MCP components (tools, resources, prompts, middleware) using Jinja2 templates stored in projects.

## Command Structure

```bash
fips-agents generate tool <name> [flags]
fips-agents generate resource <name> [flags]
fips-agents generate prompt <name> [flags]
fips-agents generate middleware <name> [flags]
```

## Architecture

### Code Organization

```
src/fips_agents_cli/
├── commands/
│   ├── create.py          # Existing - creates new projects
│   └── generate.py        # NEW - generates components in existing projects
├── tools/
│   ├── filesystem.py      # Existing - file operations
│   ├── git.py             # Existing - git operations
│   ├── project.py         # Existing - project customization
│   ├── validation.py      # NEW - component validation utilities
│   └── generators.py      # NEW - template rendering utilities
```

### Key Design Decisions

1. **Validation Module**: Keep `validation.py` separate for organization
2. **Interactive Prompts**: Use Click's built-in prompts for consistency
3. **Parameter Specification**: Support `--params params.json` file
4. **Dry Run**: `--dry-run` shows file paths only (not full code)
5. **Test Execution**: Auto-run pytest on generated files and report results

### Deferred to Future Phase

- `fips-agents edit` command group for modifying existing components:
  - `fips-agents edit tool <name> add-param`
  - `fips-agents edit tool <name> remove-param`
  - `fips-agents edit tool <name> edit-param`
  - Similar for resources, prompts, middleware

## Implementation Steps

### Phase 1: Validation Utilities

**File**: `src/fips_agents_cli/tools/validation.py`

Functions:
- `find_project_root() -> Optional[Path]`
  - Walk up from cwd looking for pyproject.toml with fastmcp dependency
  - Return project root path or None
- `is_valid_component_name(name: str) -> tuple[bool, str]`
  - Check if name is valid Python identifier (snake_case)
  - No Python keywords
  - Return (is_valid, error_message)
- `component_exists(project_root: Path, component_type: str, name: str) -> bool`
  - Check if `src/{component_type}/{name}.py` already exists
- `validate_generator_templates(project_root: Path, component_type: str) -> tuple[bool, str]`
  - Check if `.fips-agents-cli/generators/{component_type}/` exists
  - Check if `component.py.j2` and `test.py.j2` exist
  - Return (is_valid, error_message)

### Phase 2: Generator Utilities

**File**: `src/fips_agents_cli/tools/generators.py`

Functions:
- `get_project_info(project_root: Path) -> dict`
  - Load pyproject.toml
  - Extract project name
  - Return dict with project metadata
- `load_template(project_root: Path, component_type: str, template_name: str) -> jinja2.Template`
  - Load from `.fips-agents-cli/generators/{component_type}/{template_name}`
  - Return Jinja2 Template object
- `load_params_file(params_path: Path) -> list[dict]`
  - Load JSON file with parameter definitions
  - Validate schema
  - Return list of parameter dicts
- `render_component(template: jinja2.Template, variables: dict) -> str`
  - Render template with variables
  - Return rendered code as string
- `validate_python_syntax(code: str) -> tuple[bool, str]`
  - Use `ast.parse()` to check syntax
  - Return (is_valid, error_message)
- `write_component_file(content: str, file_path: Path) -> None`
  - Write content to file
  - Create parent directories if needed
- `run_component_tests(project_root: Path, test_file: Path) -> tuple[bool, str]`
  - Run pytest on the generated test file
  - Capture output
  - Return (success, output)

### Phase 3: Generate Command Implementation

**File**: `src/fips_agents_cli/commands/generate.py`

#### Main Command Group

```python
@click.group()
def generate():
    """Generate new MCP components in existing projects."""
    pass
```

#### Tool Subcommand

```python
@generate.command("tool")
@click.argument("name")
@click.option("--async/--sync", "is_async", default=True, help="Generate async or sync function")
@click.option("--with-context", is_flag=True, help="Include FastMCP Context parameter")
@click.option("--with-auth", is_flag=True, help="Include authentication decorator")
@click.option("--description", "-d", help="Tool description")
@click.option("--params", type=click.Path(exists=True), help="JSON file with parameter definitions")
@click.option("--read-only", is_flag=True, default=True, help="Mark as read-only operation")
@click.option("--open-world", is_flag=True, help="Mark as open-world operation")
@click.option("--dry-run", is_flag=True, help="Show what would be generated without creating files")
def tool(name, is_async, with_context, with_auth, description, params, read_only, open_world, dry_run):
    """Generate a new tool component."""
```

**Workflow:**
1. Find project root using validation.find_project_root()
2. Validate component name
3. Check if component already exists
4. Validate generator templates exist
5. Interactive prompt for description if not provided
6. Load params file if provided
7. Build template variables dict
8. Load templates (component.py.j2, test.py.j2)
9. Render both templates
10. If dry-run: show file paths and exit
11. Write component file to `src/tools/{name}.py`
12. Write test file to `tests/tools/test_{name}.py`
13. Validate Python syntax of generated files
14. Run pytest on generated test file
15. Display success message with results

#### Resource Subcommand

```python
@generate.command("resource")
@click.argument("name")
@click.option("--async/--sync", "is_async", default=True)
@click.option("--with-context", is_flag=True)
@click.option("--description", "-d")
@click.option("--uri", help="Resource URI (default: resource://<name>)")
@click.option("--mime-type", default="text/plain", help="MIME type for resource")
@click.option("--dry-run", is_flag=True)
def resource(name, is_async, with_context, description, uri, mime_type, dry_run):
    """Generate a new resource component."""
```

Similar workflow to tool.

#### Prompt Subcommand

```python
@generate.command("prompt")
@click.argument("name")
@click.option("--description", "-d")
@click.option("--params", type=click.Path(exists=True), help="JSON file with parameter definitions")
@click.option("--with-schema", is_flag=True, help="Include JSON schema in prompt")
@click.option("--dry-run", is_flag=True)
def prompt(name, description, params, with_schema, dry_run):
    """Generate a new prompt component."""
```

#### Middleware Subcommand

```python
@generate.command("middleware")
@click.argument("name")
@click.option("--async/--sync", "is_async", default=True)
@click.option("--description", "-d")
@click.option("--dry-run", is_flag=True)
def middleware(name, is_async, description, dry_run):
    """Generate a new middleware component."""
```

### Phase 4: Template Variables

Common variables for all templates:

```python
{
    "component_name": str,         # Snake_case function/class name
    "description": str,             # User-provided description
    "async": bool,                  # Async vs sync
    "with_context": bool,           # Include Context parameter
    "with_auth": bool,              # Include auth decorator
    "project_name": str,            # From pyproject.toml
    "params": list[dict],           # Parameter definitions

    # Tool-specific
    "read_only": bool,
    "idempotent": bool,
    "open_world": bool,

    # Resource-specific
    "uri": str,
    "mime_type": str,

    # Prompt-specific
    "with_schema": bool,

    # Return type
    "return_type": str,
}
```

### Phase 5: Parameters JSON Schema

**Format for `--params params.json`:**

```json
[
  {
    "name": "query",
    "type": "str",
    "description": "Search query",
    "required": true,
    "min_length": 1,
    "max_length": 100
  },
  {
    "name": "limit",
    "type": "int",
    "description": "Maximum results to return",
    "required": false,
    "default": 10,
    "ge": 1,
    "le": 100
  }
]
```

**Supported Types:**
- `str`, `int`, `float`, `bool`
- `list[str]`, `list[int]`, etc.
- `Optional[str]`, `Optional[int]`, etc.

**Pydantic Field Constraints:**
- `min_length`, `max_length` (str)
- `ge`, `le`, `gt`, `lt` (int, float)
- `pattern` (str, regex)

### Phase 6: Error Handling

Clear error messages with hints for:
- **Not in MCP project**: "Run this command from an MCP server project directory"
- **Invalid component name**: "Component name must be a valid Python identifier (snake_case)"
- **Component exists**: "Component already exists. Use --force to overwrite (future)"
- **Templates not found**: "Generator templates not found. Did you create this project with fips-agents?"
- **Invalid params JSON**: "Invalid params file format. See documentation for schema"
- **Permission errors**: "Cannot write to directory. Check permissions"
- **Syntax error in generated code**: "Generated code has syntax errors (this is a bug, please report)"
- **Test failures**: "Generated tests failed (this is a bug, please report)"

### Phase 7: Testing

**Unit Tests** (`tests/test_validation.py`):
- Test `is_valid_component_name()` with valid/invalid names
- Test `find_project_root()` with various directory structures
- Test `component_exists()` detection

**Unit Tests** (`tests/test_generators.py`):
- Test template loading
- Test parameter file loading and validation
- Test variable rendering
- Test Python syntax validation

**Integration Tests** (`tests/test_generate.py`):
- Create temporary MCP project (using mock template)
- Run generate commands
- Verify files are created with correct paths
- Validate generated Python syntax
- Run pytest on generated tests and verify they pass
- Test dry-run mode
- Test error cases

### Phase 8: Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    "click>=8.1.7",
    "rich>=13.7.0",
    "gitpython>=3.1.40",
    "tomlkit>=0.12.3",
    "jinja2>=3.1.2",      # NEW
]
```

### Phase 9: CLI Integration

Update `src/fips_agents_cli/cli.py`:

```python
from fips_agents_cli.commands.create import create
from fips_agents_cli.commands.generate import generate  # NEW

# Register commands
cli.add_command(create)
cli.add_command(generate)  # NEW
```

### Phase 10: Documentation

Update `README.md` with:
- Generator command examples
- Supported component types and flags
- Parameters JSON schema
- Troubleshooting guide

## Success Criteria

- [ ] All generator commands work end-to-end
- [ ] Generated code is syntactically valid Python
- [ ] Generated tests are runnable with pytest
- [ ] Generated tests pass on first run
- [ ] Auto-run pytest and report results to user
- [ ] Rich console output with progress indicators
- [ ] Error handling with helpful messages and hints
- [ ] Dry-run mode shows file paths only
- [ ] Support for `--params` JSON file
- [ ] 80%+ test coverage for new code
- [ ] Documentation updated with examples

## Implementation Order

1. **Phase 1:** `validation.py` - Validation utilities
2. **Phase 2:** `generators.py` - Generator utilities
3. **Phase 3:** `generate.py` - Tool command (most complex, implement first)
4. **Phase 4:** `generate.py` - Resource, Prompt, Middleware commands
5. **Phase 5:** Integration tests
6. **Phase 6:** CLI integration and manual testing
7. **Phase 7:** Documentation

## Timeline Estimate

- Phase 1-2: 2-3 hours (utilities)
- Phase 3: 3-4 hours (tool generation with all features)
- Phase 4: 2-3 hours (other generators, similar to tool)
- Phase 5: 2-3 hours (comprehensive testing)
- Phase 6-7: 1-2 hours (integration and docs)

**Total: ~10-15 hours**

## Future Enhancements (Deferred)

### Edit Commands

```bash
fips-agents edit tool <name> add-param --name query --type str --description "Search query"
fips-agents edit tool <name> remove-param --name query
fips-agents edit tool <name> edit-param --name query --description "New description"
fips-agents edit resource <name> --uri "resource://new-uri"
fips-agents edit prompt <name> add-param --name topic --type str
```

**Implementation approach:**
1. Parse existing Python file (use `ast` module)
2. Locate function definition
3. Modify AST to add/remove/edit parameters
4. Regenerate code from modified AST
5. Preserve formatting with `black`

### List Commands

```bash
fips-agents list tools
fips-agents list resources
fips-agents list prompts
fips-agents list middleware
```

### Template Commands

```bash
fips-agents template validate    # Check templates are valid
fips-agents template customize   # Interactive template editor
```
