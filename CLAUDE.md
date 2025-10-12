# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**fips-agents-cli** is a Python-based CLI tool for scaffolding FIPS-compliant AI agent projects, with initial focus on MCP (Model Context Protocol) server development. The tool clones template repositories, customizes them for new projects, and prepares them for immediate development use.

**Current Status:** MVP implementation complete with `create mcp-server` command.

## Development Commands

### Environment Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .[dev]
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=fips_agents_cli --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_create.py

# Run specific test
pytest tests/test_create.py::TestCreateMcpServer::test_successful_creation
```

### Code Quality

```bash
# Format code with Black (line length: 100)
black src tests

# Lint with Ruff
ruff check src tests

# Run both linters before committing
black src tests && ruff check src tests
```

### Building and Distribution

```bash
# Build distribution packages
python -m build

# Verify package integrity
twine check dist/*

# Test local installation
pip install -e .
fips-agents --version
```

## Architecture

### Module Structure

The CLI follows a layered architecture:

1. **CLI Layer** (`cli.py`): Click-based command interface with Rich output
2. **Command Layer** (`commands/`): Command implementations (create, generate, etc.)
3. **Tools Layer** (`tools/`): Reusable utilities for git, filesystem, and project operations
4. **Entry Points**: `__main__.py` for `python -m fips_agents_cli`, `cli:main` for the `fips-agents` command

### Key Design Patterns

**Template Repository Pattern**: The CLI clones git repositories as templates rather than bundling templates internally. This allows:
- Independent template versioning and updates
- User customization via template forks
- Minimal CLI package size

**Project Customization Pipeline**: When creating projects, the tool follows this sequence:
1. Clone template repository (shallow clone, depth=1)
2. Remove template's `.git` directory
3. Update `pyproject.toml` with new project name
4. Rename source directory (`template_name` → `project_name` with underscores)
5. Update entry point scripts in `pyproject.toml`
6. Initialize fresh git repository with initial commit

**Rich Console Output**: All user-facing output uses Rich library for:
- Colored output (green checkmarks, red errors, yellow warnings)
- Progress spinners for long operations
- Formatted panels for success messages
- Consistent visual style

### Important Implementation Details

**Project Name Handling**: Project names use hyphens (kebab-case) but module names use underscores (snake_case). The `to_module_name()` utility converts between these formats. This is critical for Python import compatibility.

**TOML Manipulation**: Uses `tomlkit` (not `toml`) to preserve formatting and comments in `pyproject.toml` files during customization.

**Git Operations**: Uses GitPython library for all git operations. Template clones are shallow (depth=1) for performance. The `.git` directory from templates is always removed before initializing a fresh repository.

**Error Handling Strategy**: Commands use Rich console for user-friendly error messages, then call `sys.exit()` with appropriate exit codes. Validation failures provide hints for correction.

## Testing Architecture

### Test Structure

Tests are organized by module:
- `test_create.py`: Create command integration tests
- `test_filesystem.py`: Filesystem utility unit tests
- `test_project.py`: Project customization unit tests

### Key Fixtures

**`cli_runner`**: Provides Click's `CliRunner` for command testing. Use `invoke()` to run commands in isolated environment.

**`temp_dir`**: Provides temporary directory that's automatically cleaned up. Use for file operations.

**`mock_template_repo`**: Creates a complete mock MCP server template structure with:
- `pyproject.toml` with placeholder project name
- `src/mcp_server_template/` module directory
- `prompts/` directory for YAML prompts
- `.fips-agents-cli/generators/` for future generator templates

### Testing Patterns

When testing commands:
```python
result = runner.invoke(cli, ["create", "mcp-server", "test-server"])
assert result.exit_code == 0
assert "Success" in result.output
```

When testing with filesystem fixtures:
```python
def test_something(temp_dir):
    project_path = temp_dir / "my-project"
    # Test filesystem operations
```

## Configuration Files

### pyproject.toml

- **Build System**: Uses Hatchling (not Poetry or setuptools)
- **Python Version**: Requires ≥3.9, supports 3.9-3.12
- **Line Length**: Black and Ruff both configured for 100 characters
- **Entry Point**: `fips-agents = "fips_agents_cli.cli:main"`
- **Test Configuration**: pytest runs with coverage by default

### CI/CD Workflows

**test.yml**: Runs on push/PR to main
- Matrix testing across Python 3.9, 3.10, 3.11, 3.12
- Runs pytest with coverage
- Checks Black formatting
- Runs Ruff linting
- Builds distribution and validates with twine

**workflow.yaml**: Publishes to PyPI on GitHub releases
- Uses trusted publishing (no API key needed)
- Builds wheels and source distributions
- Uploads to PyPI automatically

## Common Development Patterns

### Adding a New Command

1. Create command file in `commands/` directory
2. Define Click command group or command
3. Register in `cli.py` with `cli.add_command()`
4. Use Rich console for all output
5. Add comprehensive tests in `tests/test_commandname.py`

### Adding a New Tool/Utility

1. Create utility module in `tools/` directory
2. Import Rich console: `console = Console()`
3. Provide clear docstrings with Args/Returns
4. Return meaningful values (bool, tuple, etc.) not just console output
5. Test in isolation with fixtures

### File Operations Best Practices

- Always use `pathlib.Path`, never string paths
- Use `Path.resolve()` for absolute paths in user-facing messages
- Check existence before operations: `path.exists()`
- Use `parents=True, exist_ok=True` for `mkdir()` calls
- Handle errors gracefully with try/except and user-friendly messages

### Output Conventions

- Success: `[green]✓[/green] Message`
- Error: `[red]✗[/red] Message`
- Warning: `[yellow]⚠[/yellow] Message`
- Info: `[cyan]Message[/cyan]` or `[dim]Message[/dim]`
- Use `console.print()` not `print()` or `click.echo()`

## Known Patterns and Conventions

### Template Repository Structure

The CLI expects templates to have:
- `pyproject.toml` with project name and entry points
- `src/{module_name}/` source directory
- `.fips-agents-cli/generators/` (optional, for Phase 2 generate commands)
- Standard Python project structure

### Project Name Validation

Valid project names must:
- Start with a lowercase letter
- Contain only lowercase letters, numbers, hyphens, and underscores
- Not be empty

Examples:
- ✅ `my-server`, `test_mcp`, `server123`
- ❌ `MyServer` (uppercase), `123server` (starts with number), `my@server` (special chars)

### Module vs Project Names

- **Project name**: Uses hyphens (e.g., `my-mcp-server`)
- **Module name**: Uses underscores (e.g., `my_mcp_server`)
- Conversion: `project_name.replace("-", "_")`
- This matters for imports and directory names

## Future Roadmap Context

### Phase 2 (Next): Generate Command

The `generate` command will:
- Load generator templates from `.fips-agents-cli/generators/` in projects
- Use Jinja2 for template rendering
- Support tool, prompt, and resource generation
- Interactive prompts for parameters

Template location strategy: Generators are copied into projects during creation (not kept in CLI), allowing per-project customization.

### Why This Matters Now

- Don't remove `.fips-agents-cli/` directories during template cloning
- Test fixtures already include generator directory structure
- Project customization must preserve these directories

## Troubleshooting Common Issues

### Git Clone Failures

Check:
1. Internet connectivity
2. Template repository URL is accessible
3. Git is installed: `git --version`
4. Permissions on target directory

### Module Not Found After Installation

Ensure:
1. Virtual environment is activated
2. Package installed with `-e` flag: `pip install -e .`
3. Using correct Python interpreter: `which python`

### Test Failures

Common causes:
1. Forgot to activate venv
2. Dependencies not installed: `pip install -e .[dev]`
3. Git not configured globally: `git config --global user.email "test@example.com"`

## Repository-Specific Notes

- The main branch is `main` (not `master`)
- Template URL is hardcoded to `https://github.com/rdwj/mcp-server-template`
- Package name on PyPI: `fips-agents-cli`
- Command name: `fips-agents` (no `-cli` suffix)
- Recommended installation: `pipx install fips-agents-cli`
