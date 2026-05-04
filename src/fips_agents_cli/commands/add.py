"""Add command group for wiring capabilities into existing agent projects."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

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


@add.command("code-executor")
def code_executor_cmd():
    """Wire sandbox code execution into the current agent project.

    Adds the code_executor tool to tools/ and enables the sandbox sidecar
    in chart/values.yaml. Run from your agent project root directory.

    Example:

        cd my-research-agent

        fips-agents add code-executor
    """
    try:
        project_root = _resolve_agent_project_or_exit()
        console.print(f"[green]Found project root:[/green] {project_root}")

        try:
            result = apply_modality(project_root, CODE_EXECUTOR_SPEC)
        except ModalityError as e:
            console.print(f"\n[red]Error:[/red] {e}")
            sys.exit(1)

        _print_modality_result(CODE_EXECUTOR_SPEC, result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
