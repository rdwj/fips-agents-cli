"""Tests for the create command."""

from pathlib import Path
from unittest.mock import patch

from fips_agents_cli.cli import cli


class TestCreateMcpServer:
    """Tests for the 'create mcp-server' command."""

    def test_help_message(self, cli_runner):
        """Test that help message is displayed correctly."""
        result = cli_runner.invoke(cli, ["create", "mcp-server", "--help"])
        assert result.exit_code == 0
        assert "Create a new MCP server project" in result.output
        assert "PROJECT_NAME" in result.output

    def test_invalid_project_name_uppercase(self, cli_runner):
        """Test that uppercase letters in project name are rejected."""
        result = cli_runner.invoke(cli, ["create", "mcp-server", "TestServer"])
        assert result.exit_code == 1
        assert "Invalid project name" in result.output

    def test_invalid_project_name_special_chars(self, cli_runner):
        """Test that special characters in project name are rejected."""
        result = cli_runner.invoke(cli, ["create", "mcp-server", "test@server"])
        assert result.exit_code == 1
        assert "Invalid project name" in result.output

    def test_invalid_project_name_starts_with_number(self, cli_runner):
        """Test that project name starting with number is rejected."""
        result = cli_runner.invoke(cli, ["create", "mcp-server", "123test"])
        assert result.exit_code == 1
        assert "Invalid project name" in result.output

    def test_invalid_project_name_empty(self, cli_runner):
        """Test that empty project name is rejected."""
        result = cli_runner.invoke(cli, ["create", "mcp-server", ""])
        # Click will handle this as missing argument
        assert result.exit_code != 0

    def test_valid_project_names(self, cli_runner):
        """Test that various valid project names are accepted."""
        valid_names = [
            "test",
            "test-server",
            "test_server",
            "test123",
            "test-server-123",
            "myserver",
            "a",  # Single letter
        ]

        for name in valid_names:
            # We'll mock the git operations to avoid actual cloning
            with (
                patch("fips_agents_cli.commands.create.clone_template"),
                patch("fips_agents_cli.commands.create.update_project_name"),
                patch("fips_agents_cli.commands.create.cleanup_template_files"),
                patch("fips_agents_cli.commands.create.init_repository"),
                patch("fips_agents_cli.commands.create.is_git_installed", return_value=True),
            ):

                result = cli_runner.invoke(
                    cli, ["create", "mcp-server", name, "--target-dir", str(Path.cwd() / "temp")]
                )
                # Should pass validation (though may fail on other steps in isolation)
                assert "Invalid project name" not in result.output

    def test_existing_directory_error(self, cli_runner, temp_dir):
        """Test that existing directory causes an error."""
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        result = cli_runner.invoke(
            cli, ["create", "mcp-server", "existing-project", "--target-dir", str(temp_dir)]
        )
        assert result.exit_code == 1
        assert "already exists" in result.output

    @patch("fips_agents_cli.commands.create.is_git_installed")
    def test_git_not_installed(self, mock_is_git_installed, cli_runner, temp_dir):
        """Test that missing git installation is detected."""
        mock_is_git_installed.return_value = False

        result = cli_runner.invoke(
            cli, ["create", "mcp-server", "test-server", "--target-dir", str(temp_dir)]
        )
        assert result.exit_code == 1
        assert "Git is not installed" in result.output

    @patch("fips_agents_cli.commands.create.clone_template")
    @patch("fips_agents_cli.commands.create.is_git_installed")
    def test_clone_failure(self, mock_is_git_installed, mock_clone, cli_runner, temp_dir):
        """Test handling of git clone failures."""
        mock_is_git_installed.return_value = True
        mock_clone.side_effect = Exception("Connection timeout")

        result = cli_runner.invoke(
            cli, ["create", "mcp-server", "test-server", "--target-dir", str(temp_dir)]
        )
        assert result.exit_code == 1
        assert "Failed to clone template" in result.output

    @patch("fips_agents_cli.commands.create.clone_template")
    @patch("fips_agents_cli.commands.create.update_project_name")
    @patch("fips_agents_cli.commands.create.cleanup_template_files")
    @patch("fips_agents_cli.commands.create.init_repository")
    @patch("fips_agents_cli.commands.create.is_git_installed")
    def test_successful_creation(
        self,
        mock_is_git_installed,
        mock_init_repo,
        mock_cleanup,
        mock_update,
        mock_clone,
        cli_runner,
        temp_dir,
    ):
        """Test successful project creation with all steps."""
        mock_is_git_installed.return_value = True

        # Mock the clone to create a minimal structure
        def create_minimal_structure(url, target_path, branch=None):
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        mock_clone.side_effect = create_minimal_structure

        result = cli_runner.invoke(
            cli, ["create", "mcp-server", "my-server", "--target-dir", str(temp_dir)]
        )

        # Verify all steps were called
        assert mock_clone.called
        assert mock_update.called
        assert mock_cleanup.called
        assert mock_init_repo.called

        # Check success message
        assert result.exit_code == 0
        assert "Successfully created MCP server project" in result.output
        assert "my-server" in result.output

    @patch("fips_agents_cli.commands.create.clone_template")
    @patch("fips_agents_cli.commands.create.update_project_name")
    @patch("fips_agents_cli.commands.create.cleanup_template_files")
    @patch("fips_agents_cli.commands.create.is_git_installed")
    def test_no_git_flag(
        self,
        mock_is_git_installed,
        mock_cleanup,
        mock_update,
        mock_clone,
        cli_runner,
        temp_dir,
    ):
        """Test that --no-git flag skips git initialization."""
        mock_is_git_installed.return_value = True

        def create_minimal_structure(url, target_path, branch=None):
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / "pyproject.toml").write_text("[project]\nname = 'test'")

        mock_clone.side_effect = create_minimal_structure

        with patch("fips_agents_cli.commands.create.init_repository") as mock_init:
            result = cli_runner.invoke(
                cli,
                ["create", "mcp-server", "my-server", "--target-dir", str(temp_dir), "--no-git"],
            )

            # Verify git init was NOT called
            assert not mock_init.called
            assert result.exit_code == 0

    def test_target_dir_option(self, cli_runner, temp_dir):
        """Test that --target-dir option works correctly."""
        with (
            patch("fips_agents_cli.commands.create.clone_template"),
            patch("fips_agents_cli.commands.create.update_project_name"),
            patch("fips_agents_cli.commands.create.cleanup_template_files"),
            patch("fips_agents_cli.commands.create.init_repository"),
            patch("fips_agents_cli.commands.create.is_git_installed", return_value=True),
        ):

            result = cli_runner.invoke(
                cli, ["create", "mcp-server", "test-server", "--target-dir", str(temp_dir)]
            )

            # Should include the target directory in output
            assert str(temp_dir) in result.output or "test-server" in result.output
