# FIPS Agents CLI - Project Plan

**Date:** October 11, 2025
**Purpose:** Easy way to start and iterate on agentic AI projects
**Initial Focus:** MCP server template scaffolding and code generation

---

## Executive Summary

**Goal:** Build a CLI tool that simplifies creating and iterating on AI agent projects, starting with MCP servers and expanding to full agent workflows.

**Inspiration:** Ignite CLI's approach to scaffolding and code generation, adapted for the AI/agent development ecosystem.

**Technology Stack Decision:** Python-based CLI (aligns with CLAUDE.md preferences and existing ecosystem)

---

## 1. Technology Stack

### Core Technologies

**CLI Framework:**
- **Click** - Command hierarchy and argument parsing
- **Rich** - Beautiful terminal output, progress bars, syntax highlighting
- **Questionary** - Interactive prompts with validation

**Template Engine:**
- **Jinja2** - Template rendering
- **PyYAML** - YAML-based configuration and prompts

**File Operations:**
- **pathlib** - Modern path handling
- **shutil** - File/directory operations
- **gitpython** - Git operations for cloning templates

**Utilities:**
- **httpx** - HTTP client for fetching resources
- **appdirs** - Platform-appropriate cache/config directories
- **tomlkit** - TOML manipulation (for pyproject.toml)

**Distribution:**
- **pipx** - Zero-installation execution
- **PyPI** - Package distribution
- **hatch** or **poetry** - Build system

### Why Python (Not Node.js)?

Based on your CLAUDE.md preferences:
1. Your stack is Python/FastAPI
2. MCP servers are likely FastMCP (Python)
3. Agent frameworks: LangChain/LangGraph (Python)
4. Consistency with existing tooling

**Trade-off:** `pipx` instead of `npx`, but same zero-installation experience.

---

## 2. Command Structure Design

### Proposed Command Patterns

**Option A: Verb-Noun Pattern (Recommended)**
```bash
# Create new projects
fips-agents create mcp-server my-server
fips-agents create agent my-agent
fips-agents create workflow my-workflow

# Generate components
fips-agents generate tool weather-tool
fips-agents generate prompt data-analysis
fips-agents generate resource config-loader

# Utility commands
fips-agents check        # Environment diagnostics
fips-agents list         # List available templates
fips-agents cache clear  # Clear cache
```

**Option B: Noun-Verb Pattern (Alternative)**
```bash
# Create new projects
fips-agents mcp-server create my-server
fips-agents agent create my-agent

# Generate components
fips-agents tool generate weather-tool
fips-agents prompt generate data-analysis
```

**Option C: Hybrid Pattern (Your Original, Adapted)**
```bash
# Create new projects
fips-agents new mcp-server my-server
fips-agents new agent my-agent

# Generate components
fips-agents gen tool weather-tool
fips-agents gen prompt data-analysis
```

**Recommendation:** **Option A** (Verb-Noun)
- Most intuitive for users
- Follows Ignite pattern
- Clear action hierarchy
- Easy to extend

### Command Aliases

Support shortcuts for common operations:
```bash
fips-agents create  →  fips-agents c
fips-agents generate  →  fips-agents g, fips-agents gen
fips-agents check  →  fips-agents doctor
```

### Usage Examples

```bash
# Zero-installation (via pipx)
pipx run fips-agents-cli create mcp-server weather-service

# After installation
pipx install fips-agents-cli
fips-agents create mcp-server weather-service

# With options
fips-agents create mcp-server weather-service \
  --transport http \
  --python-version 3.11 \
  --openshift \
  --yes

# Interactive mode (prompts for options)
fips-agents create mcp-server weather-service

# Generate components
cd weather-service
fips-agents generate tool get-weather
fips-agents generate prompt weather-analysis
fips-agents generate resource config
```

---

## 3. Project Structure

### CLI Project Structure

