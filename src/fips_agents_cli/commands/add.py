"""Add command group for wiring capabilities into existing agent projects."""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

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


def _find_agent_project_root() -> Path | None:
    """Find the agent project root by looking for agent.yaml."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "agent.yaml").exists():
            return parent
    return None


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
        # Step 1: Detect project root
        project_root = _find_agent_project_root()
        if project_root is None:
            console.print(
                "[red]Error:[/red] Not in an agent project directory.\n"
                "Could not find agent.yaml in this directory or any parent.\n\n"
                "[yellow]Hint:[/yellow] Run this command from an agent project "
                "created with [dim]fips-agents create agent[/dim]."
            )
            sys.exit(1)

        console.print(f"[green]Found project root:[/green] {project_root}")

        # Step 2: Check tools/ directory exists
        tools_dir = project_root / "tools"
        if not tools_dir.exists():
            console.print(
                "[red]Error:[/red] No tools/ directory found in project root.\n\n"
                "[yellow]Hint:[/yellow] Create it with: [dim]mkdir tools[/dim]"
            )
            sys.exit(1)

        # Step 3: Write the tool file
        tool_file = tools_dir / "code_executor.py"
        if tool_file.exists():
            console.print(
                "[yellow]Warning:[/yellow] tools/code_executor.py already exists. Skipping."
            )
        else:
            tool_file.write_text(CODE_EXECUTOR_TOOL_SOURCE)
            console.print("[green]+[/green] Created tools/code_executor.py")

        # Step 4: Update chart/values.yaml if present
        values_file = project_root / "chart" / "values.yaml"
        if values_file.exists():
            values_content = values_file.read_text()
            if "sandbox:" in values_content:
                if "enabled: false" in values_content:
                    values_content = values_content.replace("enabled: false", "enabled: true", 1)
                    values_file.write_text(values_content)
                    console.print("[green]+[/green] Set sandbox.enabled: true in chart/values.yaml")
                elif "enabled: true" in values_content:
                    console.print("[dim]sandbox.enabled already true in chart/values.yaml[/dim]")
                else:
                    console.print(
                        "[yellow]Warning:[/yellow] Found sandbox: section in "
                        "chart/values.yaml but could not locate enabled field. "
                        "Please set sandbox.enabled: true manually."
                    )
            else:
                console.print(
                    "[yellow]Warning:[/yellow] No sandbox: section in chart/values.yaml.\n"
                    "  Add the following to your values.yaml:\n"
                    "  [dim]sandbox:\n"
                    "    enabled: true\n"
                    "    image: <your-sandbox-image>[/dim]"
                )
        else:
            console.print("[dim]No chart/values.yaml found (not using Helm chart). Skipping.[/dim]")

        # Step 5: Success panel
        next_steps = """
[bold cyan]Next Steps:[/bold cyan]

  1. Build or deploy the sandbox sidecar:
     [dim]fips-agents create sandbox my-sandbox[/dim]
     or use the pre-built image from fips-agents/code-sandbox

  2. Configure the sandbox URL for your agent:

     [bold]Sidecar mode[/bold] (same pod, default):
       The tool defaults to http://localhost:8000
       No extra config needed if sandbox runs as a sidecar container.

     [bold]Remote service mode[/bold] (separate deployment):
       Set the SANDBOX_URL environment variable:
       [dim]export SANDBOX_URL=http://sandbox-service:8000[/dim]

  3. The agent will auto-discover tools/code_executor.py.
     Use it in your agent's step() by calling:
       [dim]await self.use_tool("code_executor", code="print(1+1)")[/dim]
"""

        console.print(
            Panel(
                f"[bold green]Code executor tool added.[/bold green]\n{next_steps}",
                border_style="green",
                padding=(1, 2),
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        sys.exit(1)
