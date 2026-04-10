# FIPS Agents CLI - MVP Plan (Revised)

**Date:** October 11, 2025
**Package Name:** `fips-agents-cli`
**Command:** `fips-agents`
**Distribution:** pipx (Python)

---

## MVP Scope (Laser Focused)

### What's In MVP

**Single Feature:** Create MCP server from template

```bash
fips-agents create mcp-server my-server
```

**What This Does:**
1. Clone your mcp-server-template from GitHub
2. Rename project appropriately (my-server)
3. Update pyproject.toml with new project name
4. Copy generator templates to `.fips-agents-cli/generators/`
5. Initialize git repository
6. Provide next steps to user

**That's it.** No generate command in MVP. Just get the create flow rock solid.

### What's NOT In MVP

- ❌ Generate tool command (Phase 2)
- ❌ Generate prompt command (Phase 2)
- ❌ Generate resource command (Phase 2)
- ❌ Interactive prompts (Phase 2)
- ❌ Template registry (Phase 2)
- ❌ Multiple templates (Phase 2)
- ❌ Cache system (Phase 2)
- ❌ Environment check command (Phase 2)

---

## Technology Stack

### Confirmed Choices

**Core:**
- Python 3.11+ (required)
- pipx for distribution
- Click for CLI framework
- Rich for terminal output
- GitPython for git operations

**Template Engine (Phase 2):**
- Jinja2 for templates
- PyYAML for configuration

**Build/Distribution:**
- Hatch for build system
- PyPI for distribution
- GitHub Actions for CI/CD

---

## Command Structure

### Confirmed Pattern

```bash
# Main command
fips-agents create mcp-server <project-name>

# Aliases for convenience
fips-agents create mcp-server <name>
fips-agents c mcp-server <name>         # Short alias

# Future (Phase 2+)
fips-agents generate tool <name>
fips-agents g tool <name>               # Short alias
```

---

## Project Structure (MVP)

### CLI Project (fips-agents-cli)

```
fips-agents-cli/
├── pyproject.toml              # Hatch-based config
├── README.md
├── LICENSE
├── src/
│   └── fips_agents_cli/
│       ├── __init__.py
│       ├── __main__.py        # python -m fips_agents_cli
│       ├── cli.py             # Main Click entry point
│       ├── version.py         # Version info
│       │
│       ├── commands/
│       │   ├── __init__.py
│       │   └── create.py      # MVP: just create command
│       │
│       └── tools/
│           ├── __init__.py
│           ├── git.py         # Git clone/init operations
│           ├── filesystem.py  # File operations
│           └── project.py     # Project customization
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_create.py
│
└── .github/
    └── workflows/
        └── test.yml
```

### Generated Project Structure (After Create)

```
my-server/                      # Created by user
├── .git/                       # Git initialized
├── .fips-agents-cli/           # Generator templates (copied from template)
│   └── generators/
│       ├── tool/
│       │   ├── template.yaml
│       │   ├── tool.py.j2
│       │   └── test_tool.py.j2
│       ├── prompt/
│       │   └── prompt.yaml.j2
│       └── resource/
│           ├── resource.py.j2
│           └── test_resource.py.j2
│
├── src/
│   └── my_server/              # Renamed from template
│       ├── __init__.py
│       ├── server.py
│       └── tools/
│           └── __init__.py
│
├── prompts/
├── resources/
├── tests/
├── pyproject.toml              # Updated with project name
├── README.md
├── Containerfile
└── .gitignore
```

**Key Point:** `.fips-agents-cli/generators/` is part of YOUR template repo, not bundled in the CLI. The CLI just clones and preserves it.

---

## MVP Implementation Steps

### Step 1: Project Setup (Day 1)

**Create project:**
```bash
cd /Users/wjackson/Developer/AGENTS/fips-agents-cli
mkdir -p src/fips_agents_cli/{commands,tools}
mkdir -p tests
```

**Create pyproject.toml:**
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "fips-agents-cli"
version = "0.1.0"
description = "CLI for scaffolding AI agent projects"
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"},
]
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "gitpython>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[project.scripts]
fips-agents = "fips_agents_cli.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/fips_agents_cli"]
```

**Test installation:**
```bash
pip install -e .
fips-agents --version
```

### Step 2: Basic CLI Framework (Day 1)

**File: `src/fips_agents_cli/version.py`**
```python
"""Version information."""
__version__ = "0.1.0"
```

**File: `src/fips_agents_cli/cli.py`**
```python
"""Main CLI entry point."""
import click
from rich.console import Console