```
fips-agents-cli/
├── pyproject.toml              # Project metadata and dependencies
├── README.md                   # User documentation
├── LICENSE                     # License file
├── .github/
│   └── workflows/
│       ├── test.yml           # CI pipeline
│       └── release.yml        # Release automation
├── src/
│   └── fips_agents_cli/
│       ├── __init__.py
│       ├── __main__.py        # Entry point for python -m
│       ├── cli.py             # Main CLI entry point
│       ├── version.py         # Version info
│       │
│       ├── commands/          # Command implementations
│       │   ├── __init__.py
│       │   ├── create.py      # Create new projects
│       │   ├── generate.py    # Generate components
│       │   ├── check.py       # Environment check
│       │   ├── list.py        # List templates
│       │   └── cache.py       # Cache management
│       │
│       ├── tools/             # Reusable utilities
│       │   ├── __init__.py
│       │   ├── git.py         # Git operations (clone, etc.)
│       │   ├── templates.py   # Template rendering
│       │   ├── filesystem.py  # File operations
│       │   ├── validation.py  # Input validation
│       │   └── prompts.py     # Interactive prompts
│       │
│       ├── templates/         # Built-in template definitions
│       │   ├── __init__.py
│       │   └── registry.yaml  # Template registry
│       │
│       └── config/            # Configuration
│           ├── __init__.py
│           ├── defaults.py    # Default values
│           └── cache.py       # Cache management
│
├── tests/                     # Test suite
│   ├── __init__.py
│   ├── conftest.py           # Pytest fixtures
│   ├── test_create.py
│   ├── test_generate.py
│   ├── test_git.py
│   └── integration/          # Integration tests
│       └── test_full_workflow.py
│
└── docs/                      # Documentation
    ├── commands.md           # Command reference
    ├── templates.md          # Template system
    └── development.md        # Development guide
```

### Generated Project Structure (MCP Server)

After running `fips-agents create mcp-server weather-service`:

```
weather-service/
├── pyproject.toml
├── README.md
├── Containerfile              # Podman/OpenShift
├── .gitignore
├── .python-version           # pyenv version pinning
│
├── src/
│   └── weather_service/
│       ├── __init__.py
│       ├── server.py         # FastMCP server
│       └── tools/            # MCP tools
│           └── __init__.py
│
├── prompts/                  # YAML prompts (per CLAUDE.md)
│   └── README.md
│
├── resources/                # MCP resources
│   └── README.md
│
├── tests/
│   ├── __init__.py
│   └── test_server.py
│
├── manifests/                # OpenShift manifests (optional)
│   ├── base/
│   │   ├── kustomization.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── overlays/
│       ├── dev/
│       ├── staging/
│       └── production/
│
└── .cli/                     # CLI generator templates
    ├── config.yaml           # Project-specific CLI config
    └── generators/           # Copied from fips-agents-cli
        ├── tool/
        │   ├── template.yaml
        │   └── tool.py.j2
        ├── prompt/
        │   └── prompt.yaml.j2
        └── resource/
            └── resource.py.j2
```

---

## 4. Template System Architecture

### Template Registry

**`templates/registry.yaml`** in the CLI:

```yaml
templates:
  mcp-server:
    name: "MCP Server"
    description: "FastMCP server with tools, prompts, and resources"
    repository: "https://github.com/rdwj/mcp-server-template"
    branch: "main"
    type: "project"
    tags:
      - mcp
      - server
      - fastmcp

  agent:
    name: "LangGraph Agent"
    description: "LangGraph-based agent with workflow"
    repository: "https://github.com/rdwj/agent-template"
    branch: "main"
    type: "project"
    tags:
      - agent
      - langgraph
      - workflow

  workflow:
    name: "Standalone Workflow"
    description: "LangGraph workflow without full agent scaffolding"
    repository: "https://github.com/rdwj/workflow-template"
    branch: "main"
    type: "project"
    tags:
      - workflow
      - langgraph
```

### Generator Templates

**In the generated project: `.cli/generators/tool/template.yaml`**

```yaml
name: "MCP Tool Generator"
description: "Generate a new MCP tool"
version: "1.0.0"

prompts:
  - name: tool_name
    type: text
    message: "Tool name (e.g., get_weather)"
    validate: "^[a-z][a-z0-9_]*$"

  - name: tool_description
    type: text
    message: "Tool description"
    required: true

  - name: has_parameters
    type: confirm
    message: "Does this tool accept parameters?"
    default: true

files:
  - template: "tool.py.j2"
    output: "src/{{ project_name }}/tools/{{ tool_name }}.py"

  - template: "test_tool.py.j2"
    output: "tests/test_{{ tool_name }}.py"

post_generate:
  - action: "message"
    text: "✓ Generated tool: {{ tool_name }}"
  - action: "message"
    text: "Next steps:"
  - action: "message"
    text: "  1. Implement tool logic in src/{{ project_name }}/tools/{{ tool_name }}.py"
  - action: "message"
    text: "  2. Register tool in src/{{ project_name }}/server.py"
  - action: "message"
    text: "  3. Run tests: pytest tests/test_{{ tool_name }}.py"
```

### Jinja2 Template Example

**`.cli/generators/tool/tool.py.j2`**

