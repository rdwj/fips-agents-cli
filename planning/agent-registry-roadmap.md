# Agent Registry — Research and Roadmap

**Date:** 2026-04-10
**Status:** Research complete, not yet planned for implementation

## Concept

`fips-agents create registry my-registry` deploys a self-hosted registry to OpenShift with a UI for browsing and managing registered agents, MCP servers, tools, and prompts. Teams register their deployed services with `fips-agents register`, making them discoverable across the organization.

## Industry Landscape (April 2026)

### What exists

**Agent discovery standards:**
- **A2A Agent Cards** — JSON metadata at `/.well-known/agent.json` describing an agent's capabilities, endpoints, and auth. Linux Foundation stewardship. No registry standard yet (active discussion in a2aproject/A2A#741).
- **MCP Server Cards** — `.well-known` metadata for MCP servers, on the 2026 MCP roadmap. The official MCP Registry (registry.modelcontextprotocol.io) has ~2,000 entries but is public/community-oriented, not enterprise.
- **Agent Connect Protocol (ACP)** — Cisco-led (AGNTCY/Linux Foundation), defines REST/OpenAPI for invoking and configuring agents. Complements A2A.

**Cloud provider registries:**
- **AWS Agent Registry** (preview April 2026) — private governed catalog for agents, tools, skills, MCP servers. Semantic search, approval workflows, IAM + OAuth, CloudTrail audit. Auto-discovers from live A2A/MCP endpoints.
- **Microsoft Entra Agent Registry** — agent identity and governance in the Microsoft ecosystem.
- **Google Vertex AI Agent Builder** — tool governance layer with admin-curated catalogs.

**Open source:**
- **mcp-gateway-registry** (agentic-community) — OAuth (Keycloak/Entra), per-tool RBAC, audit trails, reverse proxy to MCP servers. Closest to what we'd want.
- **kagent** — Kubernetes-native agentic AI, CRD-based. Early stage.

**Prompt registries:**
- MLflow Prompt Registry, Langfuse, PromptLayer, LangSmith — versioning, environment aliases, A/B testing. Standalone products, not integrated with agent/tool registries.

**Red Hat direction:**
- MCP registry, catalog, and gateway stack planned for OpenShift AI
- MCP servers as items in the AI Assets catalog
- Longer-term "MCP-as-a-Service" vision

### What's missing

No single open-source system unifies agents, MCP servers, tools, and prompts in one governed catalog with Kubernetes-native lifecycle. The pieces exist in isolation:
- AWS has the richest registry but is cloud-locked
- MCP has a public registry but no enterprise governance
- Prompt registries are standalone products
- RBAC is protocol-specific (no cross-protocol standard)
- A2A deliberately punts on the registry problem

### RBAC for agents

Traditional RBAC is insufficient — agents chain multi-step plans autonomously. Emerging model is **dynamic RBAC**: bind an agent's declared purpose + operational context + verified identity to minimal, temporary permissions. Per-tool RBAC (mcp-gateway-registry), relationship-based access (Oso ReBAC), and IAM-based governance (AWS) are the main approaches.

## What We'd Build

### Phase 1: Discovery registry (near-term, after composable capabilities)

A lightweight catalog service that stores and serves metadata:

```
fips-agents create registry my-registry    # Deploy to OpenShift
fips-agents register                       # Register current project
```

**What it stores:**
- Agent Cards (A2A-compatible JSON) — name, description, capabilities, endpoint, version
- MCP Server Cards — name, tools list, endpoint, transport
- Tool manifests — name, description, parameters, which agent/MCP server provides them
- Prompt entries — name, description, version, variables, template preview

**How registration works:**
- `fips-agents register` reads the current project type and metadata:
  - Agent: reads `/.well-known/agent.json` from the running service (or generates from agent.yaml)
  - MCP server: reads tool list from the running server (or from project structure)
  - Prompts: reads from `prompts/` directory
- Pushes the metadata to the registry's API
- Registry stores it and makes it browsable

**UI:**
- Browse agents, MCP servers, tools, prompts in a web dashboard
- Search by name, capability, description
- View agent cards, tool schemas, prompt templates
- Show deployment status (healthy/unhealthy via health probes)
- Links to OpenShift console for the underlying deployments

**Tech stack:**
- Go server (consistent with gateway/UI templates) or Python FastAPI
- PostgreSQL for metadata storage
- OpenShift Route for the UI
- Helm chart for deployment
- Periodic health checks against registered endpoints

### Phase 2: Governance (later)

Add approval workflows, RBAC, and audit:
- Admin approval required before an agent/tool is visible to others
- Role-based access: who can register, who can discover, who can invoke
- Audit trail: who registered what, when, who accessed it
- Integration with OpenShift RBAC (ServiceAccounts, Roles)
- Keycloak/OIDC for auth (follow mcp-gateway-registry pattern)

### Phase 3: Enterprise tool/prompt catalog (distant)

- Curated enterprise tools that any agent can use (governed, versioned)
- Enterprise prompt library with approval workflows
- Agent RBAC: which agents can use which tools (policy-based)
- Integration with Red Hat's AI Hub / OpenShift AI catalog

## CLI Integration

```bash
# Deploy a registry
fips-agents create registry my-registry
cd my-registry && make deploy PROJECT=my-registry

# Register the thing you're working on
cd ../my-agent
fips-agents register                          # auto-detect project type, register with default registry
fips-agents register --registry my-registry   # explicit registry
fips-agents register --type agent             # force type
fips-agents register --type mcp-server

# Browse
fips-agents registry list                     # list all registered items
fips-agents registry list --type agent        # filter by type
fips-agents registry search "web search"      # semantic search
```

The `register` command could also be a post-deploy hook in the Makefile:
```makefile
deploy: ## Deploy to OpenShift and register
	helm upgrade --install ...
	fips-agents register --registry $(REGISTRY_URL)
```

## Open Questions

1. **Storage**: PostgreSQL vs CRDs? CRDs are more Kubernetes-native but harder to query. PostgreSQL is simpler for search and UI.
2. **Health monitoring**: Should the registry actively poll registered endpoints, or rely on passive registration updates?
3. **Scope**: Should the registry be namespace-scoped, cluster-scoped, or multi-cluster?
4. **Red Hat alignment**: How does this relate to Red Hat's planned MCP catalog in OpenShift AI? Complement or conflict?
5. **Standards**: Should agent cards be A2A-native, or a superset that includes MCP/tool/prompt metadata?
6. **Auth for registration**: How does `fips-agents register` authenticate with the registry? OpenShift token? API key?

## Relationship to Other Roadmap Items

- **HTTP mode** (Phase 1 of composable capabilities) must ship first — agents need `/.well-known/agent.json` to be registerable
- **A2A agent cards** are already in the gateway template — the registry reads these
- **MCP server template** already produces discoverable tools — the registry catalogs them
- **Multi-agent orchestration** benefits most from a registry — orchestrator agents can discover specialized agents dynamically

## References

- A2A Protocol: https://a2a-protocol.org/latest/specification/
- A2A Registry Discussion: https://github.com/a2aproject/A2A/discussions/741
- MCP Registry: https://registry.modelcontextprotocol.io/
- MCP 2026 Roadmap: https://blog.modelcontextprotocol.io/posts/2026-mcp-roadmap/
- mcp-gateway-registry: https://github.com/agentic-community/mcp-gateway-registry
- AWS Agent Registry: https://aws.amazon.com/blogs/machine-learning/the-future-of-managing-agents-at-scale-aws-agent-registry-now-in-preview/
- AGNTCY ACP Spec: https://github.com/agntcy/acp-spec
- kagent: https://kagent.dev/
