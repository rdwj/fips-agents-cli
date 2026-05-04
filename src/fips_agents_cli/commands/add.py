"""Add command group for wiring capabilities into existing agent projects."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from ruamel.yaml import YAML

from fips_agents_cli.tools.modality import (
    ModalityError,
    ModalityResult,
    ModalitySpec,
    SourceFile,
    apply_modality,
)
from fips_agents_cli.tools.project import find_agent_project_root

console = Console()


# The code_executor tool source, embedded directly to avoid network dependencies.
# Source: agent-template/examples/code-sandbox-agent/tools/code_executor.py
CODE_EXECUTOR_TOOL_SOURCE = '''\
"""Code execution tool — sends Python code to the sandbox sidecar."""

import os

import httpx

from fipsagents.baseagent.tools import tool

SANDBOX_URL = os.environ.get("SANDBOX_URL", "http://localhost:8000")


@tool(
    description="Execute Python code in an isolated sandbox and return the output. "
    "Use this for any computation, math, data processing, or logic that "
    "benefits from exact results. The code runs in a restricted environment "
    "with access to: math, statistics, itertools, functools, re, datetime, "
    "collections, json, csv, string, textwrap, decimal, fractions, random, "
    "operator, typing. Use print() to produce output.",
    visibility="llm_only",
)
async def code_executor(code: str, timeout: float = 10.0) -> str:
    """Execute Python code in the sandbox sidecar.

    Args:
        code: Python source code to execute. Must use print() for output.
        timeout: Maximum execution time in seconds (1-30).
    """
    timeout = max(1.0, min(timeout, 30.0))

    async with httpx.AsyncClient(timeout=timeout + 5) as client:
        try:
            resp = await client.post(
                f"{SANDBOX_URL}/execute",
                json={"code": code, "timeout": timeout},
            )
        except httpx.ConnectError:
            return (
                "ERROR: Cannot connect to sandbox sidecar at "
                f"{SANDBOX_URL}. Is it running?"
            )
        except httpx.TimeoutException:
            return "ERROR: Request to sandbox timed out."

    data = resp.json()

    if resp.status_code == 400:
        if "violations" in data:
            violations = "\\n".join(f"  - {v}" for v in data["violations"])
            return f"CODE BLOCKED by sandbox guardrails:\\n{violations}"
        return f"ERROR: {data.get(\'error\', \'Unknown error\')}"

    stdout = data.get("stdout", "").strip()
    stderr = data.get("stderr", "").strip()
    exit_code = data.get("exit_code", -1)
    timed_out = data.get("timed_out", False)

    if timed_out:
        return f"TIMEOUT: Code exceeded {timeout}s limit.\\nPartial output:\\n{stdout}"

    parts = []
    if stdout:
        parts.append(stdout)
    if stderr:
        parts.append(f"STDERR:\\n{stderr}")
    if exit_code != 0:
        parts.append(f"(exit code {exit_code})")

    return "\\n".join(parts) if parts else "(no output — did you forget print()?)"
'''


CODE_EXECUTOR_NEXT_STEPS = (
    "1. Build or deploy the sandbox sidecar:",
    "   [dim]fips-agents create sandbox my-sandbox[/dim]",
    "   or use the pre-built image from fips-agents/code-sandbox",
    "",
    "2. Configure the sandbox URL for your agent:",
    "",
    "   [bold]Sidecar mode[/bold] (same pod, default):",
    "     The tool defaults to http://localhost:8000",
    "     No extra config needed if sandbox runs as a sidecar container.",
    "",
    "   [bold]Remote service mode[/bold] (separate deployment):",
    "     Set the SANDBOX_URL environment variable:",
    "     [dim]export SANDBOX_URL=http://sandbox-service:8000[/dim]",
    "",
    "3. The agent will auto-discover tools/code_executor.py.",
    "   Use it in your agent's step() by calling:",
    '     [dim]await self.use_tool("code_executor", code="print(1+1)")[/dim]',
)


CODE_EXECUTOR_SPEC = ModalitySpec(
    name="code-executor",
    description="Sandbox code execution",
    chart_values_enable="sandbox.enabled",
    source_files=(
        SourceFile(
            relative_path="tools/code_executor.py",
            content=CODE_EXECUTOR_TOOL_SOURCE,
        ),
    ),
    next_steps=CODE_EXECUTOR_NEXT_STEPS,
)


FILES_NEXT_STEPS = (
    r"1. Install the \[files] extra (pulls in docling + python-magic):",
    r"   [dim]pip install -e '.\[files]'[/dim]",
    "",
    "2. Choose a persistence backend by setting FILES_BACKEND:",
    "   [bold]sqlite[/bold] (dev / single-replica)",
    "     [dim]export FILES_BACKEND=sqlite[/dim]",
    "   [bold]postgres[/bold] (production / multi-replica)",
    "     [dim]export FILES_BACKEND=postgres[/dim]",
    "     [dim]export DATABASE_URL=postgresql://...[/dim]",
    "",
    "3. (Optional) For multi-replica deployments use the S3 bytes backend:",
    "   [dim]chart/values.yaml: files.bytesBackend.type=s3 + bucket/region/credentials[/dim]",
    "",
    "4. (Optional) Enable the ClamAV virus-scanner sidecar:",
    "   [dim]chart/values.yaml: files.virusScanner.enabled=true[/dim]",
    "",
    "5. (Optional) Persist uploaded bytes across pod restarts (PVC):",
    "   [dim]chart/values.yaml: files.persistence.enabled=true[/dim]",
    "",
    "6. Upload a file and reference it in chat completions:",
    "   [dim]curl -F file=@doc.pdf $AGENT_URL/v1/files[/dim]",
    "   The response carries a file_id; pass it on subsequent",
    "   /v1/chat/completions requests via the file_ids field.",
)


FILES_SPEC = ModalitySpec(
    name="files",
    description="File upload and attachment support",
    agent_yaml_enable="server.files.enabled",
    chart_values_enable="files.enabled",
    next_steps=FILES_NEXT_STEPS,
)


# ---------------------------------------------------------------------------
# vision — multimodal (image input) example client
# ---------------------------------------------------------------------------

# A self-contained client snippet showing the three image_url variants the
# server accepts. Lives at examples/vision_client.py — out of the agent
# import path on purpose, since content blocks are constructed by callers,
# not by the agent itself.
VISION_CLIENT_SOURCE = '''\
"""Vision input examples — three ways to send an image to a multimodal agent.