```python
"""{{ tool_description }}"""
from typing import Any, Dict
from fastmcp import Context

{% if has_parameters %}
async def {{ tool_name }}(
    context: Context,
    {% for param in parameters %}
    {{ param.name }}: {{ param.type }},
    {% endfor %}
) -> Dict[str, Any]:
    """
    {{ tool_description }}

    Args:
    {% for param in parameters %}
        {{ param.name }}: {{ param.description }}
    {% endfor %}

    Returns:
        Dict containing the tool result
    """
    # TODO: Implement tool logic
    return {
        "status": "success",
        "message": "{{ tool_name }} executed"
    }
{% else %}
async def {{ tool_name }}(context: Context) -> Dict[str, Any]:
    """
    {{ tool_description }}

    Returns:
        Dict containing the tool result
    """
    # TODO: Implement tool logic
    return {
        "status": "success",
        "message": "{{ tool_name }} executed"
    }
{% endif %}
```

---

## 5. Implementation Roadmap

### Phase 1: MVP - Create Command (Week 1-2)

**Goal:** Basic project creation from git templates

**Features:**
- ✅ CLI framework setup (Click + Rich)
- ✅ `fips-agents create mcp-server <name>` command
- ✅ Git clone template repository
- ✅ Project name validation
- ✅ Directory structure verification
- ✅ Basic error handling

**Deliverables:**
- Working `create` command
- Can clone mcp-server-template
- Basic terminal output with Rich
- Initial tests

**Commands Available:**
```bash
fips-agents create mcp-server my-server
fips-agents create mcp-server my-server --yes  # Non-interactive
```

### Phase 2: Interactive Prompts & Options (Week 3)

**Goal:** Rich user experience with prompts and configuration

**Features:**
- ✅ Interactive prompts (Questionary)
- ✅ Configuration options:
  - Python version (3.11, 3.12)
  - Transport type (stdio, http)
  - OpenShift manifests (yes/no)
  - FIPS mode (yes/no)
- ✅ `--yes` flag for non-interactive mode
- ✅ Progress indicators (spinners)
- ✅ Better error messages

**Commands Available:**
```bash
# Interactive
fips-agents create mcp-server my-server

# Non-interactive with options
fips-agents create mcp-server my-server \
  --python-version 3.11 \
  --transport http \
  --openshift \
  --fips \
  --yes
```

### Phase 3: Generate Command - Tools (Week 4)

**Goal:** Generate components within projects

**Features:**
- ✅ `fips-agents generate tool <name>` command
- ✅ Load generator templates from `.cli/generators/`
- ✅ Jinja2 template rendering
- ✅ Variable substitution
- ✅ File creation
- ✅ Copy generators into new projects during creation

**Commands Available:**
```bash
cd my-server
fips-agents generate tool get_weather
fips-agents generate tool search_documents --async
```

### Phase 4: Generate Command - Prompts & Resources (Week 5)

**Goal:** Complete MCP server component generation

**Features:**
- ✅ `fips-agents generate prompt <name>` command
- ✅ `fips-agents generate resource <name>` command
- ✅ YAML prompt templates
- ✅ Resource scaffolding

**Commands Available:**
```bash
fips-agents generate prompt data-analysis
fips-agents generate resource config-loader
```

### Phase 5: Template Registry & Cache (Week 6)

**Goal:** Multiple templates and performance optimization

**Features:**
- ✅ Template registry system
- ✅ `fips-agents list` command (show available templates)
- ✅ Local template caching
- ✅ `fips-agents cache clear` command
- ✅ Custom template repositories

**Commands Available:**
```bash
fips-agents list                    # List all templates
fips-agents list --tags mcp         # Filter by tag
fips-agents cache clear             # Clear template cache
fips-agents create agent my-agent   # Use different template
```

### Phase 6: Environment Check & Diagnostics (Week 7)

**Goal:** Help users debug their environment

**Features:**
- ✅ `fips-agents check` command
- ✅ Verify Python version
- ✅ Check for required tools (git, podman, oc)
- ✅ FIPS mode detection
- ✅ OpenShift connection test

**Commands Available:**
```bash
fips-agents check
fips-agents doctor  # Alias
```

### Phase 7: Testing & Documentation (Week 8)

**Goal:** Production-ready release

**Features:**
- ✅ Comprehensive test suite
- ✅ Integration tests
- ✅ Documentation site
- ✅ Example projects
- ✅ Tutorial walkthrough

**Deliverables:**
- ≥80% test coverage
- Complete documentation
- Published to PyPI
- CI/CD pipeline

---

## 6. Future Roadmap (Post-MVP)

### Phase 8: Agent Templates (Weeks 9-10)

**New Templates:**
- LangGraph agent template
- LlamaStack agent template
- Multi-agent system template