from fips_agents_cli.version import __version__
from fips_agents_cli.commands.create import create

console = Console()


@click.group()
@click.version_option(version=__version__, prog_name="fips-agents")
def cli():
    """FIPS Agents CLI - Scaffolding for AI agent projects."""
    pass


# Register commands
cli.add_command(create)


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
```

**Test:**
```bash
fips-agents --version
fips-agents --help
```

### Step 3: Create Command Structure (Day 2)

**File: `src/fips_agents_cli/commands/create.py`**
```python
"""Create command for scaffolding new projects."""
import click
from rich.console import Console

console = Console()


@click.group()
def create():
    """Create a new project from a template."""
    pass


@create.command("mcp-server")
@click.argument("project_name")
@click.option(
    "--target-dir",
    default=".",
    help="Directory where the project will be created",
)
def mcp_server(project_name: str, target_dir: str):
    """Create a new MCP server project.

    Example:
        fips-agents create mcp-server my-server
    """
    console.print(f"[bold green]Creating MCP server:[/bold green] {project_name}")
    console.print(f"[dim]Target directory:[/dim] {target_dir}")

    # TODO: Implement actual logic
    console.print("[yellow]⚠ Not implemented yet[/yellow]")
```

**Test:**
```bash
fips-agents create mcp-server test-server
```

### Step 4: Git Operations (Day 2)

**File: `src/fips_agents_cli/tools/git.py`**
```python
"""Git operations for cloning and initializing repositories."""
from pathlib import Path
from typing import Optional
import git
from rich.console import Console

console = Console()


def clone_template(
    repo_url: str,
    target_path: Path,
    branch: str = "main",
) -> bool:
    """Clone a git repository to a target path.

    Args:
        repo_url: URL of the git repository
        target_path: Path where to clone the repository
        branch: Branch to clone (default: main)

    Returns:
        True if successful, False otherwise
    """
    try:
        console.print(f"[dim]Cloning from {repo_url}...[/dim]")
        git.Repo.clone_from(
            repo_url,
            target_path,
            branch=branch,
            depth=1,  # Shallow clone for speed
        )

        # Remove .git directory from template
        git_dir = target_path / ".git"
        if git_dir.exists():
            import shutil
            shutil.rmtree(git_dir)

        return True
    except Exception as e:
        console.print(f"[red]✗ Clone failed: {e}[/red]")
        return False


def init_repository(project_path: Path, initial_commit: bool = True) -> bool:
    """Initialize a new git repository.

    Args:
        project_path: Path to the project
        initial_commit: Whether to create an initial commit

    Returns:
        True if successful, False otherwise
    """
    try:
        repo = git.Repo.init(project_path)

        if initial_commit:
            repo.index.add("*")
            repo.index.commit("Initial commit from fips-agents-cli")

        return True
    except Exception as e:
        console.print(f"[red]✗ Git init failed: {e}[/red]")
        return False
```

### Step 5: Project Customization (Day 3)

**File: `src/fips_agents_cli/tools/project.py`**
```python
"""Project customization utilities."""
from pathlib import Path
import re
import toml
from rich.console import Console

console = Console()


def update_project_name(project_path: Path, new_name: str) -> bool:
    """Update project name in pyproject.toml and other files.

    Args:
        project_path: Path to the project
        new_name: New project name

    Returns:
        True if successful, False otherwise
    """
    try:
        # Update pyproject.toml
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "r") as f:
                config = toml.load(f)

            # Update project name
            if "project" in config:
                config["project"]["name"] = new_name

            with open(pyproject_path, "w") as f:
                toml.dump(config, f)

            console.print(f"[dim]✓ Updated pyproject.toml[/dim]")

        # Rename source directory
        src_path = project_path / "src"
        if src_path.exists():
            # Find the old module name
            for old_module in src_path.iterdir():
                if old_module.is_dir() and not old_module.name.startswith("."):
                    # Rename to new project name (with underscores)
                    new_module_name = new_name.replace("-", "_")
                    new_module_path = src_path / new_module_name

                    if old_module != new_module_path:
                        old_module.rename(new_module_path)
                        console.print(f"[dim]✓ Renamed module: {old_module.name} → {new_module_name}[/dim]")
                    break

        return True
    except Exception as e:
        console.print(f"[red]✗ Project customization failed: {e}[/red]")
        return False


