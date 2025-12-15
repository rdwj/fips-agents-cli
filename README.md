# FIPS Agents CLI

A command-line tool for creating and managing FIPS-compliant AI agent projects, with a focus on MCP (Model Context Protocol) server development.

## Features

- 🚀 Quick project scaffolding from templates
- 📦 MCP server project generation
- 🔧 Automatic project customization
- ⚡ Component generation (tools, resources, prompts, middleware)
- 🎨 Beautiful CLI output with Rich
- ✅ Git repository initialization
- 🧪 Comprehensive test coverage with auto-run

## Installation

**Recommended:** Install with [pipx](https://pipx.pypa.io/) for isolated command-line tools:

```bash
pipx install fips-agents-cli
```

pipx installs the CLI in an isolated environment while making it globally available. This prevents dependency conflicts with other Python packages.

<details>
<summary><b>Alternative: Using pip</b></summary>

If you prefer pip or don't have pipx installed:

```bash
pip install fips-agents-cli
```

**Note:** Consider using a virtual environment to avoid dependency conflicts.

</details>

<details>
<summary><b>Alternative: Install from source (for development)</b></summary>

For contributing or local development:

```bash
# Clone the repository
git clone https://github.com/rdwj/fips-agents-cli.git
cd fips-agents-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e .[dev]
```

</details>

## Quick Start

### Create a new MCP server project

```bash
fips-agents create mcp-server my-awesome-server
```

This will:
1. Clone the MCP server template
2. Customize the project with your chosen name
3. Initialize a git repository
4. Provide next steps for development

### Specify a target directory

```bash
fips-agents create mcp-server my-server --target-dir ~/projects
```

### Skip git initialization

```bash
fips-agents create mcp-server my-server --no-git
```

### Generate components in an existing project

```bash
# Navigate to your MCP server project
cd my-mcp-server

# Generate a new tool
fips-agents generate tool search_documents --description "Search through documents"

# Generate a resource
fips-agents generate resource config_data --description "Application configuration"

# Generate a prompt
fips-agents generate prompt code_review --description "Review code for best practices"

# Generate middleware
fips-agents generate middleware auth_middleware --description "Authentication middleware"
```

## Usage

### Basic Commands

```bash
# Display version
fips-agents --version

# Get help
fips-agents --help
fips-agents create --help
fips-agents create mcp-server --help
fips-agents generate --help
fips-agents generate tool --help
```

### Create MCP Server

```bash
fips-agents create mcp-server <project-name> [OPTIONS]
```

**Arguments:**
- `project-name`: Name for your MCP server project (must start with lowercase letter, contain only lowercase letters, numbers, hyphens, and underscores)

**Options:**
- `--target-dir, -t PATH`: Target directory for the project (default: current directory)
- `--no-git`: Skip git repository initialization
- `--help`: Show help message

**Examples:**

```bash
# Create in current directory
fips-agents create mcp-server my-mcp-server

# Create in specific directory
fips-agents create mcp-server my-server -t ~/projects

# Create without git initialization
fips-agents create mcp-server my-server --no-git
```

### Generate Components

The `generate` command group allows you to scaffold MCP components (tools, resources, prompts, middleware) in existing MCP server projects.

**Important**: Run these commands from within your MCP server project directory.

#### Generate Tool

```bash
fips-agents generate tool <name> [OPTIONS]
```

**Arguments:**
- `name`: Tool name in snake_case (e.g., `search_documents`, `fetch_data`)

**Options:**
- `--description, -d TEXT`: Tool description
- `--async/--sync`: Generate async or sync function (default: async)
- `--with-context`: Include FastMCP Context parameter
- `--with-auth`: Include authentication decorator
- `--params PATH`: JSON file with parameter definitions
- `--read-only`: Mark as read-only operation (default: true)
- `--idempotent`: Mark as idempotent (default: true)
- `--open-world`: Mark as open-world operation
- `--return-type TEXT`: Return type annotation (default: str)
- `--dry-run`: Show what would be generated without creating files

**Examples:**

```bash
# Basic tool generation
fips-agents generate tool search_documents --description "Search through documents"

# Tool with context and authentication
fips-agents generate tool fetch_user_data --description "Fetch user data" --with-context --with-auth

# Tool with parameters from JSON file
fips-agents generate tool advanced_search --params params.json

# Sync tool with custom return type
fips-agents generate tool process_data --sync --return-type "dict[str, Any]"

# Dry run to preview
fips-agents generate tool test_tool --description "Test" --dry-run
```

#### Generate Resource

```bash
fips-agents generate resource <name> [OPTIONS]
```

**Arguments:**
- `name`: Resource name in snake_case (e.g., `config_data`, `user_profile`)

**Options:**
- `--description, -d TEXT`: Resource description
- `--async/--sync`: Generate async or sync function (default: async)
- `--with-context`: Include FastMCP Context parameter
- `--uri TEXT`: Resource URI (default: `resource://<name>`)
- `--mime-type TEXT`: MIME type for resource (default: text/plain)
- `--dry-run`: Show what would be generated without creating files

**Examples:**

```bash
# Basic resource
fips-agents generate resource config_data --description "Application configuration"

# Resource with custom URI
fips-agents generate resource user_profile --uri "resource://users/{id}" --description "User profile data"

# Resource with specific MIME type
fips-agents generate resource json_config --mime-type "application/json"
```

#### Generate Prompt

```bash
fips-agents generate prompt <name> [OPTIONS]
```

**Arguments:**
- `name`: Prompt name in snake_case (e.g., `code_review`, `summarize_text`)

**Options:**
- `--description, -d TEXT`: Prompt description
- `--params PATH`: JSON file with parameter definitions
- `--with-schema`: Include JSON schema in prompt
- `--dry-run`: Show what would be generated without creating files

**Examples:**

```bash
# Basic prompt
fips-agents generate prompt code_review --description "Review code for best practices"

# Prompt with parameters
fips-agents generate prompt summarize_text --params params.json --with-schema
```

#### Generate Middleware

```bash
fips-agents generate middleware <name> [OPTIONS]
```

**Arguments:**
- `name`: Middleware name in snake_case (e.g., `auth_middleware`, `rate_limiter`)

**Options:**
- `--description, -d TEXT`: Middleware description
- `--async/--sync`: Generate async or sync function (default: async)
- `--dry-run`: Show what would be generated without creating files

**Examples:**

```bash
# Basic middleware
fips-agents generate middleware auth_middleware --description "Authentication middleware"

# Sync middleware
fips-agents generate middleware rate_limiter --sync --description "Rate limiting middleware"
```

#### Parameters JSON Schema

When using `--params` flag, provide a JSON file with parameter definitions:

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
- `list[str]`, `list[int]`, `list[float]`
- `Optional[str]`, `Optional[int]`, `Optional[float]`, `Optional[bool]`

**Pydantic Field Constraints:**
- `min_length`, `max_length` (for strings)
- `ge`, `le`, `gt`, `lt` (for numbers)
- `pattern` (for regex validation on strings)
- `default` (default value when optional)

## Project Name Requirements

Project names must follow these rules:
- Start with a lowercase letter
- Contain only lowercase letters, numbers, hyphens (`-`), and underscores (`_`)
- Not be empty

**Valid examples:** `my-server`, `test_mcp`, `server123`, `my-awesome-mcp-server`

**Invalid examples:** `MyServer` (uppercase), `123server` (starts with number), `my@server` (special characters)

## After Creating a Project

Once your project is created, follow these steps:

```bash
# 1. Navigate to your project
cd my-mcp-server

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install the project
pip install -e .[dev]

# 4. Run tests
pytest

# 5. Start developing!
# Edit src/my_mcp_server/ files to add your functionality
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/rdwj/fips-agents-cli.git
cd fips-agents-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=fips_agents_cli --cov-report=html

# Run specific test file
pytest tests/test_create.py

# Run specific test
pytest tests/test_create.py::TestCreateMcpServer::test_successful_creation
```

### Code Quality

```bash
# Format code with Black
black src tests

# Lint with Ruff
ruff check src tests

# Type checking (if using mypy)
mypy src
```

### Project Structure

```
fips-agents-cli/
├── pyproject.toml          # Project configuration
├── README.md               # This file
├── src/
│   └── fips_agents_cli/
│       ├── __init__.py     # Package initialization
│       ├── __main__.py     # Entry point for python -m
│       ├── cli.py          # Main CLI application
│       ├── version.py      # Version information
│       ├── commands/       # CLI command implementations
│       │   ├── __init__.py
│       │   └── create.py   # Create command
│       └── tools/          # Utility modules
│           ├── __init__.py
│           ├── filesystem.py  # Filesystem operations
│           ├── git.py         # Git operations
│           └── project.py     # Project customization
└── tests/                  # Test suite
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── test_create.py      # Create command tests
    ├── test_filesystem.py  # Filesystem utilities tests
    └── test_project.py     # Project utilities tests
```

## Requirements

- Python 3.10 or higher
- Git (for cloning templates and initializing repositories)

## Dependencies

- **click** (>=8.1.0): Command-line interface creation
- **rich** (>=13.0.0): Terminal output formatting
- **gitpython** (>=3.1.0): Git operations
- **tomlkit** (>=0.12.0): TOML file manipulation
- **jinja2** (>=3.1.2): Template rendering for component generation

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Format code (`black src tests`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Troubleshooting

### Git not found

If you see "Git is not installed" error:
- **macOS**: `brew install git`
- **Linux**: `sudo apt-get install git` or `sudo yum install git`
- **Windows**: Download from https://git-scm.com/downloads

### Directory already exists

If you see "Directory already exists" error:
- Choose a different project name
- Remove the existing directory: `rm -rf project-name`
- Use a different target directory with `--target-dir`

### Template clone fails

If template cloning fails:
- Check your internet connection
- Verify the template repository is accessible: https://github.com/rdwj/mcp-server-template
- Try again later if GitHub is experiencing issues

### "Not in an MCP server project directory"

When using `generate` commands:
- Ensure you're running the command from within an MCP server project
- Check that `pyproject.toml` exists with `fastmcp` dependency
- If the project wasn't created with `fips-agents create mcp-server`, generator templates may be missing

### "Component already exists"

If you see this error:
- Choose a different component name
- Manually remove the existing component file from `src/<component-type>/`
- Check the component type directory for existing files

### Invalid component name

Component names must:
- Be valid Python identifiers (snake_case)
- Not be Python keywords (`for`, `class`, etc.)
- Start with a letter or underscore
- Contain only letters, numbers, and underscores

## License

MIT License - see LICENSE file for details

## Links

- **Repository**: https://github.com/rdwj/fips-agents-cli
- **Issues**: https://github.com/rdwj/fips-agents-cli/issues
- **MCP Protocol**: https://modelcontextprotocol.io/

## Changelog

### Version 0.2.0

- Feature: GitHub integration for `create mcp-server` command
- Feature: New `--github` flag to create GitHub repository and push code
- Feature: New `--local` flag to skip GitHub and create local-only project
- Feature: Non-interactive mode (`--yes`) for agent/CI workflows
- Feature: New `--private` flag to create private GitHub repositories
- Feature: New `--org` option to create repositories in GitHub organizations
- Feature: New `--description` option for GitHub repository descriptions
- Feature: New `--remote-only` flag to create GitHub repo without local clone
- Feature: Added missing `patch build` subcommand for updating build/deployment files
- Feature: GitHub metadata tracking in `.template-info` file
- Feature: New git utilities for remote management (`add_remote`, `push_to_remote`)
- Improvement: Auto-detects `gh` CLI and prompts user when available
- Improvement: Clean git history - customizes project before initial push

### Version 0.1.9

- Feature: Added `.fips-agents-cli` directory to ModelCar projects with generation metadata
- Feature: ModelCar projects now include `info.json` with source, destination, and generator info
- Feature: ModelCar projects now include `CLAUDE.md` with project-specific Claude Code instructions
- Improvement: Consistent project metadata structure between MCP server and ModelCar projects

### Version 0.1.8

- Feature: Added GitHub Copilot agent template support
- Feature: Added `model-car` command for creating model car projects
- Fix: Subdirectory names now convert hyphens to underscores for valid Python package names
- Fix: Added `module_path` template variable for proper import paths in subdirectory components
- Fix: Script generator improvements
- Improvement: Removed download filter for cleaner template handling
- Improvement: Added info file tracking for generated projects

### Version 0.1.7

- **Critical Fix**: Resource generator now automatically extracts URI template parameters (e.g., `{country_code}`, `{id}`) and adds them to function signature
- **Critical Fix**: Generated resources now comply with FastMCP requirement that URI parameters must match function arguments
- Fix: Updated test templates to use `.fn` attribute pattern for testing FastMCP decorated functions
- Fix: Improved `component_exists()` to properly handle subdirectory paths
- Fix: Removed obsolete `_preview_prompt_utility.py` from template (YAML-based prompts removed)
- Improvement: Generated resource tests now pass out of the box
- Improvement: Resource function signatures now include proper type hints and docstring Args sections

### Version 0.1.6

- Feature: Added `fips-agents patch` command for selective template updates without losing custom code
- Feature: Resource subdirectory support - organize resources in hierarchies (e.g., `country-profiles/japan`)
- Feature: `generate resource` now supports subdirectory paths for better organization
- Improvement: Recursive resource loading from subdirectories with automatic discovery
- Improvement: Patch command shows interactive diffs for files that may be customized
- Improvement: Template version tracking enables smart updates via `.template-info` file
- Enhancement: Cleaned up redundant auto-discovery code from template `__init__.py` files

### Version 0.1.5

- Feature: Added `.template-info` file to track CLI version and template commit hash in generated projects
- Improvement: Implemented auto-discovery for tools/resources/prompts/middleware components, eliminating manual registration in `__init__.py` files
- Improvement: Template components can now be added or removed by simply creating/deleting files—no registry updates required

### Version 0.1.4

- Fix: Fixed Containerfile in template to remove incorrect prompts/ copy line
- Fix: Fixed CLI to correctly update entry point script names for new projects
- Fix: Updated CLI to handle new multi-module template structure (core/, tools/, etc.)
- Fix: Updated fallback project name to match current template (fastmcp-unified-template)
- Improvement: Improved messaging when template uses multi-module structure

### Version 0.1.3

- Improvement: Enhanced prompt creation to comply with FastMCP 2.9+ requirements

### Version 0.1.2

- Documentation: Updated documentation and improved release management guidance
- Automation: Added `/create-release` slash command for automated release workflow
- Automation: Created `scripts/release.sh` for streamlined version management and tagging
- Documentation: Added `RELEASE_CHECKLIST.md` with comprehensive release procedures

### Version 0.1.1

- Added `fips-agents generate` command group
- Component generation: tools, resources, prompts, middleware
- Jinja2-based template rendering
- Parameter validation and JSON schema support
- Auto-run pytest on generated components
- Dry-run mode for previewing changes
- Comprehensive error handling and validation

### Version 0.1.0 (MVP)

- Initial release
- `fips-agents create mcp-server` command
- Template cloning and customization
- Git repository initialization
- Comprehensive test suite
- Beautiful CLI output with Rich