**New Commands:**
```bash
fips-agents create agent my-agent
fips-agents create multi-agent my-system
fips-agents generate node decision-node
fips-agents generate edge conditional-edge
```

### Phase 9: Workflow Generation (Weeks 11-12)

**Features:**
- Workflow scaffolding
- Node generation
- Edge configuration
- State management

**New Commands:**
```bash
fips-agents create workflow order-processing
fips-agents generate node validate-order
fips-agents generate node process-payment
fips-agents generate edge success-path
```

### Phase 10: OpenShift Integration (Weeks 13-14)

**Features:**
- Deploy to OpenShift
- Manifest generation
- Kustomize overlays
- ArgoCD integration

**New Commands:**
```bash
fips-agents deploy
fips-agents deploy --namespace my-agents --env production
fips-agents logs my-server
fips-agents status
fips-agents scale --replicas 3
```

### Phase 11: Advanced Generators (Weeks 15-16)

**Features:**
- Local (non-MCP) tools
- Custom agent types
- Integration with external APIs
- Batch generation

**New Commands:**
```bash
fips-agents generate local-tool my-tool
fips-agents generate api-integration weather-api
fips-agents generate batch --from schema.yaml
```

### Phase 12: Plugin System (Weeks 17-18)

**Features:**
- Third-party template plugins
- Custom generator plugins
- Template marketplace

**New Commands:**
```bash
fips-agents plugin install company-templates
fips-agents plugin list
fips-agents create company-agent my-agent
```

---

## 7. Initial Implementation Plan (MVP Focus)

### Step 1: Project Setup (Day 1)

```bash
# Create project
mkdir fips-agents-cli
cd fips-agents-cli

# Initialize with hatch
hatch new .

# Or manually create structure
mkdir -p src/fips_agents_cli/{commands,tools,templates,config}
mkdir -p tests/{unit,integration}
```

**Files to create:**
1. `pyproject.toml` - Project metadata
2. `src/fips_agents_cli/cli.py` - Main entry point
3. `src/fips_agents_cli/version.py` - Version management
4. `src/fips_agents_cli/commands/create.py` - Create command
5. `src/fips_agents_cli/tools/git.py` - Git operations
6. `tests/test_create.py` - Initial tests

### Step 2: Core CLI Framework (Days 2-3)

**Implement:**
- Click command structure
- Rich console for output
- Basic error handling
- Version command
- Help system

**Test:**
```bash
fips-agents --version
fips-agents --help
fips-agents create --help
```

### Step 3: Git Template Cloning (Days 4-5)

**Implement:**
- Clone repository function
- Template validation
- Directory creation
- Git initialization

**Test:**
```bash
fips-agents create mcp-server test-server
cd test-server
git status  # Should be initialized
```

### Step 4: Project Customization (Days 6-7)

**Implement:**
- Rename project files
- Update pyproject.toml
- Replace placeholder names
- Basic validation

**Test:**
```bash
fips-agents create mcp-server weather-service
cd weather-service
grep -r "weather-service" .  # Should find project name
```

### Step 5: Interactive Prompts (Days 8-9)

**Implement:**
- Questionary integration
- Prompt flow
- Option validation
- `--yes` flag support

**Test:**
```bash
fips-agents create mcp-server my-server  # Interactive
fips-agents create mcp-server my-server --yes  # Skip prompts
```

### Step 6: Polish & Testing (Day 10)

**Implement:**
- Comprehensive error messages
- Progress indicators
- Success messaging
- Integration tests

---

## 8. Technical Decisions to Discuss

### 1. Python vs Node.js

**Question:** Your command examples use `npx`, but CLAUDE.md specifies Python. Confirm Python?

**Recommendation:** Python with `pipx`
- Aligns with ecosystem (FastAPI, LangGraph, FastMCP)
- Consistent with CLAUDE.md preferences
- Same zero-installation experience

**If Python:**
```bash
pipx run fips-agents-cli create mcp-server my-server
# or
pipx install fips-agents-cli
fips-agents create mcp-server my-server
```

**If Node.js:**
```bash
npx fips-agents-cli create mcp-server my-server
# or
npm install -g fips-agents-cli
fips-agents create mcp-server my-server
```

### 2. Command Structure

**Question:** Which command pattern do you prefer?

**Option A (Recommended):**
```bash
fips-agents create mcp-server my-server
fips-agents generate tool weather-tool
```

**Option B:**
```bash
fips-agents new mcp-server my-server
fips-agents gen tool weather-tool
```

**Option C:**
```bash
fips-agents mcp-server create my-server
fips-agents tool generate weather-tool
```

### 3. Template Source

