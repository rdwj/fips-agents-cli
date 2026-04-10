"""Tests for project customization utilities."""

import pytest
import tomlkit

from fips_agents_cli.tools.project import (
    customize_agent_project,
    to_module_name,
    validate_project_name,
)


class TestProjectValidation:
    """Tests for project name validation."""

    def test_validate_valid_names(self):
        """Test that valid project names pass validation."""
        valid_names = [
            "test",
            "test-server",
            "test_server",
            "myproject",
            "a",
            "test123",
            "test-123-server",
        ]

        for name in valid_names:
            is_valid, error = validate_project_name(name)
            assert is_valid, f"Expected {name} to be valid, got error: {error}"
            assert error is None

    def test_validate_invalid_names(self):
        """Test that invalid project names fail validation."""
        invalid_names = [
            "Test",  # Uppercase
            "TEST",  # All uppercase
            "test@server",  # Special char
            "test.server",  # Period
            "123test",  # Starts with number
            "-test",  # Starts with hyphen
            "_test",  # Starts with underscore
            "",  # Empty
        ]

        for name in invalid_names:
            is_valid, error = validate_project_name(name)
            assert not is_valid, f"Expected {name} to be invalid"
            assert error is not None

    def test_validate_empty_name(self):
        """Test that empty project name returns appropriate error."""
        is_valid, error = validate_project_name("")
        assert not is_valid
        assert "empty" in error.lower()


class TestModuleNameConversion:
    """Tests for converting project names to module names."""

    def test_hyphens_to_underscores(self):
        """Test that hyphens are converted to underscores."""
        assert to_module_name("test-server") == "test_server"
        assert to_module_name("my-mcp-server") == "my_mcp_server"
        assert to_module_name("test-123-server") == "test_123_server"

    def test_underscores_unchanged(self):
        """Test that existing underscores remain unchanged."""
        assert to_module_name("test_server") == "test_server"
        assert to_module_name("my_mcp_server") == "my_mcp_server"

    def test_no_hyphens(self):
        """Test that names without hyphens are unchanged."""
        assert to_module_name("testserver") == "testserver"
        assert to_module_name("myproject") == "myproject"

    def test_mixed_hyphens_underscores(self):
        """Test names with both hyphens and underscores."""
        assert to_module_name("test-server_name") == "test_server_name"
        assert to_module_name("my_test-server") == "my_test_server"


class TestCustomizeAgentProject:
    """Tests for agent project customization."""

    def _create_agent_template(self, path):
        """Create a minimal agent template structure for testing."""
        path.mkdir(parents=True, exist_ok=True)

        (path / "pyproject.toml").write_text(
            '[build-system]\nrequires = ["setuptools>=68"]\n\n'
            '[project]\nname = "agent-template"\nversion = "0.1.0"\n'
        )
        (path / "Makefile").write_text(
            "PROJECT     ?= agent-template\nIMAGE_NAME  ?= agent-template\n"
        )
        (path / "AGENTS.md").write_text("# agent-template\n\nA BaseAgent built on the template.\n")
        (path / "Containerfile").write_text(
            'LABEL io.opencontainers.image.title="agent-template"\n'
        )

        chart = path / "chart"
        chart.mkdir()
        (chart / "Chart.yaml").write_text("name: agent-template\nversion: 0.1.0\n")
        (chart / "values.yaml").write_text("image:\n  repository: agent-template\n")

    def test_updates_pyproject_name(self, temp_dir):
        """Test that pyproject.toml name field is updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        pyproject = tomlkit.parse((project / "pyproject.toml").read_text())
        assert pyproject["project"]["name"] == "my-agent"

    def test_updates_chart_name(self, temp_dir):
        """Test that chart/Chart.yaml name is updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        content = (project / "chart" / "Chart.yaml").read_text()
        assert "name: my-agent" in content
        assert "agent-template" not in content

    def test_updates_values_image(self, temp_dir):
        """Test that chart/values.yaml image repository is updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        content = (project / "chart" / "values.yaml").read_text()
        assert "repository: my-agent" in content
        assert "agent-template" not in content

    def test_updates_makefile(self, temp_dir):
        """Test that Makefile IMAGE_NAME and PROJECT are updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        content = (project / "Makefile").read_text()
        assert "IMAGE_NAME  ?= my-agent" in content
        assert "PROJECT     ?= my-agent" in content
        assert "agent-template" not in content

    def test_updates_agents_md(self, temp_dir):
        """Test that AGENTS.md heading is updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        content = (project / "AGENTS.md").read_text()
        assert "# my-agent" in content
        assert "agent-template" not in content

    def test_updates_containerfile(self, temp_dir):
        """Test that Containerfile image title label is updated."""
        project = temp_dir / "my-agent"
        self._create_agent_template(project)

        customize_agent_project(project, "my-agent")

        content = (project / "Containerfile").read_text()
        assert 'image.title="my-agent"' in content
        assert "agent-template" not in content

    def test_missing_pyproject_raises_error(self, temp_dir):
        """Test that missing pyproject.toml raises FileNotFoundError."""
        project = temp_dir / "my-agent"
        project.mkdir()

        with pytest.raises(FileNotFoundError):
            customize_agent_project(project, "my-agent")

    def test_missing_optional_files_no_error(self, temp_dir):
        """Test that missing optional files (chart, Makefile, etc.) don't cause errors."""
        project = temp_dir / "my-agent"
        project.mkdir()
        # Only create pyproject.toml — everything else is optional
        (project / "pyproject.toml").write_text('[project]\nname = "agent-template"\n')

        # Should not raise
        customize_agent_project(project, "my-agent")

        pyproject = tomlkit.parse((project / "pyproject.toml").read_text())
        assert pyproject["project"]["name"] == "my-agent"
