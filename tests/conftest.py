"""Pytest configuration and fixtures for fips-agents-cli tests."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Provide a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_template_repo(temp_dir):
    """Create a mock template repository structure for testing."""
    template_dir = temp_dir / "template"
    template_dir.mkdir()

    # Create basic template structure
    (template_dir / "pyproject.toml").write_text("""[project]
name = "mcp-server-template"
version = "0.1.0"

[project.scripts]
mcp-server-template = "mcp_server_template.server:main"
""")

    # Create src directory with module
    src_dir = template_dir / "src" / "mcp_server_template"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "server.py").write_text("def main(): pass")

    # Create prompts directory
    prompts_dir = template_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "example.yaml").write_text("name: example\ntemplate: test")

    # Create .fips-agents-cli/generators directory
    generators_dir = template_dir / ".fips-agents-cli" / "generators"
    generators_dir.mkdir(parents=True)
    (generators_dir / "test.py").write_text("# Generator test")

    return template_dir


@pytest.fixture
def mock_agent_template(temp_dir):
    """Create a mock agent template directory structure."""
    template = temp_dir / "agent-template"
    template.mkdir()

    (template / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["setuptools>=68"]\n\n'
        '[project]\nname = "agent-template"\nversion = "0.1.0"\n'
    )
    (template / "agent.yaml").write_text("model:\n  name: test\n")
    (template / "Makefile").write_text(
        "PROJECT     ?= agent-template\nIMAGE_NAME  ?= agent-template\n"
    )
    (template / "AGENTS.md").write_text("# agent-template\n\nA BaseAgent built on the template.\n")
    (template / "Containerfile").write_text(
        'LABEL io.opencontainers.image.title="agent-template"\n'
    )

    src = template / "src"
    src.mkdir()
    (src / "__init__.py").touch()
    (src / "agent.py").write_text("# Example agent\n")

    base = src / "base_agent"
    base.mkdir()
    (base / "__init__.py").write_text('__version__ = "0.1.0"\n')

    chart = template / "chart"
    chart.mkdir()
    (chart / "Chart.yaml").write_text("name: agent-template\nversion: 0.1.0\n")
    (chart / "values.yaml").write_text("image:\n  repository: agent-template\n")

    return template


@pytest.fixture
def sample_project_name():
    """Provide a valid sample project name."""
    return "test-mcp-server"


@pytest.fixture(autouse=True)
def mock_registry_login():
    """Mock registry login check for model-car tests."""
    with patch(
        "fips_agents_cli.commands.model_car.check_registry_login",
        return_value=(True, "testuser"),
    ):
        yield