**Question:** Should we clone your template repos directly, or copy them into the CLI?

**Option A (Recommended): Clone from Git**
- Templates stay in separate repos
- Easy to update templates independently
- Users can fork and customize templates
- CLI just knows the repo URLs

**Option B: Bundle in CLI**
- Faster (no network call)
- Works offline
- But harder to update templates

### 4. Generator Template Location

**Question:** Where should generator templates live?

**Recommendation:** Copy into projects (like Ignite)
- Located at `.cli/generators/` in each project
- Copied during project creation
- Teams can customize per-project
- Version controlled with project

**Alternative:** Keep in CLI
- Centralized updates
- But harder to customize per-project

### 5. Configuration Strategy

**Question:** How should users configure defaults?

**Option A: No global config (Recommended)**
- All config via flags or prompts
- Like Ignite
- Simpler to reason about

**Option B: Global config file**
- `~/.config/fips-agents/config.yaml`
- Set defaults once
- But adds complexity

### 6. Package Name

**Question:** What should the PyPI package be named?

**Options:**
- `fips-agents-cli` (explicit)
- `fips-agents` (shorter)
- `agents-cli` (generic)
- `fips-cli` (very short)

**Recommendation:** `fips-agents-cli`
- Clear what it does
- Namespaced with `fips-`
- Command can be `fips-agents` (without `-cli`)

---

## 9. MVP Success Criteria

### Functional Requirements

- [ ] Can create MCP server project from template repo
- [ ] Project is fully functional after creation
- [ ] Can generate tools within project
- [ ] Generated code is valid Python
- [ ] Works in both interactive and non-interactive modes

### User Experience Requirements

- [ ] Zero-installation via pipx
- [ ] Clear, helpful error messages
- [ ] Progress indicators for long operations
- [ ] Works on macOS, Linux, Windows
- [ ] < 5 seconds from command to project ready

### Quality Requirements

- [ ] ≥80% test coverage
- [ ] Integration tests pass
- [ ] No linting errors
- [ ] Type hints throughout
- [ ] Documentation complete

---

## 10. Open Questions for Discussion

1. **Technology:** Confirm Python (not Node.js)?
2. **Command structure:** Which pattern do you prefer?
3. **Template strategy:** Clone from git vs bundle in CLI?
4. **Generator location:** Copy to project vs keep in CLI?
5. **Config strategy:** No global config vs config file?
6. **Package name:** What should we call it on PyPI?
7. **Scope:** Focus on MVP (create + generate tool) first, or broader?
8. **Timeline:** What's the target for MVP release?
9. **Testing:** Any specific scenarios to test?
10. **Documentation:** What level of docs for MVP?

---

## 11. Next Steps

Once we align on the above decisions:

1. **Create project structure**
2. **Set up pyproject.toml**
3. **Implement basic CLI framework**
4. **Add create command**
5. **Test with your mcp-server-template**
6. **Iterate based on feedback**

---

## 12. Example Usage Flow (Target Experience)

```bash
# Install once (or use pipx run for zero-install)
pipx install fips-agents-cli

# Create new MCP server
fips-agents create mcp-server weather-service
# 🔍 Using template: mcp-server-template
# 📦 Cloning from https://github.com/rdwj/mcp-server-template
# ✓ Project created: weather-service
#
# Next steps:
#   cd weather-service
#   python -m venv venv
#   source venv/bin/activate  # or venv\Scripts\activate on Windows
#   pip install -e .
#   fips-agents generate tool get_weather

# Navigate into project
cd weather-service

# Set up environment
python -m venv venv
source venv/bin/activate
pip install -e .

# Generate a tool
fips-agents generate tool get_weather
# ✓ Generated tool: get_weather
# ✓ Created: src/weather_service/tools/get_weather.py
# ✓ Created: tests/test_get_weather.py
#
# Next steps:
#   1. Implement tool logic in src/weather_service/tools/get_weather.py
#   2. Register tool in src/weather_service/server.py
#   3. Run tests: pytest tests/test_get_weather.py

# Generate a prompt
fips-agents generate prompt weather_analysis
# ✓ Generated prompt: weather_analysis
# ✓ Created: prompts/weather_analysis.yaml

# Run tests
pytest

# Start the server
python -m weather_service.server
```

---

## Summary

This plan provides:
1. ✅ Clear technology choices (Python + Click + Rich)
2. ✅ Command structure options
3. ✅ Detailed architecture
4. ✅ Phase-by-phase roadmap
5. ✅ MVP focus (create + generate)
6. ✅ Future expansion path
7. ✅ Discussion points for alignment

Ready to discuss and refine before implementation!