def validate_project_name(name: str) -> bool:
    """Validate project name follows Python package naming conventions.

    Args:
        name: Project name to validate

    Returns:
        True if valid, False otherwise
    """
    # Must start with letter, contain only letters, numbers, hyphens, underscores
    pattern = r"^[a-z][a-z0-9\-_]*$"
    return bool(re.match(pattern, name.lower()))
```

### Step 6: Wire It All Together (Day 3)

**Update `src/fips_agents_cli/commands/create.py`:**
```python
"""Create command for scaffolding new projects."""
from pathlib import Path
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from fips_agents_cli.tools.git import clone_template, init_repository
from fips_agents_cli.tools.project import update_project_name, validate_project_name

console = Console()

# Template repository URL
MCP_SERVER_TEMPLATE_URL = "https://github.com/rdwj/mcp-server-template"


@click.group()
def create():
    """Create a new project from a template."""
    pass


@create.command("mcp-server")
@click.argument("project_name")
@click.option(
    "--target-dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory where the project will be created",
)
def mcp_server(project_name: str, target_dir: Path):
    """Create a new MCP server project.

    Example:
        fips-agents create mcp-server my-server
    """
    # Validate project name
    if not validate_project_name(project_name):
        console.print("[red]✗ Invalid project name[/red]")
        console.print("Project name must start with a letter and contain only lowercase letters, numbers, hyphens, and underscores.")
        raise click.Abort()

    # Determine project path
    project_path = target_dir / project_name

    # Check if directory already exists
    if project_path.exists():
        console.print(f"[red]✗ Directory already exists:[/red] {project_path}")
        raise click.Abort()

    console.print(f"\n[bold green]Creating MCP server:[/bold green] {project_name}\n")

    # Step 1: Clone template
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Cloning template repository...", total=None)

        if not clone_template(MCP_SERVER_TEMPLATE_URL, project_path):
            console.print("[red]✗ Failed to clone template[/red]")
            raise click.Abort()

    console.print("[green]✓ Template cloned[/green]")

    # Step 2: Customize project
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Customizing project...", total=None)

        if not update_project_name(project_path, project_name):
            console.print("[yellow]⚠ Warning: Could not fully customize project[/yellow]")

    console.print("[green]✓ Project customized[/green]")

    # Step 3: Initialize git repository
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task(description="Initializing git repository...", total=None)

        if not init_repository(project_path):
            console.print("[yellow]⚠ Warning: Could not initialize git repository[/yellow]")

    console.print("[green]✓ Git repository initialized[/green]")

    # Success message
    console.print(f"\n[bold green]✓ Successfully created:[/bold green] {project_name}")

    # Next steps
    console.print("\n[bold]Next steps:[/bold]")
    console.print(f"  [cyan]cd {project_name}[/cyan]")
    console.print(f"  [cyan]python -m venv venv[/cyan]")
    console.print(f"  [cyan]source venv/bin/activate[/cyan]  # or [cyan]venv\\Scripts\\activate[/cyan] on Windows")
    console.print(f"  [cyan]pip install -e .[/cyan]")
    console.print(f"\n[dim]Generator templates are available in .fips-agents-cli/generators/[/dim]")
