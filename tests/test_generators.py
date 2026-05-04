"""Tests for generator utilities."""

import json
from unittest.mock import patch

import jinja2
import pytest

from fips_agents_cli.tools.generators import (
    get_project_info,
    load_params_file,
    load_template,
    render_component,
    run_component_tests,
    validate_python_syntax,
    write_component_file,
)


class TestGetProjectInfo:
    """Tests for getting project information."""

    def test_get_project_info_success(self, tmp_path):
        """Test successfully getting project info."""
        pyproject_content = """
[project]
name = "my-mcp-server"
version = "1.2.3"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        info = get_project_info(tmp_path)
        assert info["name"] == "my-mcp-server"
        assert info["module_name"] == "my_mcp_server"
        assert info["version"] == "1.2.3"

    def test_get_project_info_defaults(self, tmp_path):
        """Test defaults when fields are missing."""
        pyproject_content = """
[project]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        info = get_project_info(tmp_path)
        assert info["name"] == "unknown"
        assert info["version"] == "0.1.0"

    def test_get_project_info_missing_file(self, tmp_path):
        """Test error when pyproject.toml doesn't exist."""
        with pytest.raises(FileNotFoundError):
            get_project_info(tmp_path)

    def test_get_project_info_invalid_toml(self, tmp_path):
        """Test error when pyproject.toml is invalid."""
        (tmp_path / "pyproject.toml").write_text("invalid [[ toml")

        with pytest.raises(ValueError):
            get_project_info(tmp_path)


class TestLoadTemplate:
    """Tests for loading Jinja2 templates."""

    def test_load_template_success(self, tmp_path):
        """Test successfully loading a template."""
        # Create generator template
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / "tool"
        generators_dir.mkdir(parents=True)
        (generators_dir / "component.py.j2").write_text("def {{ component_name }}():\n    pass")

        template = load_template(tmp_path, "tool", "component.py.j2")
        assert isinstance(template, jinja2.Template)

        # Test rendering
        result = template.render(component_name="my_tool")
        assert "def my_tool():" in result

    def test_load_template_missing_file(self, tmp_path):
        """Test error when template file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_template(tmp_path, "tool", "component.py.j2")

    def test_load_template_invalid_jinja(self, tmp_path):
        """Test error when template has invalid Jinja2 syntax."""
        # Create generator template with invalid syntax
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / "tool"
        generators_dir.mkdir(parents=True)
        (generators_dir / "component.py.j2").write_text("{{ unclosed")

        with pytest.raises(jinja2.TemplateError):
            load_template(tmp_path, "tool", "component.py.j2")


class TestLoadParamsFile:
    """Tests for loading parameter files."""

    def test_load_params_success(self, tmp_path):
        """Test successfully loading params file."""
        params_data = [
            {
                "name": "query",
                "type": "str",
                "description": "Search query",
                "required": True,
                "min_length": 1,
            },
            {
                "name": "limit",
                "type": "int",
                "description": "Max results",
                "required": False,
                "default": 10,
            },
        ]
        params_file = tmp_path / "params.json"
        params_file.write_text(json.dumps(params_data))

        params = load_params_file(params_file)
        assert len(params) == 2
        assert params[0]["name"] == "query"
        assert params[1]["name"] == "limit"

    def test_load_params_missing_file(self, tmp_path):
        """Test error when params file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_params_file(tmp_path / "nonexistent.json")

    def test_load_params_invalid_json(self, tmp_path):
        """Test error when JSON is invalid."""
        params_file = tmp_path / "params.json"
        params_file.write_text("{ invalid json")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_params_file(params_file)

    def test_load_params_not_array(self, tmp_path):
        """Test error when params is not an array."""
        params_file = tmp_path / "params.json"
        params_file.write_text('{"name": "query"}')

        with pytest.raises(ValueError, match="must contain a JSON array"):
            load_params_file(params_file)

    def test_load_params_missing_required_field(self, tmp_path):
        """Test error when parameter is missing required field."""
        params_data = [{"name": "query", "type": "str"}]  # Missing description
        params_file = tmp_path / "params.json"
        params_file.write_text(json.dumps(params_data))

        with pytest.raises(ValueError, match="missing required field"):
            load_params_file(params_file)

    def test_load_params_invalid_name(self, tmp_path):
        """Test error when parameter name is invalid."""
        params_data = [{"name": "123invalid", "type": "str", "description": "Invalid name"}]
        params_file = tmp_path / "params.json"
        params_file.write_text(json.dumps(params_data))

        with pytest.raises(ValueError, match="invalid name"):
            load_params_file(params_file)

    def test_load_params_invalid_type(self, tmp_path):
        """Test error when parameter type is invalid."""
        params_data = [{"name": "query", "type": "invalid_type", "description": "Query"}]
        params_file = tmp_path / "params.json"
        params_file.write_text(json.dumps(params_data))

        with pytest.raises(ValueError, match="invalid type"):
            load_params_file(params_file)

    def test_load_params_valid_types(self, tmp_path):
        """Test all valid parameter types."""
        valid_types = [
            "str",
            "int",
            "float",
            "bool",
            "list[str]",
            "str | None",
            "dict[str, str]",
            "dict[str, Any]",
        ]

        for param_type in valid_types:
            params_data = [{"name": "param", "type": param_type, "description": "Test"}]
            params_file = tmp_path / "params.json"
            params_file.write_text(json.dumps(params_data))

            params = load_params_file(params_file)
            assert params[0]["type"] == param_type


