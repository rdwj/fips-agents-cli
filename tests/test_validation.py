"""Tests for validation utilities."""

from fips_agents_cli.tools.validation import (
    component_exists,
    find_project_root,
    is_valid_component_name,
    validate_generator_templates,
)


class TestIsValidComponentName:
    """Tests for component name validation."""

    def test_valid_snake_case_name(self):
        """Test valid snake_case component name."""
        is_valid, error = is_valid_component_name("my_tool")
        assert is_valid is True
        assert error == ""

    def test_valid_name_with_numbers(self):
        """Test valid name with numbers."""
        is_valid, error = is_valid_component_name("tool_v2")
        assert is_valid is True
        assert error == ""

    def test_valid_name_starting_with_underscore(self):
        """Test valid name starting with underscore."""
        is_valid, error = is_valid_component_name("_private_tool")
        assert is_valid is True
        assert error == ""

    def test_empty_name(self):
        """Test empty component name is invalid."""
        is_valid, error = is_valid_component_name("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_name_starting_with_number(self):
        """Test name starting with number is invalid."""
        is_valid, error = is_valid_component_name("123tool")
        assert is_valid is False
        assert "start with" in error.lower()

    def test_name_with_hyphens(self):
        """Test name with hyphens is invalid."""
        is_valid, error = is_valid_component_name("my-tool")
        assert is_valid is False
        assert "identifier" in error.lower()

    def test_name_with_spaces(self):
        """Test name with spaces is invalid."""
        is_valid, error = is_valid_component_name("my tool")
        assert is_valid is False
        assert "identifier" in error.lower()

    def test_name_with_uppercase(self):
        """Test name with uppercase letters is invalid."""
        is_valid, error = is_valid_component_name("MyTool")
        assert is_valid is False
        assert "snake_case" in error.lower()

    def test_python_keyword(self):
        """Test Python keywords are invalid."""
        is_valid, error = is_valid_component_name("for")
        assert is_valid is False
        assert "keyword" in error.lower()

    def test_another_python_keyword(self):
        """Test another Python keyword."""
        is_valid, error = is_valid_component_name("class")
        assert is_valid is False
        assert "keyword" in error.lower()

    def test_name_with_special_characters(self):
        """Test name with special characters is invalid."""
        is_valid, error = is_valid_component_name("my@tool")
        assert is_valid is False
        assert "identifier" in error.lower()


class TestFindProjectRoot:
    """Tests for finding project root."""

    def test_find_root_in_current_directory(self, tmp_path):
        """Test finding project root in current directory."""
        # Create a mock MCP project structure
        pyproject_content = """
[project]
name = "test-mcp-server"
dependencies = [
    "fastmcp>=0.1.0",
]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Change to the directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            root = find_project_root()
            assert root == tmp_path
        finally:
            os.chdir(original_cwd)

    def test_find_root_in_parent_directory(self, tmp_path):
        """Test finding project root in parent directory."""
        # Create a mock MCP project structure
        pyproject_content = """
[project]
name = "test-mcp-server"
dependencies = [
    "fastmcp>=0.1.0",
]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Create a subdirectory
        subdir = tmp_path / "src" / "tools"
        subdir.mkdir(parents=True)

        # Change to the subdirectory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            root = find_project_root()
            assert root == tmp_path
        finally:
            os.chdir(original_cwd)

    def test_no_project_root_found(self, tmp_path):
        """Test returns None when no project root is found."""
        # Create a directory without pyproject.toml
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            root = find_project_root()
            assert root is None
        finally:
            os.chdir(original_cwd)

    def test_project_without_fastmcp_dependency(self, tmp_path):
        """Test returns None for projects without fastmcp dependency."""
        # Create a pyproject.toml without fastmcp
        pyproject_content = """
[project]
name = "test-project"
dependencies = [
    "click>=8.0.0",
]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        # Change to the directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            root = find_project_root()
            assert root is None
        finally:
            os.chdir(original_cwd)


class TestComponentExists:
    """Tests for checking if component exists."""

    def test_component_does_not_exist(self, tmp_path):
        """Test component that doesn't exist."""
        exists = component_exists(tmp_path, "tool", "my_tool")
        assert exists is False

    def test_component_exists_tool(self, tmp_path):
        """Test existing tool component."""
        # Create a tool file
        tool_dir = tmp_path / "src" / "tools"
        tool_dir.mkdir(parents=True)
        (tool_dir / "my_tool.py").write_text("# Tool code")

        exists = component_exists(tmp_path, "tool", "my_tool")
        assert exists is True

    def test_component_exists_resource(self, tmp_path):
        """Test existing resource component."""
        # Create a resource file
        resource_dir = tmp_path / "src" / "resources"
        resource_dir.mkdir(parents=True)
        (resource_dir / "my_resource.py").write_text("# Resource code")

        exists = component_exists(tmp_path, "resource", "my_resource")
        assert exists is True

    def test_component_exists_prompt(self, tmp_path):
        """Test existing prompt component."""
        # Create a prompt file
        prompt_dir = tmp_path / "src" / "prompts"
        prompt_dir.mkdir(parents=True)
        (prompt_dir / "my_prompt.py").write_text("# Prompt code")

        exists = component_exists(tmp_path, "prompt", "my_prompt")
        assert exists is True

    def test_component_exists_middleware(self, tmp_path):
        """Test existing middleware component."""
        # Create a middleware file
        middleware_dir = tmp_path / "src" / "middleware"
        middleware_dir.mkdir(parents=True)
        (middleware_dir / "my_middleware.py").write_text("# Middleware code")

        exists = component_exists(tmp_path, "middleware", "my_middleware")
        assert exists is True

    def test_invalid_component_type(self, tmp_path):
        """Test invalid component type returns False."""
        exists = component_exists(tmp_path, "invalid_type", "my_component")
        assert exists is False


class TestValidateGeneratorTemplates:
    """Tests for validating generator templates."""

    def test_templates_exist(self, tmp_path):
        """Test valid generator templates."""
        # Create generator template structure
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / "tool"
        generators_dir.mkdir(parents=True)
        (generators_dir / "component.py.j2").write_text("{{ component_name }}")
        (generators_dir / "test.py.j2").write_text("test_{{ component_name }}")

        is_valid, error = validate_generator_templates(tmp_path, "tool")
        assert is_valid is True
        assert error == ""

    def test_generators_directory_missing(self, tmp_path):
        """Test missing generators directory."""
        is_valid, error = validate_generator_templates(tmp_path, "tool")
        assert is_valid is False
        assert "not found" in error.lower()

    def test_component_template_missing(self, tmp_path):
        """Test missing component template."""
        # Create generator directory but missing component.py.j2
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / "tool"
        generators_dir.mkdir(parents=True)
        (generators_dir / "test.py.j2").write_text("test_{{ component_name }}")

        is_valid, error = validate_generator_templates(tmp_path, "tool")
        assert is_valid is False
        assert "component.py.j2" in error

    def test_test_template_missing(self, tmp_path):
        """Test missing test template."""
        # Create generator directory but missing test.py.j2
        generators_dir = tmp_path / ".fips-agents-cli" / "generators" / "tool"
        generators_dir.mkdir(parents=True)
        (generators_dir / "component.py.j2").write_text("{{ component_name }}")

        is_valid, error = validate_generator_templates(tmp_path, "tool")
        assert is_valid is False
        assert "test.py.j2" in error

    def test_all_component_types(self, tmp_path):
        """Test validation for all component types."""
        component_types = ["tool", "resource", "prompt", "middleware"]

        for component_type in component_types:
            # Create generator template structure
            generators_dir = tmp_path / ".fips-agents-cli" / "generators" / component_type
            generators_dir.mkdir(parents=True, exist_ok=True)
            (generators_dir / "component.py.j2").write_text("{{ component_name }}")
            (generators_dir / "test.py.j2").write_text("test_{{ component_name }}")

            is_valid, error = validate_generator_templates(tmp_path, component_type)
            assert is_valid is True, f"Failed for {component_type}: {error}"
