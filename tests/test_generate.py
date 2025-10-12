"""Integration tests for generate commands."""

import json

import pytest
from click.testing import CliRunner

from fips_agents_cli.commands.generate import generate


@pytest.fixture
def mock_mcp_project(tmp_path):
    """Create a mock MCP server project structure."""
    # Create pyproject.toml with fastmcp dependency
    pyproject_content = """
[project]
name = "test-mcp-server"
version = "0.1.0"
dependencies = [
    "fastmcp>=0.1.0",
]
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)

    # Create source directory structure
    for component_dir in ["tools", "resources", "prompts", "middleware"]:
        (tmp_path / "src" / component_dir).mkdir(parents=True)

    # Create test directory structure
    for component_dir in ["tools", "resources", "prompts", "middleware"]:
        (tmp_path / "tests" / component_dir).mkdir(parents=True)

    # Create generator templates for each component type
    for component_type in ["tool", "resource", "prompt", "middleware"]:
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / component_type
        generators_dir.mkdir(parents=True)

        # Create component template
        component_template = """'''{{ description }}'''

{% if async %}async {% endif %}def {{ component_name }}():
    '''{{ description }}'''
    return "TODO: Implement"
"""
        (generators_dir / "component.py.j2").write_text(component_template)

        # Create test template
        test_template = """'''Tests for {{ component_name }}.'''

import pytest

{% if async %}@pytest.mark.asyncio
async def test_{{ component_name }}_basic():
{% else %}def test_{{ component_name }}_basic():
{% endif %}    '''Test basic {{ component_name }} functionality.'''
    from src.{{ component_type }}s.{{ component_name }} import {{ component_name }}
    result = {% if async %}await {% endif %}{{ component_name }}()
    assert result is not None
"""
        (generators_dir / "test.py.j2").write_text(test_template)

    return tmp_path


@pytest.fixture
def runner():
    """Create a Click CLI runner."""
    return CliRunner()


class TestGenerateToolCommand:
    """Tests for generate tool command."""

    def test_generate_tool_basic(self, runner, mock_mcp_project):
        """Test basic tool generation."""
        result = runner.invoke(
            generate,
            ["tool", "search_data", "--description", "Search through data"],
            input="Search through data\n",
            catch_exceptions=False,
            obj={},
            env={"PWD": str(mock_mcp_project)},
        )

        # Due to cwd changes, we need to run from within the project
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["tool", "search_data", "--description", "Search through data"],
                catch_exceptions=False,
            )

            # Check exit code
            if result.exit_code != 0:
                print(f"Output: {result.output}")
                print(f"Exception: {result.exception}")

            assert result.exit_code == 0
            assert "success" in result.output.lower() or "created" in result.output.lower()

            # Verify files were created
            assert (mock_mcp_project / "src" / "tools" / "search_data.py").exists()
            assert (mock_mcp_project / "tests" / "tools" / "test_search_data.py").exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_tool_dry_run(self, runner, mock_mcp_project):
        """Test dry-run mode shows file paths."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["tool", "test_tool", "--description", "Test tool", "--dry-run"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0
            assert "dry run" in result.output.lower()
            # Rich console may wrap long paths, so check for path components
            output_normalized = result.output.replace("\n", "")
            assert "src/tools/test_tool.py" in output_normalized

            # Verify files were NOT created
            assert not (mock_mcp_project / "src" / "tools" / "test_tool.py").exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_tool_with_params(self, runner, mock_mcp_project):
        """Test tool generation with params file."""
        # Create params file
        params_data = [
            {
                "name": "query",
                "type": "str",
                "description": "Search query",
                "required": True,
            }
        ]
        params_file = mock_mcp_project / "params.json"
        params_file.write_text(json.dumps(params_data))

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                [
                    "tool",
                    "search_tool",
                    "--description",
                    "Search tool",
                    "--params",
                    str(params_file),
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

        finally:
            os.chdir(original_cwd)

    def test_generate_tool_invalid_name(self, runner, mock_mcp_project):
        """Test error with invalid tool name."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["tool", "Invalid-Name", "--description", "Test"],
                catch_exceptions=False,
            )

            assert result.exit_code != 0
            assert "invalid" in result.output.lower()

        finally:
            os.chdir(original_cwd)

    def test_generate_tool_already_exists(self, runner, mock_mcp_project):
        """Test error when tool already exists."""
        # Create existing tool
        tool_file = mock_mcp_project / "src" / "tools" / "existing_tool.py"
        tool_file.write_text("# Existing tool")

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["tool", "existing_tool", "--description", "Test"],
                catch_exceptions=False,
            )

            assert result.exit_code != 0
            assert "exists" in result.output.lower()

        finally:
            os.chdir(original_cwd)


class TestGenerateResourceCommand:
    """Tests for generate resource command."""

    def test_generate_resource_basic(self, runner, mock_mcp_project):
        """Test basic resource generation."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["resource", "config_data", "--description", "Configuration data"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

            # Verify files were created
            assert (mock_mcp_project / "src" / "resources" / "config_data.py").exists()
            assert (mock_mcp_project / "tests" / "resources" / "test_config_data.py").exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_resource_with_uri(self, runner, mock_mcp_project):
        """Test resource generation with custom URI."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                [
                    "resource",
                    "user_data",
                    "--description",
                    "User data",
                    "--uri",
                    "resource://users/{id}",
                ],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

        finally:
            os.chdir(original_cwd)


class TestGeneratePromptCommand:
    """Tests for generate prompt command."""

    def test_generate_prompt_basic(self, runner, mock_mcp_project):
        """Test basic prompt generation."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["prompt", "code_review", "--description", "Review code"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

            # Verify files were created
            assert (mock_mcp_project / "src" / "prompts" / "code_review.py").exists()
            assert (mock_mcp_project / "tests" / "prompts" / "test_code_review.py").exists()

        finally:
            os.chdir(original_cwd)


class TestGenerateMiddlewareCommand:
    """Tests for generate middleware command."""

    def test_generate_middleware_basic(self, runner, mock_mcp_project):
        """Test basic middleware generation."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["middleware", "auth_middleware", "--description", "Auth middleware"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

            # Verify files were created
            assert (mock_mcp_project / "src" / "middleware" / "auth_middleware.py").exists()
            assert (mock_mcp_project / "tests" / "middleware" / "test_auth_middleware.py").exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_middleware_sync(self, runner, mock_mcp_project):
        """Test sync middleware generation."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                ["middleware", "sync_middleware", "--description", "Sync middleware", "--sync"],
                catch_exceptions=False,
            )

            assert result.exit_code == 0

        finally:
            os.chdir(original_cwd)


class TestGenerateErrorCases:
    """Tests for error handling."""

    def test_not_in_mcp_project(self, runner, tmp_path):
        """Test error when not in MCP project."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            result = runner.invoke(
                generate,
                ["tool", "test_tool", "--description", "Test"],
                catch_exceptions=False,
            )

            assert result.exit_code != 0
            assert "not in an mcp" in result.output.lower()

        finally:
            os.chdir(original_cwd)

    def test_invalid_params_file(self, runner, mock_mcp_project):
        """Test error with invalid params file."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(mock_mcp_project)

            result = runner.invoke(
                generate,
                [
                    "tool",
                    "test_tool",
                    "--description",
                    "Test",
                    "--params",
                    "nonexistent.json",
                ],
                catch_exceptions=False,
            )

            # The path validation will fail before our code runs
            assert result.exit_code != 0

        finally:
            os.chdir(original_cwd)