The agent runtime accepts any OpenAI-shaped ``image_url`` content block on
``POST /v1/chat/completions``. The block carries a URL in one of three
forms; the agent (via ``OpenAIChatServer._resolve_image_file_ids``)
rewrites ``file_id:<id>`` references to inline ``data:`` URIs before
forwarding to the model.

Prerequisites:
- Files capability is enabled (``fips-agents add files`` already run).
- The configured ``model.endpoint`` is a vision-capable model (e.g.
  Granite Vision 3.2-2B, LLaVA, Phi-4-Multimodal). Set
  ``MODEL_ENDPOINT`` and ``MODEL_NAME`` accordingly.

Run against a locally-running agent:

    python examples/vision_client.py
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path

import httpx

AGENT_URL = os.environ.get("AGENT_URL", "http://localhost:8080")


def variant_data_uri(image_path: Path) -> dict:
    """Inline the image as a base64 ``data:`` URI.

    Suited for one-shot requests where the image lives on the client
    and you do not need to reference it again.
    """
    mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{encoded}"},
    }


def variant_remote_url(url: str) -> dict:
    """Reference a publicly-fetchable HTTPS URL.

    The model serves the URL itself; no upload is required. Best when
    the image is already on a CDN or public bucket.
    """
    return {"type": "image_url", "image_url": {"url": url}}


