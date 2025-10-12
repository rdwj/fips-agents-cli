# FIPS Agents CLI

A command-line tool for creating and managing FIPS-compliant AI agent projects, with a focus on MCP (Model Context Protocol) server development.

## Features

- 🚀 Quick project scaffolding from templates
- 📦 MCP server project generation
- 🔧 Automatic project customization
- 🎨 Beautiful CLI output with Rich
- ✅ Git repository initialization
- 🧪 Comprehensive test coverage

## Installation

### Using pipx (Recommended)

```bash
pipx install fips-agents-cli
```

### Using pip

```bash
pip install fips-agents-cli
```

### From Source (Development)

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

## Usage

### Basic Commands

```bash
# Display version
fips-agents --version

# Get help
fips-agents --help
fips-agents create --help
fips-agents create mcp-server --help
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

- Python 3.9 or higher
- Git (for cloning templates and initializing repositories)

## Dependencies

- **click** (>=8.1.0): Command-line interface creation
- **rich** (>=13.0.0): Terminal output formatting
- **gitpython** (>=3.1.0): Git operations
- **tomlkit** (>=0.12.0): TOML file manipulation

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

## License

MIT License - see LICENSE file for details

## Links

- **Repository**: https://github.com/rdwj/fips-agents-cli
- **Issues**: https://github.com/rdwj/fips-agents-cli/issues
- **MCP Protocol**: https://modelcontextprotocol.io/

## Changelog

### Version 0.1.0 (MVP)

- Initial release
- `fips-agents create mcp-server` command
- Template cloning and customization
- Git repository initialization
- Comprehensive test suite
- Beautiful CLI output with Rich
