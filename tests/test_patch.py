"""Tests for the patch command and the patching tools layer."""

import json
from pathlib import Path

import pytest

from fips_agents_cli.cli import cli
from fips_agents_cli.tools import patching
from fips_agents_cli.tools.patching import (
    AGENT_FILE_CATEGORIES,
    AGENT_NEVER_PATCH,
    MCP_FILE_CATEGORIES,
    MCP_NEVER_PATCH,
    get_categories_for_type,
    get_project_type,
)
from fips_agents_cli.tools.validation import find_fips_project_root

# ---------------------------------------------------------------------------
# Unit tests — pure helpers
# ---------------------------------------------------------------------------


class TestGetProjectType:
    def test_reads_type_from_template_info(self):
        assert get_project_type({"template": {"type": "agent"}}) == "agent"

    def test_defaults_to_mcp_server_when_missing(self):
        # Backwards compat: pre-#13 projects had no template.type
        assert get_project_type({"template": {"url": "x"}}) == "mcp-server"
        assert get_project_type({}) == "mcp-server"


class TestGetCategoriesForType:
    def test_mcp_server(self):
        cats, never = get_categories_for_type("mcp-server")
        assert cats is MCP_FILE_CATEGORIES
        assert never is MCP_NEVER_PATCH

    @pytest.mark.parametrize("project_type", ["agent", "workflow"])
    def test_agent_and_workflow_share_categories(self, project_type):
        cats, never = get_categories_for_type(project_type)
        assert cats is AGENT_FILE_CATEGORIES
        assert never is AGENT_NEVER_PATCH

    @pytest.mark.parametrize("project_type", ["gateway", "ui", "sandbox", "bogus"])
    def test_unsupported_types_raise(self, project_type):
        with pytest.raises(ValueError, match=project_type):
            get_categories_for_type(project_type)

    def test_agent_categories_have_no_framework_language(self):
        # Per project convention: avoid "framework" in user-facing strings
        for category, config in AGENT_FILE_CATEGORIES.items():
            assert "framework" not in category.lower()
            assert "framework" not in config["description"].lower()


# ---------------------------------------------------------------------------
# Unit tests — find_fips_project_root walks up to .template-info
# ---------------------------------------------------------------------------


