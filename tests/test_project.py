"""Tests for project customization utilities."""

from fips_agents_cli.tools.project import to_module_name, validate_project_name


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
