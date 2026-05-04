"""Tests for the modality helper used by `fips-agents add` subcommands."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from ruamel.yaml import YAML

from fips_agents_cli.cli import cli
from fips_agents_cli.commands.add import CODE_EXECUTOR_SPEC
from fips_agents_cli.tools.modality import (
    ModalityError,
    ModalitySpec,
    PyprojectExtra,
    SourceFile,
    apply_modality,
)
from fips_agents_cli.tools.project import find_agent_project_root

FIXTURE_SOURCE = Path(__file__).parent / "fixtures" / "agent_project"


@pytest.fixture
def agent_project(tmp_path: Path) -> Path:
    """Copy the committed agent fixture into a tmp dir for safe mutation."""
    dest = tmp_path / "myagent"
    shutil.copytree(FIXTURE_SOURCE, dest)
    return dest


def _yaml_load(path: Path):
    yaml = YAML()
    with open(path) as f:
        return yaml.load(f)


# ---------------------------------------------------------------------------
# find_agent_project_root
# ---------------------------------------------------------------------------


class TestFindAgentProjectRoot:
    def test_finds_via_template_info(self, agent_project: Path) -> None:
        nested = agent_project / "tools"
        nested.mkdir(exist_ok=True)
        assert find_agent_project_root(start=nested) == agent_project

    def test_finds_via_agent_yaml_when_no_template_info(self, agent_project: Path) -> None:
        (agent_project / ".template-info").unlink()
        assert find_agent_project_root(start=agent_project) == agent_project

    def test_returns_none_outside_a_project(self, tmp_path: Path) -> None:
        assert find_agent_project_root(start=tmp_path) is None

    def test_skips_non_agent_template_info(self, tmp_path: Path) -> None:
        # An mcp-server project should NOT be returned as an agent project,
        # even if its .template-info is found while walking up.
        (tmp_path / ".template-info").write_text('{"template": {"type": "mcp-server"}}')
        assert find_agent_project_root(start=tmp_path) is None


# ---------------------------------------------------------------------------
# apply_modality — chart/values.yaml toggle
# ---------------------------------------------------------------------------


class TestChartValuesToggle:
    def test_flips_top_level_enabled_field(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="sandbox",
            description="Sandbox sidecar",
            chart_values_enable="sandbox.enabled",
        )
        result = apply_modality(agent_project, spec)
        assert "Set sandbox.enabled: true in chart/values.yaml" in result.actions

        values = _yaml_load(agent_project / "chart" / "values.yaml")
        assert values["sandbox"]["enabled"] is True
        # Sibling fields untouched
        assert values["sandbox"]["profile"] == "minimal"
        assert values["replicaCount"] == 1

    def test_flips_nested_persistence_enabled(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="files-persist",
            description="Files persistence",
            chart_values_enable="files.persistence.enabled",
        )
        apply_modality(agent_project, spec)
        values = _yaml_load(agent_project / "chart" / "values.yaml")
        assert values["files"]["persistence"]["enabled"] is True
        assert values["files"]["enabled"] is False  # untouched

    def test_idempotent_on_already_true_value(self, agent_project: Path) -> None:
        # Pre-flip the value, then run apply twice — second pass should
        # report skipped, not re-write.
        values_path = agent_project / "chart" / "values.yaml"
        text = values_path.read_text().replace(
            "sandbox:\n  enabled: false", "sandbox:\n  enabled: true", 1
        )
        values_path.write_text(text)

        spec = ModalitySpec(
            name="sandbox",
            description="Sandbox sidecar",
            chart_values_enable="sandbox.enabled",
        )
        result = apply_modality(agent_project, spec)
        assert any("already true" in s for s in result.skipped)
        assert result.actions == []

    def test_warns_on_missing_section(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="bogus",
            description="Bogus",
            chart_values_enable="nonexistent.enabled",
        )
        result = apply_modality(agent_project, spec)
        assert any("nonexistent" in w for w in result.warnings)
        assert result.actions == []

    def test_warns_on_missing_values_yaml(self, agent_project: Path) -> None:
        (agent_project / "chart" / "values.yaml").unlink()
        spec = ModalitySpec(
            name="sandbox",
            description="Sandbox sidecar",
            chart_values_enable="sandbox.enabled",
        )
        result = apply_modality(agent_project, spec)
        assert any("chart/values.yaml" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# apply_modality — agent.yaml toggle
# ---------------------------------------------------------------------------


class TestAgentYamlToggle:
    def test_flips_nested_server_files_enabled(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="files",
            description="File uploads",
            agent_yaml_enable="server.files.enabled",
        )
        result = apply_modality(agent_project, spec)
        assert any("server.files.enabled: true in agent.yaml" in a for a in result.actions)

        loaded = _yaml_load(agent_project / "agent.yaml")
        assert loaded["server"]["files"]["enabled"] is True
        # Sibling untouched
        assert (
            loaded["server"]["files"]["max_file_size_bytes"] == "${FILES_MAX_SIZE_BYTES:-52428800}"
        )
        assert loaded["server"]["traces"]["enabled"] == "${TRACES_ENABLED:-false}"

    def test_preserves_comments_and_env_var_substitutions(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="files",
            description="File uploads",
            agent_yaml_enable="server.files.enabled",
        )
        apply_modality(agent_project, spec)

        text = (agent_project / "agent.yaml").read_text()
        # Comments preserved
        assert "# -- File uploads (optional)" in text
        # Unrelated env-var substitutions preserved verbatim
        assert "${MODEL_NAME:-meta-llama/Llama-3.3-70B-Instruct}" in text
        assert "${TRACES_ENABLED:-false}" in text


# ---------------------------------------------------------------------------
# apply_modality — source files
# ---------------------------------------------------------------------------


class TestSourceFiles:
    def test_writes_new_file(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="vision",
            description="Vision",
            source_files=(SourceFile("tools/vision_helper.py", "# vision helper\n"),),
        )
        result = apply_modality(agent_project, spec)
        assert "Wrote tools/vision_helper.py" in result.actions
        assert (agent_project / "tools" / "vision_helper.py").read_text() == ("# vision helper\n")

    def test_skips_existing_file_by_default(self, agent_project: Path) -> None:
        existing = agent_project / "tools" / "vision_helper.py"
        existing.write_text("# original\n")
        spec = ModalitySpec(
            name="vision",
            description="Vision",
            source_files=(SourceFile("tools/vision_helper.py", "# replacement\n"),),
        )
        result = apply_modality(agent_project, spec)
        assert any("already exists" in s for s in result.skipped)
        assert existing.read_text() == "# original\n"

    def test_overwrites_when_skip_disabled(self, agent_project: Path) -> None:
        existing = agent_project / "tools" / "vision_helper.py"
        existing.write_text("# original\n")
        spec = ModalitySpec(
            name="vision",
            description="Vision",
            source_files=(
                SourceFile(
                    "tools/vision_helper.py",
                    "# replacement\n",
                    skip_if_exists=False,
                ),
            ),
        )
        result = apply_modality(agent_project, spec)
        assert "Wrote tools/vision_helper.py" in result.actions
        assert existing.read_text() == "# replacement\n"

    def test_creates_intermediate_directories(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="deep",
            description="Deep",
            source_files=(SourceFile("integrations/voice/stt.py", "# stt\n"),),
        )
        apply_modality(agent_project, spec)
        assert (agent_project / "integrations" / "voice" / "stt.py").exists()


# ---------------------------------------------------------------------------
# apply_modality — pyproject extras
# ---------------------------------------------------------------------------


class TestPyprojectExtras:
    def test_adds_new_extra(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="files",
            description="File uploads",
            pyproject_extra=PyprojectExtra(name="files", dependencies=("docling>=2.0",)),
        )
        result = apply_modality(agent_project, spec)
        assert "Added [files] extra to pyproject.toml" in result.actions

        text = (agent_project / "pyproject.toml").read_text()
        assert 'files = ["docling>=2.0"]' in text or '"docling>=2.0"' in text

    def test_merges_into_existing_extra(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="metrics-plus",
            description="Metrics plus",
            pyproject_extra=PyprojectExtra(
                name="metrics", dependencies=("opentelemetry-api>=1.20",)
            ),
        )
        result = apply_modality(agent_project, spec)
        assert "Updated [metrics] extra in pyproject.toml" in result.actions

        text = (agent_project / "pyproject.toml").read_text()
        # Pre-existing dep preserved, new dep added
        assert "prometheus-client" in text
        assert "opentelemetry-api" in text

    def test_idempotent_when_dep_already_present(self, agent_project: Path) -> None:
        spec = ModalitySpec(
            name="metrics-noop",
            description="Metrics noop",
            pyproject_extra=PyprojectExtra(
                name="metrics", dependencies=("prometheus-client>=0.20",)
            ),
        )
        result = apply_modality(agent_project, spec)
        assert any("already declares all deps" in s for s in result.skipped)


# ---------------------------------------------------------------------------
# apply_modality — preconditions
# ---------------------------------------------------------------------------


class TestPreconditions:
    def test_failing_precondition_raises_and_makes_no_changes(self, agent_project: Path) -> None:
        def precondition(_root: Path) -> tuple[bool, str]:
            return False, "vision must be enabled before video"

        spec = ModalitySpec(
            name="video",
            description="Video preprocessing",
            chart_values_enable="files.enabled",  # would mutate if it ran
            precondition=precondition,
        )
        with pytest.raises(ModalityError, match="vision must be enabled"):
            apply_modality(agent_project, spec)

        # Project state is untouched
        values = _yaml_load(agent_project / "chart" / "values.yaml")
        assert values["files"]["enabled"] is False

    def test_passing_precondition_lets_the_apply_run(self, agent_project: Path) -> None:
        def precondition(_root: Path) -> tuple[bool, str]:
            return True, ""

        spec = ModalitySpec(
            name="files",
            description="Files",
            chart_values_enable="files.enabled",
            precondition=precondition,
        )
        apply_modality(agent_project, spec)
        values = _yaml_load(agent_project / "chart" / "values.yaml")
        assert values["files"]["enabled"] is True


# ---------------------------------------------------------------------------
# Integration — `fips-agents add code-executor` end-to-end
# ---------------------------------------------------------------------------


class TestAddCodeExecutorE2E:
    def test_first_run_writes_tool_and_toggles_chart(
        self, agent_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(agent_project)
        runner = CliRunner()
        result = runner.invoke(cli, ["add", "code-executor"])
        assert result.exit_code == 0, result.output

        assert (agent_project / "tools" / "code_executor.py").exists()
        values = _yaml_load(agent_project / "chart" / "values.yaml")
        assert values["sandbox"]["enabled"] is True
        assert "Sandbox code execution added" in result.output

    def test_second_run_is_idempotent(
        self, agent_project: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(agent_project)
        runner = CliRunner()
        runner.invoke(cli, ["add", "code-executor"])
        result = runner.invoke(cli, ["add", "code-executor"])
        assert result.exit_code == 0, result.output
        assert "already exists" in result.output
        assert "already true" in result.output

    def test_errors_when_not_in_an_agent_project(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        runner = CliRunner()
        result = runner.invoke(cli, ["add", "code-executor"])
        assert result.exit_code == 1
        assert "Not in an agent project" in result.output


# ---------------------------------------------------------------------------
# Spec validation — the existing CODE_EXECUTOR_SPEC stays consistent
# ---------------------------------------------------------------------------


class TestCodeExecutorSpec:
    def test_spec_has_expected_shape(self) -> None:
        # Guard against accidental edits drifting the spec away from what
        # the existing add code-executor implementation guarantees.
        assert CODE_EXECUTOR_SPEC.name == "code-executor"
        assert CODE_EXECUTOR_SPEC.chart_values_enable == "sandbox.enabled"
        assert CODE_EXECUTOR_SPEC.agent_yaml_enable is None
        assert CODE_EXECUTOR_SPEC.pyproject_extra is None
        assert len(CODE_EXECUTOR_SPEC.source_files) == 1
        assert CODE_EXECUTOR_SPEC.source_files[0].relative_path == "tools/code_executor.py"