class TestFindFipsProjectRoot:
    def test_returns_none_when_no_template_info(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert find_fips_project_root() is None

    def test_finds_template_info_in_cwd(self, tmp_path, monkeypatch):
        info = {"template": {"type": "agent"}}
        (tmp_path / ".template-info").write_text(json.dumps(info))
        monkeypatch.chdir(tmp_path)

        result = find_fips_project_root()
        assert result is not None
        root, template_info = result
        assert root == tmp_path
        assert template_info == info

    def test_walks_up_to_parent(self, tmp_path, monkeypatch):
        info = {"template": {"type": "mcp-server"}}
        (tmp_path / ".template-info").write_text(json.dumps(info))
        nested = tmp_path / "src" / "tools"
        nested.mkdir(parents=True)
        monkeypatch.chdir(nested)

        result = find_fips_project_root()
        assert result is not None
        root, _ = result
        assert root == tmp_path


# ---------------------------------------------------------------------------
# Unit tests — _clone_template_for_patch handles subdirs
# ---------------------------------------------------------------------------


class TestCloneTemplateForPatch:
    def test_standalone_repo_returns_clone_root(self, tmp_path, monkeypatch):
        def fake_clone(url, target_path, branch=None):
            target_path.mkdir(parents=True, exist_ok=True)
            (target_path / "Makefile").write_text("# fake\n")
            return "abc123"

        monkeypatch.setattr(patching, "clone_template", fake_clone)

        info = {"template": {"url": "https://example.com/repo.git"}}
        result = patching._clone_template_for_patch(info, tmp_path)
        assert result == tmp_path
        assert (result / "Makefile").exists()

    def test_monorepo_subdir_returns_subdir_root(self, tmp_path, monkeypatch):
        def fake_clone(url, target_path, branch=None):
            target_path.mkdir(parents=True, exist_ok=True)
            sub = target_path / "templates" / "agent-loop"
            sub.mkdir(parents=True)
            (sub / "Makefile").write_text("# agent makefile\n")
            (target_path / "README.md").write_text("# monorepo root\n")
            return "abc123"

        monkeypatch.setattr(patching, "clone_template", fake_clone)

        info = {
            "template": {
                "url": "https://example.com/agent-template",
                "subdir": "templates/agent-loop",
            }
        }
        result = patching._clone_template_for_patch(info, tmp_path)
        assert result == tmp_path / "templates" / "agent-loop"
        assert (result / "Makefile").exists()
        # Crucially, monorepo-root files are NOT visible to the patch comparator
        assert not (result / "README.md").exists()

    def test_missing_subdir_raises(self, tmp_path, monkeypatch):
        def fake_clone(url, target_path, branch=None):
            target_path.mkdir(parents=True, exist_ok=True)
            return "abc123"

        monkeypatch.setattr(patching, "clone_template", fake_clone)

        info = {
            "template": {
                "url": "https://example.com/agent-template",
                "subdir": "templates/missing",
            }
        }
        with pytest.raises(FileNotFoundError, match="templates/missing"):
            patching._clone_template_for_patch(info, tmp_path)


# ---------------------------------------------------------------------------
# E2E test — `patch check` on a freshly-scaffolded agent project
# ---------------------------------------------------------------------------


def _make_fake_agent_template(
    template_root: Path, makefile_body: str = "# template makefile\n"
) -> None:
    """Build a minimal agent-loop template tree under template_root."""
    template_root.mkdir(parents=True, exist_ok=True)
    (template_root / "Makefile").write_text(makefile_body)
    (template_root / "Containerfile").write_text("FROM ubi9\n")
    (template_root / "AGENTS.md").write_text("# template\n")

    chart = template_root / "chart"
    (chart / "templates").mkdir(parents=True)
    (chart / "Chart.yaml").write_text("name: agent-template\nversion: 0.1.0\n")
    (chart / "values.yaml").write_text("image: agent-template\n")
    (chart / "templates" / "deployment.yaml").write_text("# deploy\n")

    claude = template_root / ".claude" / "commands"
    claude.mkdir(parents=True)
    (claude / "plan-agent.md").write_text("# plan command\n")


def _make_fake_agent_project(project_root: Path) -> None:
    """Build a minimal scaffolded agent project, simulating create-agent output."""
    project_root.mkdir(parents=True, exist_ok=True)
    # Match the template baseline so most files are unchanged
    _make_fake_agent_template(project_root)
    # User-customized values (must never be patched)
    (project_root / "chart" / "values.yaml").write_text("image: my-agent\n")
    (project_root / "src").mkdir()
    (project_root / "src" / "agent.py").write_text("# user code\n")
    (project_root / "agent.yaml").write_text("model:\n  name: my-model\n")
    (project_root / "pyproject.toml").write_text('[project]\nname = "my-agent"\n')

    info = {
        "generator": {"tool": "fips-agents-cli", "version": "0.0.0-test"},
        "template": {
            "url": "https://github.com/fips-agents/agent-template",
            "type": "agent",
            "subdir": "templates/agent-loop",
            "commit": "abcdef123456",
            "full_commit": "abcdef1234567890",
        },
        "project": {"name": "my-agent", "created_at": "2026-01-01T00:00:00+00:00"},
    }
    (project_root / ".template-info").write_text(json.dumps(info, indent=2))


class TestPatchAgentE2E:
    """End-to-end: scaffolded agent project + `patch check` finds drift correctly."""

    @pytest.fixture
    def agent_project(self, tmp_path):
        project = tmp_path / "my-agent"
        _make_fake_agent_project(project)
        return project

    def test_patch_check_reports_no_drift_when_template_unchanged(
        self, agent_project, monkeypatch, cli_runner
    ):
        # Stub clone_template to drop the same content the project was scaffolded from
        def fake_clone(url, target_path, branch=None):
            sub = target_path / "templates" / "agent-loop"
            _make_fake_agent_template(sub)
            return "abcdef1234567890"

        monkeypatch.setattr(patching, "clone_template", fake_clone)
        monkeypatch.chdir(agent_project)

        result = cli_runner.invoke(cli, ["patch", "check"])
        assert result.exit_code == 0, result.output
        assert "up to date" in result.output

    def test_patch_check_reports_drift_in_agent_categories(
        self, agent_project, monkeypatch, cli_runner
    ):
        # Template's Makefile has changed since scaffold time → "build" should appear
        def fake_clone(url, target_path, branch=None):
            sub = target_path / "templates" / "agent-loop"
            _make_fake_agent_template(sub, makefile_body="# UPDATED template makefile\n")
            return "newcommit12345"

        monkeypatch.setattr(patching, "clone_template", fake_clone)
        monkeypatch.chdir(agent_project)

        result = cli_runner.invoke(cli, ["patch", "check"])
        assert result.exit_code == 0, result.output
        assert "Available Updates" in result.output
        assert "build" in result.output
        # Crucially, MCP-only categories must NOT appear for an agent project
        assert "generators" not in result.output
        assert "core" not in result.output

    def test_patch_chart_applies_change_to_agent_project(
        self, agent_project, monkeypatch, cli_runner
    ):
        # Template's chart/templates/deployment.yaml has changed
        def fake_clone(url, target_path, branch=None):
            sub = target_path / "templates" / "agent-loop"
            _make_fake_agent_template(sub)
            (sub / "chart" / "templates" / "deployment.yaml").write_text("# UPDATED deploy\n")
            return "newcommit12345"

        monkeypatch.setattr(patching, "clone_template", fake_clone)
        monkeypatch.chdir(agent_project)

        # `chart` has ask_before_patch=True, so use --skip-confirmation via `all`?
        # Simpler: invoke patch chart with `input="y\n"` to accept the diff
        result = cli_runner.invoke(cli, ["patch", "chart"], input="y\n")
        assert result.exit_code == 0, result.output

        # values.yaml is in NEVER_PATCH — must NOT be touched
        assert (agent_project / "chart" / "values.yaml").read_text() == "image: my-agent\n"
        # User's agent.py is also off-limits
        assert (agent_project / "src" / "agent.py").read_text() == "# user code\n"
        # The drifted template file should now match the template
        assert (
            agent_project / "chart" / "templates" / "deployment.yaml"
        ).read_text() == "# UPDATED deploy\n"

    def test_mcp_only_subcommand_rejected_in_agent_project(
        self, agent_project, monkeypatch, cli_runner
    ):
        # Running `patch generators` (MCP-only) inside an agent project must fail
        # with a clear, type-aware error message — no clone should happen.
        called = {"clone": False}

        def fake_clone(url, target_path, branch=None):
            called["clone"] = True
            return "x"

        monkeypatch.setattr(patching, "clone_template", fake_clone)
        monkeypatch.chdir(agent_project)

        result = cli_runner.invoke(cli, ["patch", "generators"])
        assert result.exit_code == 1
        assert "agent" in result.output
        assert "generators" in result.output
        # Must enumerate the available agent categories
        for cat in AGENT_FILE_CATEGORIES:
            assert cat in result.output
