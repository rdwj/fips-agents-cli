"""Tests for GitHub CLI integration utilities."""

import json
from unittest.mock import MagicMock, patch

from fips_agents_cli.tools.github import (
    check_gh_prerequisites,
    create_github_repo,
    get_github_username,
    get_repo_info,
    is_gh_authenticated,
    is_gh_installed,
)


class TestIsGhInstalled:
    """Tests for is_gh_installed function."""

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_true_when_gh_installed(self, mock_run):
        """Should return True when gh --version succeeds."""
        mock_run.return_value = MagicMock(returncode=0)
        assert is_gh_installed() is True
        mock_run.assert_called_once()

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_false_when_gh_not_installed(self, mock_run):
        """Should return False when gh command not found."""
        mock_run.side_effect = FileNotFoundError()
        assert is_gh_installed() is False

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_false_on_timeout(self, mock_run):
        """Should return False when command times out."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("gh", 10)
        assert is_gh_installed() is False


class TestIsGhAuthenticated:
    """Tests for is_gh_authenticated function."""

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_true_when_authenticated(self, mock_run):
        """Should return True when gh auth status succeeds."""
        mock_run.return_value = MagicMock(returncode=0)
        assert is_gh_authenticated() is True

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_false_when_not_authenticated(self, mock_run):
        """Should return False when gh auth status fails."""
        mock_run.return_value = MagicMock(returncode=1)
        assert is_gh_authenticated() is False

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_false_when_gh_not_installed(self, mock_run):
        """Should return False when gh is not installed."""
        mock_run.side_effect = FileNotFoundError()
        assert is_gh_authenticated() is False


class TestGetGithubUsername:
    """Tests for get_github_username function."""

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_username_when_authenticated(self, mock_run):
        """Should return username when gh api user succeeds."""
        mock_run.return_value = MagicMock(returncode=0, stdout="testuser\n")
        assert get_github_username() == "testuser"

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_none_when_not_authenticated(self, mock_run):
        """Should return None when not authenticated."""
        mock_run.return_value = MagicMock(returncode=1)
        assert get_github_username() is None

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_none_on_error(self, mock_run):
        """Should return None on error."""
        mock_run.side_effect = FileNotFoundError()
        assert get_github_username() is None


class TestCreateGithubRepo:
    """Tests for create_github_repo function."""

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_creates_public_repo_successfully(self, mock_run):
        """Should create public repo and return URL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps(
                {
                    "url": "https://github.com/testuser/my-repo",
                    "name": "my-repo",
                    "owner": "testuser",
                }
            ),
        )

        success, url, error = create_github_repo("my-repo")

        assert success is True
        assert url == "https://github.com/testuser/my-repo"
        assert error is None

        # Verify command includes --public
        call_args = mock_run.call_args[0][0]
        assert "--public" in call_args
        assert "--private" not in call_args

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_creates_private_repo(self, mock_run):
        """Should create private repo when private=True."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"url": "https://github.com/testuser/my-repo"}),
        )

        success, url, error = create_github_repo("my-repo", private=True)

        assert success is True
        call_args = mock_run.call_args[0][0]
        assert "--private" in call_args
        assert "--public" not in call_args

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_creates_repo_in_org(self, mock_run):
        """Should create repo in specified org."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"url": "https://github.com/myorg/my-repo"}),
        )

        success, url, error = create_github_repo("my-repo", org="myorg")

        assert success is True
        call_args = mock_run.call_args[0][0]
        assert "myorg/my-repo" in call_args

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_includes_description(self, mock_run):
        """Should include description in command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"url": "https://github.com/testuser/my-repo"}),
        )

        create_github_repo("my-repo", description="My awesome repo")

        call_args = mock_run.call_args[0][0]
        assert "--description" in call_args
        desc_index = call_args.index("--description")
        assert call_args[desc_index + 1] == "My awesome repo"

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_handles_already_exists_error(self, mock_run):
        """Should return error when repo already exists."""
        mock_run.return_value = MagicMock(returncode=1, stderr="repository already exists")

        success, url, error = create_github_repo("my-repo")

        assert success is False
        assert url is None
        assert "already exists" in error

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_handles_org_not_found_error(self, mock_run):
        """Should return error when org not found."""
        mock_run.return_value = MagicMock(returncode=1, stderr="organization not found")

        success, url, error = create_github_repo("my-repo", org="nonexistent")

        assert success is False
        assert "not found" in error.lower()

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_handles_auth_error(self, mock_run):
        """Should return error when not authenticated."""
        mock_run.return_value = MagicMock(
            returncode=1, stderr="authentication required, please login"
        )

        success, url, error = create_github_repo("my-repo")

        assert success is False
        assert "authentication" in error.lower()

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_handles_gh_not_installed(self, mock_run):
        """Should return error when gh not installed."""
        mock_run.side_effect = FileNotFoundError()

        success, url, error = create_github_repo("my-repo")

        assert success is False
        assert "not installed" in error.lower()


class TestCheckGhPrerequisites:
    """Tests for check_gh_prerequisites function."""

    @patch("fips_agents_cli.tools.github.is_gh_authenticated")
    @patch("fips_agents_cli.tools.github.is_gh_installed")
    def test_returns_ready_when_all_ok(self, mock_installed, mock_auth):
        """Should return (True, None) when all prerequisites met."""
        mock_installed.return_value = True
        mock_auth.return_value = True

        ready, error = check_gh_prerequisites()

        assert ready is True
        assert error is None

    @patch("fips_agents_cli.tools.github.is_gh_installed")
    def test_returns_error_when_not_installed(self, mock_installed):
        """Should return error when gh not installed."""
        mock_installed.return_value = False

        ready, error = check_gh_prerequisites()

        assert ready is False
        assert "not installed" in error.lower()

    @patch("fips_agents_cli.tools.github.is_gh_authenticated")
    @patch("fips_agents_cli.tools.github.is_gh_installed")
    def test_returns_error_when_not_authenticated(self, mock_installed, mock_auth):
        """Should return error when not authenticated."""
        mock_installed.return_value = True
        mock_auth.return_value = False

        ready, error = check_gh_prerequisites()

        assert ready is False
        assert "not authenticated" in error.lower()


class TestGetRepoInfo:
    """Tests for get_repo_info function."""

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_repo_info(self, mock_run):
        """Should return repo info dict when successful."""
        repo_data = {
            "name": "my-repo",
            "owner": {"login": "testuser"},
            "url": "https://github.com/testuser/my-repo",
            "description": "Test repo",
            "isPrivate": False,
        }
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(repo_data))

        result = get_repo_info("testuser/my-repo")

        assert result == repo_data

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_none_when_not_found(self, mock_run):
        """Should return None when repo not found."""
        mock_run.return_value = MagicMock(returncode=1)

        result = get_repo_info("testuser/nonexistent")

        assert result is None

    @patch("fips_agents_cli.tools.github.subprocess.run")
    def test_returns_none_on_error(self, mock_run):
        """Should return None on error."""
        mock_run.side_effect = FileNotFoundError()

        result = get_repo_info("testuser/my-repo")

        assert result is None
