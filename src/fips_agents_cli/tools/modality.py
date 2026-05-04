"""Apply composable capabilities ("modalities") to existing agent projects.

A *modality* is a capability that the user opts into after their agent
project has already been scaffolded — file uploads, vision input, voice,
video, sandbox code execution, and so on. The agent template ships every
modality in a disabled state (``enabled: false`` in ``agent.yaml`` and
``chart/values.yaml``) plus any sidecar templates guarded by Helm
conditionals. The CLI's job is to flip those toggles atomically and drop
in any source-file scaffolds the modality needs.

This module models a modality declaratively as a :class:`ModalitySpec`.
:func:`apply_modality` walks the spec and applies every change
idempotently. New ``add`` subcommands should be a few lines of glue
around a spec and a single :func:`apply_modality` call — no more
hand-written string replacement, which is what motivated this module
(see ``commands/add.py``'s pre-refactor ``code-executor`` for the
pattern we are replacing).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import tomlkit
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap


class ModalityError(Exception):
    """Raised when a modality cannot be applied to a project."""


@dataclass(frozen=True)
class SourceFile:
    """A source file the modality drops into the project tree.

    Attributes:
        relative_path: Path relative to the project root (POSIX style).
        content: Full file content to write.
        skip_if_exists: When true (the default), an existing file at the
            target path is left untouched and the action is recorded as
            "skipped". When false, the file is overwritten.
    """

    relative_path: str
    content: str
    skip_if_exists: bool = True


@dataclass(frozen=True)
class PyprojectExtra:
    """An optional-dependencies extra to add to ``pyproject.toml``.

    Attributes:
        name: Extra name, e.g. ``"files"``. Becomes a key under
            ``[project.optional-dependencies]``.
        dependencies: Requirement strings, e.g.
            ``["docling>=2.0", "boto3>=1.34"]``.
    """

    name: str
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class ModalitySpec:
    """Declarative description of a modality the user can ``add``.

    Every field except ``name`` and ``description`` is optional — a
    modality may need only a chart toggle (e.g. ``code-executor``), only
    a source-file drop, or any combination. ``apply_modality`` only
    touches the files the spec actually references.
    """

    name: str
    description: str

    #: Dotted key path inside ``agent.yaml`` whose value should be set
    #: to ``True``. For example ``"server.files.enabled"`` flips the
    #: ``files.enabled`` field nested under the ``server`` block.
    agent_yaml_enable: str | None = None

    #: Dotted key path inside ``chart/values.yaml`` whose value should be
    #: set to ``True``. For example ``"sandbox.enabled"`` or
    #: ``"files.enabled"``.
    chart_values_enable: str | None = None

    #: Source files to write into the project.
    source_files: tuple[SourceFile, ...] = ()

    #: Optional extra to register under ``[project.optional-dependencies]``.
    pyproject_extra: PyprojectExtra | None = None

    #: Cross-modality precondition. Receives the project root and returns
    #: ``(ok, message)``. When ``ok`` is false, ``apply_modality`` raises
    #: :class:`ModalityError` with ``message`` and makes no changes.
    precondition: Callable[[Path], tuple[bool, str]] | None = None

    #: Plain-text follow-up steps printed by the calling command after a
    #: successful apply. Each entry is rendered as a separate line.
    next_steps: tuple[str, ...] = ()


@dataclass
class ModalityResult:
    """Outcome of an :func:`apply_modality` call.

    The result is informational — :func:`apply_modality` raises on
    unrecoverable errors. Anything in ``warnings`` is non-fatal: the
    modality is partially applied and the user should be told.
    """

    actions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def apply_modality(project_root: Path, spec: ModalitySpec) -> ModalityResult:
    """Apply ``spec`` to the agent project rooted at ``project_root``.

    The function is idempotent: running it twice is a no-op the second
    time (every step is a "skipped" entry in the result). Unrecoverable
    errors (precondition failure, malformed YAML, missing target file
    that the spec strictly requires) raise :class:`ModalityError`.
    Recoverable surprises (target section missing, key not present)
    surface as warnings and the rest of the spec still applies.

    Args:
        project_root: Path to the agent project root.
        spec: The modality to apply.

    Returns:
        :class:`ModalityResult` describing every action taken.
    """
    if not project_root.is_dir():
        raise ModalityError(f"Project root does not exist: {project_root}")

    if spec.precondition is not None:
        ok, message = spec.precondition(project_root)
        if not ok:
            raise ModalityError(message)

    result = ModalityResult()

    for source in spec.source_files:
        _apply_source_file(project_root, source, result)

    if spec.agent_yaml_enable is not None:
        _toggle_yaml_key(
            project_root / "agent.yaml",
            spec.agent_yaml_enable,
            result,
            file_label="agent.yaml",
        )

    if spec.chart_values_enable is not None:
        _toggle_yaml_key(
            project_root / "chart" / "values.yaml",
            spec.chart_values_enable,
            result,
            file_label="chart/values.yaml",
        )

    if spec.pyproject_extra is not None:
        _add_pyproject_extra(project_root / "pyproject.toml", spec.pyproject_extra, result)

    return result


def _apply_source_file(project_root: Path, source: SourceFile, result: ModalityResult) -> None:
    target = project_root / source.relative_path
    if target.exists() and source.skip_if_exists:
        result.skipped.append(f"{source.relative_path} already exists")
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.content)
    result.actions.append(f"Wrote {source.relative_path}")


def _toggle_yaml_key(
    yaml_path: Path,
    dotted_key: str,
    result: ModalityResult,
    *,
    file_label: str,
) -> None:
    """Set ``dotted_key`` to ``True`` in the YAML file at ``yaml_path``.

    Uses ruamel.yaml in round-trip mode so existing comments, key order,
    and string-quoting style are preserved. Missing files / missing
    intermediate keys produce warnings instead of errors so the rest of
    the modality can still apply (e.g. a project without a Helm chart
    can still get its tool source files dropped in).
    """
    if not yaml_path.exists():
        result.warnings.append(f"No {file_label} found — skipped {dotted_key} toggle")
        return

    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        with open(yaml_path) as f:
            data = yaml.load(f)
    except Exception as e:
        raise ModalityError(f"Failed to parse {file_label}: {e}") from e

    if not isinstance(data, CommentedMap):
        raise ModalityError(f"{file_label} root is not a mapping")

    parts = dotted_key.split(".")
    cursor: CommentedMap = data
    for part in parts[:-1]:
        if not isinstance(cursor, CommentedMap) or part not in cursor:
            result.warnings.append(
                f"{file_label} has no '{'.'.join(parts[: parts.index(part) + 1])}' "
                f"section — set {dotted_key}: true manually"
            )
            return
        cursor = cursor[part]

    leaf = parts[-1]
    if not isinstance(cursor, CommentedMap) or leaf not in cursor:
        result.warnings.append(
            f"{file_label} has no '{dotted_key}' field — set it to true manually"
        )
        return

    current = cursor[leaf]
    if current is True:
        result.skipped.append(f"{dotted_key} already true in {file_label}")
        return

    cursor[leaf] = True
    try:
        with open(yaml_path, "w") as f:
            yaml.dump(data, f)
    except Exception as e:
        raise ModalityError(f"Failed to write {file_label}: {e}") from e

    result.actions.append(f"Set {dotted_key}: true in {file_label}")


def _add_pyproject_extra(
    pyproject_path: Path, extra: PyprojectExtra, result: ModalityResult
) -> None:
    """Register ``extra`` under ``[project.optional-dependencies]``.

    Merges with an existing extra of the same name (deduplicating by
    requirement string). tomlkit preserves comments and formatting in
    ``pyproject.toml``, matching the rest of the codebase's TOML edits.
    """
    if not pyproject_path.exists():
        result.warnings.append(
            f"No pyproject.toml found — declare the [{extra.name}] extra manually"
        )
        return

    try:
        doc = tomlkit.parse(pyproject_path.read_text())
    except Exception as e:
        raise ModalityError(f"Failed to parse pyproject.toml: {e}") from e

    project = doc.setdefault("project", tomlkit.table())
    optional = project.setdefault("optional-dependencies", tomlkit.table())

    if extra.name in optional:
        existing = list(optional[extra.name])
        before = len(existing)
        for dep in extra.dependencies:
            if dep not in existing:
                existing.append(dep)
        if len(existing) == before:
            result.skipped.append(f"[{extra.name}] extra already declares all deps")
            return
        optional[extra.name] = existing
        action = f"Updated [{extra.name}] extra in pyproject.toml"
    else:
        optional[extra.name] = list(extra.dependencies)
        action = f"Added [{extra.name}] extra to pyproject.toml"

    pyproject_path.write_text(tomlkit.dumps(doc))
    result.actions.append(action)