def variant_file_id(image_path: Path) -> dict:
    """Upload the image once via POST /v1/files, then reference by id.

    The agent fetches bytes from the configured BytesStore, sniffs the
    MIME type, and rewrites the URL to a ``data:`` URI server-side
    before forwarding to the model. Best when the same image is used
    across multiple turns or sessions.
    """
    with httpx.Client() as client:
        upload = client.post(
            f"{AGENT_URL}/v1/files",
            files={"file": (image_path.name, image_path.read_bytes(), "image/png")},
            timeout=30.0,
        )
        upload.raise_for_status()
        file_id = upload.json()["file_id"]
    return {
        "type": "image_url",
        "image_url": {"url": f"file_id:{file_id}"},
    }


def chat_with_image(prompt: str, image_block: dict) -> str:
    with httpx.Client() as client:
        resp = client.post(
            f"{AGENT_URL}/v1/chat/completions",
            json={
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            image_block,
                        ],
                    }
                ],
                "max_tokens": 128,
                "temperature": 0,
            },
            timeout=60.0,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    image = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./test.png")
    if not image.exists():
        print(f"Image not found: {image}", file=sys.stderr)
        print("Usage: python examples/vision_client.py [path/to/image.png]", file=sys.stderr)
        sys.exit(1)

    print("=== Variant 1: inline data: URI ===")
    print(chat_with_image("Describe this image briefly.", variant_data_uri(image)))

    print("\\n=== Variant 2: remote URL ===")
    # Replace with any public image URL.
    print(
        chat_with_image(
            "Describe this image briefly.",
            variant_remote_url("https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png"),
        )
    )

    print("\\n=== Variant 3: file_id (server-resolved) ===")
    print(chat_with_image("Describe this image briefly.", variant_file_id(image)))