```

### Step 7: Testing (Day 4)

**File: `tests/test_create.py`**
```python
"""Tests for create command."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from fips_agents_cli.cli import cli


def test_create_mcp_server(tmp_path):
    """Test creating an MCP server project."""
    runner = CliRunner()

    # Run create command
    result = runner.invoke(
        cli,
        ["create", "mcp-server", "test-server"],
        env={"HOME": str(tmp_path)},
        catch_exceptions=False,
    )

    # Check command succeeded
    assert result.exit_code == 0

    # Check project directory created
    project_path = tmp_path / "test-server"
    assert project_path.exists()

    # Check key files exist
    assert (project_path / "pyproject.toml").exists()
    assert (project_path / "README.md").exists()
    assert (project_path / "src").exists()
    assert (project_path / ".fips-agents-cli" / "generators").exists()

    # Check git initialized
    assert (project_path / ".git").exists()


def test_create_invalid_name():
    """Test creating project with invalid name."""
    runner = CliRunner()

    # Run with invalid name (uppercase)
    result = runner.invoke(cli, ["create", "mcp-server", "MyServer"])

    # Should fail
    assert result.exit_code != 0


def test_create_existing_directory(tmp_path):
    """Test creating project in existing directory."""
    runner = CliRunner()

    # Create directory first
    existing = tmp_path / "existing-server"
    existing.mkdir()

    # Try to create project
    result = runner.invoke(
        cli,
        ["create", "mcp-server", "existing-server"],
        env={"HOME": str(tmp_path)},
    )

    # Should fail
    assert result.exit_code != 0
```

**Run tests:**
```bash
pytest tests/test_create.py -v
pytest tests/test_create.py --cov=fips_agents_cli
```

### Step 8: Documentation (Day 4)

**Update README.md:**
```markdown
# FIPS Agents CLI

Easy scaffolding for AI agent projects.

## Installation

```bash
pipx install fips-agents-cli
```

## Usage

### Create MCP Server

```bash
fips-agents create mcp-server my-server
cd my-server
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
```

## Development

```bash
git clone https://github.com/yourusername/fips-agents-cli
cd fips-agents-cli
pip install -e .[dev]
pytest
```
```

---

## MVP Acceptance Criteria

### Must Have

- [ ] `fips-agents create mcp-server <name>` works
- [ ] Clones from https://github.com/rdwj/mcp-server-template
- [ ] Renames project correctly
- [ ] Updates pyproject.toml with new name
- [ ] Renames source directory (e.g., `template_name` → `my_server`)
- [ ] Preserves `.fips-agents-cli/generators/` from template
- [ ] Initializes git repository with initial commit
- [ ] Shows clear next steps to user
- [ ] Validates project name (lowercase, starts with letter)
- [ ] Fails gracefully if directory exists
- [ ] Works on macOS and Linux (Windows nice-to-have)

### Success Metrics

- [ ] Can create functional MCP server in < 30 seconds
- [ ] Generated project works immediately (no manual fixes)
- [ ] Clear, helpful error messages
- [ ] ≥80% test coverage
- [ ] No linting errors (ruff, black)

---

## Generator Templates (Phase 2 Preview)

**What Will Exist in `.fips-agents-cli/generators/tool/`:**

```
.fips-agents-cli/generators/tool/
├── template.yaml           # Generator configuration
├── tool.py.j2             # Tool implementation template
└── test_tool.py.j2        # Test template
```

**Example `template.yaml`:**
```yaml
name: "MCP Tool Generator"
description: "Generate a new MCP tool"
version: "1.0.0"

# Prompts for user input
prompts:
  - name: tool_name
    type: text
    message: "Tool name (e.g., get_weather)"
    validate: "^[a-z][a-z0-9_]*$"

  - name: tool_description
    type: text
    message: "Brief description of what this tool does"

  - name: output_dir
    type: text
    message: "Output directory (relative to src/{project})"
    default: "tools"

# Files to generate
files:
  - template: "tool.py.j2"
    output: "src/{{ project_name }}/{{ output_dir }}/{{ tool_name }}.py"

  - template: "test_tool.py.j2"
    output: "tests/test_{{ tool_name }}.py"

# Post-generation messages
post_generate:
  - action: "message"
    text: "✓ Generated tool: {{ tool_name }}"
  - action: "message"
    text: "  Location: src/{{ project_name }}/{{ output_dir }}/{{ tool_name }}.py"
```

**This lets users do:**
```bash
cd my-server
fips-agents generate tool get_weather
# Prompts: "Output directory (relative to src/my_server)? [tools]"
# User types: "tools/api"
# Creates: src/my_server/tools/api/get_weather.py
```

**Key Insight:** Like Ignite, the user controls the directory structure. The generator respects their organization.

---

## Discussion Points

### 1. MVP Scope Confirmation

**Proposed MVP:**
- Just `fips-agents create mcp-server <name>`
- No interactive prompts (Phase 2)
- No generate commands (Phase 2)
- Hardcoded template URL

**Questions:**
- Does this narrow scope make sense for MVP?
- Should we add `--yes` flag even in MVP, or wait for Phase 2?
- Any other must-haves for MVP?

### 2. Template Repository Requirements

**What needs to be in your mcp-server-template:**
- `.fips-agents-cli/generators/` directory with:
  - `tool/` subdirectory with templates
  - `prompt/` subdirectory with templates
  - `resource/` subdirectory with templates
- `pyproject.toml` with placeholder name
- Source directory that can be renamed

**Questions:**
- Is your template already structured this way?
- Should we prep the template first, or build CLI and adapt template later?

### 3. Project Name Validation

**Proposed rules:**
- Must start with lowercase letter
- Can contain: lowercase letters, numbers, hyphens, underscores
- No uppercase, no spaces, no special characters

**Examples:**
- ✅ `my-server`
- ✅ `weather_service`
- ✅ `api2`
- ❌ `MyServer` (uppercase)
- ❌ `my server` (space)
- ❌ `_server` (starts with underscore)

**Questions:**
- Do these rules work for you?
- Any other constraints?

### 4. Directory Naming

**Confirmed:** `.fips-agents-cli/` (not `.cli/`)

**Question:** Should this be configurable, or always `.fips-agents-cli/`?

### 5. Error Handling

**Proposed behavior:**
- If git clone fails → clear error, exit cleanly
- If directory exists → error message, suggest different name
- If invalid name → explain rules, examples of valid names
- If can't rename files → warning but continue (project still usable)

**Questions:**
- Should we have a `--force` flag to overwrite existing directories?
- Or keep it strict for MVP?

### 6. Git Initialization

**Proposed behavior:**
- Always initialize git repository
- Always create initial commit: "Initial commit from fips-agents-cli"
- Remove template's .git directory first

**Questions:**
- Should we have a `--no-git` flag?
- Or always initialize for MVP?

### 7. Next Steps Display

**After successful creation, show:**
```
✓ Successfully created: my-server

Next steps:
  cd my-server
  python -m venv venv
  source venv/bin/activate
  pip install -e .

Generator templates are available in .fips-agents-cli/generators/
```

**Questions:**
- Is this helpful?
- Should we add more guidance?
- Should we offer to run these commands automatically?

---

## Implementation Timeline

### MVP Sprint (1 Week)

**Day 1: Setup**
- Create project structure
- Set up pyproject.toml
- Basic CLI framework
- Test installation with pipx

**Day 2: Git Operations**
- Implement clone_template()
- Implement init_repository()
- Test git operations

**Day 3: Project Customization**
- Implement project name validation
- Implement pyproject.toml updates
- Implement directory renaming
- Wire everything together

**Day 4: Testing & Polish**
- Write comprehensive tests
- Add error handling
- Write documentation
- Manual testing with real template

**Day 5: Buffer/Review**
- Address any issues
- Code review
- Prepare for PyPI publishing (optional)

---

## Post-MVP Roadmap Preview

### Phase 2: Generate Command (Week 2)
- Implement `fips-agents generate tool <name>`
- Load generator templates from `.fips-agents-cli/generators/`
- Jinja2 template rendering
- Interactive prompts for parameters
- Directory placement control (like Ignite)

### Phase 3: Additional Generators (Week 3)
- `fips-agents generate prompt <name>`
- `fips-agents generate resource <name>`
- Test all three generator types

### Phase 4: Polish & Distribution (Week 4)
- Interactive prompts for create command
- Cache system
- Template registry
- Publish to PyPI
- Documentation site

---

## Open Questions for Discussion

1. **MVP Scope:** Does the narrowed scope make sense?
2. **Template Prep:** Should we prepare your template repo first?
3. **Validation Rules:** Are the project name rules appropriate?
4. **Error Handling:** Strict or permissive for MVP?
5. **Git Behavior:** Always initialize, or add `--no-git` flag?
6. **Timeline:** Is 1 week realistic for MVP?
7. **Testing:** Should we test with real template during development?

---

## Success Definition

**MVP is successful if:**
1. A developer can run `fips-agents create mcp-server my-server`
2. It clones your template correctly
3. It renames everything appropriately
4. The resulting project is immediately functional
5. The developer can then start adding tools/prompts/resources manually
6. They have generator templates ready for when Phase 2 lands

**We'll know we succeeded when:**
- You can create a new MCP server in < 30 seconds
- The generated project works without any manual fixes
- The experience feels polished and professional
- It saves you significant time vs manual git clone + rename

Ready to discuss and then start building!