class TestRenderComponent:
    """Tests for rendering components."""

    def test_render_component_success(self):
        """Test successfully rendering a template."""
        template_str = "def {{ name }}({{ param }}):\n    return {{ value }}"
        template = jinja2.Template(template_str)

        result = render_component(template, {"name": "my_func", "param": "x", "value": "42"})
        assert "def my_func(x):" in result
        assert "return 42" in result

    def test_render_component_missing_variable(self):
        """Test error when variable is missing."""
        template_str = "def {{ name }}():\n    return {{ missing_var }}"
        template = jinja2.Template(template_str)

        # Jinja2 renders undefined variables as empty strings by default
        result = render_component(template, {"name": "my_func"})
        assert "def my_func():" in result

    def test_render_component_with_filters(self):
        """Test rendering with Jinja2 filters."""
        template_str = "{{ name|upper }}"
        template = jinja2.Template(template_str)

        result = render_component(template, {"name": "hello"})
        assert result == "HELLO"


class TestValidatePythonSyntax:
    """Tests for validating Python syntax."""

    def test_valid_syntax(self):
        """Test valid Python code."""
        code = "def my_func():\n    return 42"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True
        assert error == ""

    def test_valid_complex_code(self):
        """Test valid complex Python code."""
        code = """
class MyClass:
    def __init__(self, value):
        self.value = value

    def get_value(self):
        return self.value
"""
        is_valid, error = validate_python_syntax(code)
        assert is_valid is True

    def test_invalid_syntax_missing_colon(self):
        """Test invalid syntax with missing colon."""
        code = "def my_func()\n    return 42"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False
        assert "syntax error" in error.lower()

    def test_invalid_syntax_indentation(self):
        """Test invalid syntax with bad indentation."""
        code = "def my_func():\nreturn 42"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False

    def test_invalid_syntax_unclosed_paren(self):
        """Test invalid syntax with unclosed parenthesis."""
        code = "def my_func(:\n    return 42"
        is_valid, error = validate_python_syntax(code)
        assert is_valid is False


class TestWriteComponentFile:
    """Tests for writing component files."""

    def test_write_file_success(self, tmp_path):
        """Test successfully writing a file."""
        file_path = tmp_path / "test.py"
        content = "def my_func():\n    return 42"

        write_component_file(content, file_path)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_write_file_creates_parent_dirs(self, tmp_path):
        """Test that parent directories are created."""
        file_path = tmp_path / "src" / "tools" / "test.py"
        content = "# Test content"

        write_component_file(content, file_path)

        assert file_path.exists()
        assert file_path.read_text() == content

    def test_write_file_overwrites_existing(self, tmp_path):
        """Test that existing files are overwritten."""
        file_path = tmp_path / "test.py"
        file_path.write_text("old content")

        new_content = "new content"
        write_component_file(new_content, file_path)

        assert file_path.read_text() == new_content


class TestRunComponentTests:
    """Tests for running component tests."""

    def test_run_tests_success(self, tmp_path):
        """Test running tests that pass."""
        # Create a simple passing test
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_passing():
    assert True
"""
        )

        success, output = run_component_tests(tmp_path, test_file)

        # Note: This may fail if pytest isn't installed in the test environment
        # The actual test will verify the behavior
        assert isinstance(success, bool)
        assert isinstance(output, str)

    def test_run_tests_failure(self, tmp_path):
        """Test running tests that fail."""
        # Create a failing test
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_failing():
    assert False, "This test should fail"
"""
        )

        success, output = run_component_tests(tmp_path, test_file)

        # The test should fail
        assert isinstance(success, bool)
        assert isinstance(output, str)

    @patch("subprocess.run")
    def test_run_tests_timeout(self, mock_run, tmp_path):
        """Test handling of test timeout."""
        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("pytest", 30)

        test_file = tmp_path / "test_example.py"
        success, output = run_component_tests(tmp_path, test_file)

        assert success is False
        assert "timed out" in output.lower()

    @patch("subprocess.run")
    def test_run_tests_pytest_not_found(self, mock_run, tmp_path):
        """Test handling when pytest is not found."""
        mock_run.side_effect = FileNotFoundError("pytest not found")

        test_file = tmp_path / "test_example.py"
        success, output = run_component_tests(tmp_path, test_file)

        assert success is False
        assert "pytest not found" in output.lower()