'''


VISION_NEXT_STEPS = (
    "1. Set the agent's model endpoint to a vision-capable model.",
    "   Granite Vision 3.2-2B is the canonical example:",
    "     [dim]export MODEL_ENDPOINT=https://granite-vision-3-2-2b-...:443/v1[/dim]",
    "     [dim]export MODEL_NAME=ibm-granite/granite-vision-3.2-2b[/dim]",
    "",
    "2. Run the agent locally:",
    "   [dim]make run-local[/dim]",
    "",
    "3. Send an image-bearing chat completion. Three URL forms work:",
    "",
    r"   [bold]data:[/bold] inline base64 (\"data:image/png;base64,...\")",
    "   [bold]https://[/bold] remote URL the model fetches",
    "   [bold]file_id:[/bold] internal scheme — upload via POST /v1/files first,",
    "     then reference the returned id; the agent rewrites the URL to",
    "     a data: URI server-side before forwarding to the model.",
    "",
    "4. See examples/vision_client.py for runnable snippets of all three.",
    "",
    "5. Notes:",
    "   - Image input requires fipsagents>=0.20.0 (content-block support).",
    "   - Tool calling is not enabled on most vision endpoints — your",
    "     agent's step() may need to call_model(include_tools=False).",
    "   - Trace spans fingerprint image bytes (SHA-256 + size); raw",
    "     payloads are never logged.",
)


def _vision_precondition(project_root: Path) -> tuple[bool, str]:
    """Vision input only makes sense when files is enabled.

    The ``file_id:<id>`` URL scheme resolves bytes via the configured
    ``BytesStore``, which is only wired up when ``server.files.enabled``
    is true. The other two variants (``data:`` URIs and remote
    ``https://`` URLs) work without files, but the agent's value-add is
    the file_id resolution path — fail fast and tell the user to run
    ``fips-agents add files`` first.
    """
    yaml_path = project_root / "agent.yaml"
    if not yaml_path.exists():
        return False, "agent.yaml not found in this project"

    yaml = YAML()
    try:
        with open(yaml_path) as f:
            data = yaml.load(f)
    except Exception as e:
        return False, f"Failed to parse agent.yaml: {e}"

    server = data.get("server") if hasattr(data, "get") else None
    files = server.get("files") if server is not None and hasattr(server, "get") else None
    enabled = files.get("enabled") if files is not None and hasattr(files, "get") else None

    if enabled is True:
        return True, ""

    return False, (
        "Vision input requires file uploads to be enabled — "
        "the file_id:<id> URL scheme resolves bytes via the agent's "
        "BytesStore. Run `fips-agents add files` first, then re-run "
        "`fips-agents add vision`."
    )


VISION_SPEC = ModalitySpec(
    name="vision",
    description="Multimodal image input via OpenAI content blocks",
    source_files=(
        SourceFile(
            relative_path="examples/vision_client.py",
            content=VISION_CLIENT_SOURCE,
        ),
    ),
    precondition=_vision_precondition,
    next_steps=VISION_NEXT_STEPS,
)


def _print_modality_result(spec: ModalitySpec, result: ModalityResult) -> None:
    """Render the per-action lines + the success panel for an applied spec."""
    for action in result.actions:
        console.print(f"[green]+[/green] {action}")
    for skipped in result.skipped:
        console.print(f"[dim]{skipped}[/dim]")
    for warning in result.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")

    body_lines = [f"[bold green]{spec.description} added.[/bold green]", ""]
    if spec.next_steps:
        body_lines.append("[bold cyan]Next Steps:[/bold cyan]")
        body_lines.append("")
        body_lines.extend(f"  {line}" for line in spec.next_steps)

    console.print(
        Panel(
            "\n".join(body_lines),
            border_style="green",
            padding=(1, 2),
        )
    )


def _resolve_agent_project_or_exit() -> Path:
    project_root = find_agent_project_root()
    if project_root is None:
        console.print(
            "[red]Error:[/red] Not in an agent project directory.\n"
            "Could not find agent.yaml or .template-info in this directory or any parent.\n\n"
            "[yellow]Hint:[/yellow] Run this command from an agent project "
            "created with [dim]fips-agents create agent[/dim]."
        )
        sys.exit(1)
    return project_root


@click.group()
def add():
    """Add capabilities to an existing agent project."""
    pass


def _run_modality(spec: ModalitySpec) -> None:
    """Shared implementation for every `add <modality>` subcommand."""
    try:
        project_root = _resolve_agent_project_or_exit()
        console.print(f"[green]Found project root:[/green] {project_root}")

        try:
            result = apply_modality(project_root, spec)
        except ModalityError as e:
            console.print(f"\n[red]Error:[/red] {e}")
            sys.exit(1)

        _print_modality_result(spec, result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)


@add.command("code-executor")
def code_executor_cmd():
    """Wire sandbox code execution into the current agent project.

    Adds the code_executor tool to tools/ and enables the sandbox sidecar
    in chart/values.yaml. Run from your agent project root directory.

    Example:

        cd my-research-agent

        fips-agents add code-executor
    """
    _run_modality(CODE_EXECUTOR_SPEC)


@add.command("files")
def files_cmd():
    """Enable file upload + attachment support in the current agent project.

    Flips ``server.files.enabled`` in agent.yaml and ``files.enabled`` in
    chart/values.yaml. The agent template already ships the rest of the
    files surface (storage backends, S3, ClamAV sidecar, Docling parsing,
    pgvector chunking) — this command only wires up the toggles. Follow
    the printed next-steps to install the ``[files]`` extra and choose a
    persistence backend.

    Example:

        cd my-research-agent

        fips-agents add files
    """
    _run_modality(FILES_SPEC)


@add.command("vision")
def vision_cmd():
    """Wire multimodal (image input) example client into the project.

    Drops examples/vision_client.py showing the three image_url URL
    forms the agent runtime accepts (inline data:, remote https://,
    and the internal file_id:<id> scheme). Files capability must be
    enabled first — run `fips-agents add files` and re-run.

    Image input runs through the agent's existing model.endpoint —
    no separate vision endpoint split. Set MODEL_ENDPOINT and
    MODEL_NAME to a vision-capable model (e.g. Granite Vision 3.2-2B,
    LLaVA, Phi-4-Multimodal) before running the agent.

    Requires fipsagents>=0.20.0 in the project's dependencies.

    Example:

        cd my-research-agent

        fips-agents add files     # prerequisite

        fips-agents add vision
    """
    _run_modality(VISION_SPEC)
