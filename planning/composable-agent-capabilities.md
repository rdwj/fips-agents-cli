# Composable Agent Capabilities — Planning

**Date:** 2026-04-10
**Status:** Discussion, not yet implemented

## Vision

The CLI evolves from "scaffold once" to "scaffold + compose." Agents start lean and gain capabilities through `add` commands. Each capability is a template fragment (files, deps, config) that the CLI layers into an existing project.

## Command Design

### Current commands
- `create agent|mcp-server|gateway|ui` — scaffold a new project
- `generate tool|resource|prompt|middleware` — add a single MCP component from Jinja2 template

### Proposed: `add` command
- `add http` — FastAPI server + health probes + agent card + uvicorn CMD
- `add tool <name>` — add a pre-built tool (web-search, code-executor, etc.)
- `add memory` — MemoryHub integration (config init, dependency, schema)
- `add rag` — RAG client (LlamaStack or equivalent connection, retrieval tool)
- `add sessions` — conversation state persistence (Redis/PostgreSQL)
- `add observability` — structured logging, metrics

### Command relationship
- `generate` creates a **single component file** from a Jinja2 template (MCP-oriented)
- `add` layers a **whole capability** (multiple files, dependencies, config, tests)
- `add tool` should detect project type (MCP server vs agent) and generate the right decorator/structure. This requires consistent tree structure across templates.

### Slash command relationship
- CLI `add` commands handle **structural changes** (files, deps, Containerfile)
- Slash commands handle **behavioral configuration** (agent.yaml tuning, prompt design, tool parameters)
- Example flow: `fips-agents add tool web-search` → `/configure-search` in Claude Code

## Capability Tiers

### Tier 1 — Almost every agent
1. **HTTP mode** — FastAPI, /v1/chat/completions, health probes, A2A agent card
2. **Web search** — Tavily/Brave with rate limiting
3. **Observability** — structured logging, optional Prometheus metrics

### Tier 2 — Common
4. **Memory** — MemoryHub integration (already partially wired in base_agent)
5. **Code execution** — sandboxed Python/shell via sidecar container
6. **RAG** — client-side connection to LlamaStack or equivalent (not rebuilding RAG infra)
7. **Sessions** — Redis/PostgreSQL conversation state

### Tier 3 — Specialized
8. **A2A discovery** — agent-to-agent calling, registry
9. **Auth** — OAuth2/OIDC middleware
10. **Multi-model routing** — cheap model for classification, expensive for generation
11. **File handling** — upload/download, temp storage

## Code Execution Design

Recommended: **sidecar container** approach.
- `add tool code-executor` adds the tool to the agent AND a sidecar to the Helm chart
- Agent sends code to sidecar via localhost HTTP
- Sidecar runs in a locked-down container (no network, resource limits, timeout)
- Stronger isolation than in-process subprocess, simpler than managing a separate MCP server
- Advanced path: MCP code-execution server for shared infrastructure

## RAG Design

Don't rebuild RAG — connect to it.
- LlamaStack provides vector store, embedding, retrieval out of the box
- `add rag` sets up the client side: config for the RAG endpoint, retrieval tool, ingestion tool
- The RAG infrastructure (LlamaStack, vLLM for embeddings, vector DB) is separate
- Agent template provides the wiring pattern, not the infrastructure
- This will likely need a full session to design and implement properly

## Multi-Agent Design

Building blocks already exist:
- Each agent has `/.well-known/agent.json` (A2A agent card)
- Gateway routes between agents
- UI connects to any OpenAI-compatible endpoint

Orchestration pattern:
- An "orchestrator" agent discovers other agents via their agent cards
- Delegates subtasks via HTTP to specialized agents
- Each agent is independently deployable and scalable
- Gateway provides the routing layer

This is the natural evolution of the current stack (agent + gateway + UI) into a multi-agent system. The `add a2a` command would wire up the discovery and calling patterns.

## Memory Design

MemoryHub integration is partially wired into base_agent already:
- `agent.yaml` has a `memory:` section pointing to `.memoryhub.yaml`
- `base_agent/memory.py` has `create_memory_client()` that falls back to NullMemoryClient
- `add memory` command would: install memoryhub dep, run `memoryhub config init`, offer `/configure-memory` slash command for schema design

This is a quick win — most of the framework code exists.

## Prioritization

### Phase 1: HTTP mode + `add` framework
- HTTP mode is the #1 blocker (every agent that needs a URL)
- Building the `add` infrastructure enables everything else
- Reference implementation: `demo-fips-agent-builder/src/server.py`

### Phase 2: Memory + web search as first `add` capabilities  
- Memory (MemoryHub) is partially wired, quick to finish
- Web search validates the `add tool` pattern (we have a working Tavily implementation)
- These are two different shapes: memory is config/framework, web search is a tool file

### Phase 3: Code executor + RAG client
- Code executor validates the sidecar pattern (Helm chart changes)
- RAG client connects to LlamaStack (full session needed for design)

### Phase 4: Multi-agent orchestration
- A2A discovery and inter-agent calling
- Orchestrator pattern on top of the gateway
- Builds on HTTP mode foundation

## Open Questions

1. Should `add tool` auto-detect project type (MCP vs agent) or require explicit context?
2. Where do capability template fragments live — in the CLI package, or in the template repos?
3. How do we version capability fragments independently from the base templates?
4. For RAG: do we standardize on LlamaStack, or support multiple backends?
5. For multi-agent: does the gateway need to become aware of multiple backends, or is that a separate orchestration layer?

## Key Bug Found This Session

redhat-ai-americas/agent-template#19: The example agent doesn't append the assistant's tool_use message before tool_result messages, violating the Anthropic API contract. Must fix before HTTP mode ships, since it affects every agent using Anthropic.
