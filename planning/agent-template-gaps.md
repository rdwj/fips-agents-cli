# Agent Template Gap Analysis and Roadmap

**Date:** 2026-04-10
**Source:** End-to-end test of agent scaffolding workflow (`fips-agents create agent demo-fips-agent-builder`), followed by adding an HTTP/conversational layer, configuring for Anthropic, and deploying to OpenShift.

---

## Template Bugs

These are defects in the `redhat-ai-americas/agent-template` repository. A scaffolded project should work out of the box -- passing its own linting, building cleanly, and deploying without manual patching.

### 1. Lint errors ship with the template

**Severity:** Medium
**Files:** `src/agent.py`, `src/base_agent/agent.py`, `src/base_agent/prompts.py`, `tests/test_agent.py`, `tests/test_example_agent.py`, `tests/test_skills.py`

11 lint errors (unused imports) exist in a freshly scaffolded project. Running `ruff check` on a brand-new project should produce zero errors.

### 2. `make run-local` doesn't work

**Severity:** High
**File:** `src/agent.py`

There is no `__main__` block. `python -m src.agent` fails with no entry point. The Makefile advertises a target that doesn't function.

### 3. `OWNER/REPO` placeholder in Containerfile

**Severity:** Low
**File:** `Containerfile`

The label `io.opencontainers.image.source` retains the placeholder `OWNER/REPO` instead of being customized during scaffolding. The `customize_agent_project` pipeline should string-replace this.

### 4. `agent-template` hardcoded in deploy.sh

**Severity:** High
**File:** `deploy.sh`, line 55

`helm upgrade --install agent-template` uses the literal template name instead of the `$APP_NAME` variable. Every deployment installs under the wrong release name.

### 5. Helm helper names not customized

**Severity:** High
**File:** `chart/templates/_helpers.tpl`

All helper definitions reference `agent-template.fullname`, `agent-template.labels`, etc. These are not updated during scaffolding, causing Helm resource name collisions if multiple agents are deployed to the same namespace.

### 6. `ruff` not in dev dependencies

**Severity:** Low
**File:** `pyproject.toml`

The Makefile lint target works around this by auto-installing ruff, but it should be declared in `[project.optional-dependencies.dev]` so that `pip install -e .[dev]` brings it in.

### 7. Optional COPY glob patterns fail on OpenShift BuildConfig

**Severity:** High
**File:** `Containerfile`

`COPY .memoryhub.yam[l] ./` and `COPY AGENTS.m[d] ./` use a bracket-glob trick (copy if file exists, skip otherwise) that works with Docker/Podman but fails with OpenShift BuildConfig. The build errors with `copier: stat: no such file or directory`.

**Fix options:**
- Use a multi-stage approach where optional files are copied in a separate stage
- Use a `.containerignore`-based approach
- Create empty placeholder files in the template

### 8. Builder stage user permissions

**Severity:** High
**File:** `Containerfile`

The UBI Python image defaults to UID 1001, but `pip install .` needs write access to create `.egg-info`. Build fails with `Cannot update time stamp of directory`.

**Fix:** Add `USER 0` to the builder stage (not the runtime stage, which should remain non-root).

### 9. `LLMConfig.endpoint` doesn't support empty/None

**Severity:** Medium
**File:** `src/base_agent/config.py`

The Pydantic model has `endpoint: str = "http://llamastack:8321/v1"`. This breaks when using hosted providers (Anthropic, OpenAI) where litellm handles routing automatically and no `api_base` should be set.

**Fix:** Change to `endpoint: str | None = None` and only pass `api_base` to litellm when the value is truthy.

### 10. BuildConfig needs explicit `dockerfilePath`

**Severity:** Medium
**Context:** OpenShift deployment

OpenShift BuildConfig defaults to looking for `Dockerfile`. When using `Containerfile` (Red Hat convention), the build fails silently or falls back to S2I.

**Fix:** Patch the BuildConfig with `dockerStrategy.dockerfilePath: Containerfile`, or add this to `deploy.sh`.

### 11. Deployment template missing container port

**Severity:** Medium
**File:** `chart/templates/deployment.yaml`

No `ports` section in the container spec. The Service targets port name `http` but the container doesn't declare it, causing connection failures.

### 12. Health probes commented out

**Severity:** Low
**File:** `chart/templates/deployment.yaml`

Liveness and readiness probes are commented out with a note to "uncomment when the agent exposes a health endpoint." For HTTP-mode agents (see roadmap below), these should be active by default.

### Bug Summary

| # | Description | Severity | Effort |
|---|-------------|----------|--------|
| 1 | 11 lint errors in scaffolded project | Medium | Small |
| 2 | `make run-local` broken (no entry point) | High | Small |
| 3 | `OWNER/REPO` placeholder not customized | Low | Small |
| 4 | `agent-template` hardcoded in deploy.sh | High | Small |
| 5 | Helm helper names not customized | High | Medium |
| 6 | `ruff` missing from dev dependencies | Low | Small |
| 7 | COPY glob patterns fail on OpenShift | High | Medium |
| 8 | Builder stage UID permissions | High | Small |
| 9 | `LLMConfig.endpoint` breaks hosted providers | Medium | Small |
| 10 | BuildConfig needs `dockerfilePath` | Medium | Small |
| 11 | Deployment template missing container port | Medium | Small |
| 12 | Health probes commented out | Low | Small |

---

## Strategic Gaps

These are missing capabilities that surfaced during the end-to-end exercise. They represent the difference between "template that compiles" and "template that gets you to production."

### Gap 1: No HTTP/API Surface

**Priority:** Critical
**Impact:** Blocks all conversational and service-oriented agent use cases

The template produces a batch agent loop. Conversational agents -- the most common type -- need an HTTP endpoint. During the demo, we had to manually add FastAPI, a chat completions endpoint, health checks, and an A2A agent card. This was the largest source of manual work.

**Proposed solution:** Add a `--mode` flag to `fips-agents create agent`:

- `--mode=batch` (current behavior) -- headless agent loop, no HTTP server
- `--mode=http` (new) -- adds FastAPI server with standard endpoints

The HTTP mode should scaffold:

| File | Purpose |
|------|---------|
| `src/server.py` | FastAPI app with `/v1/chat/completions` (sync + SSE streaming) |
| Health endpoints | `/healthz` (liveness), `/readyz` (readiness) |
| `/.well-known/agent.json` | A2A Agent Card for discovery |
| Updated Containerfile | `CMD` runs uvicorn instead of agent loop |
| Updated Makefile | `run-local` starts the HTTP server |
| Updated Helm chart | Probes enabled, port configured, route created |

### Gap 2: No Polyglot Support

**Priority:** Low (long-term)
**Impact:** Performance ceiling for high-concurrency streaming workloads

Python + uvicorn handles most workloads, but Go is significantly better for managing thousands of concurrent SSE connections, heartbeats, and graceful shutdown.

**Phased approach:**

- **Phase 1:** Python-only HTTP mode (FastAPI + uvicorn). Covers 80% of use cases. This is Gap 1 above.
- **Phase 2:** Go gateway + Python backend (`--with-gateway` flag). Go handles HTTP routing, SSE lifecycle, rate limiting. Python handles agent logic, LLM calls, tool execution.
- **Phase 3:** Full Go agent template for Go-native agents (`fips-agents create agent --lang=go`).

### Gap 3: No UI Template

**Priority:** Medium
**Impact:** Every demo and internal tool needs a chat UI; teams rebuild it each time

**Proposed:** `fips-agents create ui <name>` or `--with-ui` flag on `create agent`.

Requirements:
- Minimal React or plain HTML/JS chat interface
- Connects to the OpenAI-compatible `/v1/chat/completions` endpoint
- Supports SSE streaming for real-time token display
- Deployable as a separate pod or as static files served by the agent

### Gap 4: No Agent-to-Agent Discovery

**Priority:** Medium
**Impact:** Prevents agents from discovering and calling each other

The A2A Agent Card (`/.well-known/agent.json`) is trivial to add and enables agent discovery. It should be standard in HTTP mode.

Contents should include: agent name, description, capabilities, supported models, API interface, authentication requirements.

### Gap 5: OpenShift BuildConfig Not Integrated

**Priority:** Medium
**Impact:** Deploy workflow assumes manual image build and push

The current deploy path requires building a container locally (or remotely), pushing to a registry, then deploying. OpenShift's BuildConfig with `oc start-build --from-dir` eliminates the registry step entirely.

**Proposed additions:**
- `make build-openshift` target in Makefile
- BuildConfig resource in Helm chart (with `dockerfilePath: Containerfile`)
- Updated `deploy.sh` to optionally use BuildConfig

### Gap 6: No Secret Management Guidance

**Priority:** Medium
**Impact:** Teams hardcode API keys or struggle with OpenShift secrets

The template uses ConfigMap for environment variables but has no guidance or tooling for secrets (LLM API keys, database credentials).

**Proposed additions:**
- `make create-secret` target that prompts for API key and creates an OpenShift Secret
- Deployment template mounts the Secret as environment variables
- `AGENTS.md` documents the secret management workflow

### Gap 7: Conversation State Management

**Priority:** Low (long-term)
**Impact:** Stateful agents require server-side session tracking

The HTTP server is stateless -- the client sends full conversation history with each request. This works for simple use cases but breaks down for agents that need to maintain context across many turns or across clients.

**Phased approach:**
- **Phase 1:** Stateless (current). Client manages history. Good enough for most use cases.
- **Phase 2:** Optional session management. `--with-sessions` flag adds Redis or PostgreSQL-backed session storage with a `session_id` parameter on the chat endpoint.

---

## API Surface Standard

Every HTTP-mode agent should expose these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/healthz` | GET | Kubernetes liveness probe |
| `/readyz` | GET | Kubernetes readiness probe |
| `/.well-known/agent.json` | GET | A2A Agent Card for discovery |
| `/v1/chat/completions` | POST | OpenAI-compatible chat (sync + SSE streaming) |

**Rationale:**

- OpenAI chat completions is the universal standard. vLLM, Ollama, LiteLLM, and every chat UI speak this format. Using it means agents are instantly compatible with existing tooling.
- A2A Agent Card is a lightweight JSON document that enables agent-to-agent discovery without a central registry.
- Health endpoints are mandatory for Kubernetes deployments. Without them, OpenShift can't determine if the pod is alive or ready to serve traffic.

---

## Polyglot Architecture

For most agents, Python-only is the right choice. The Go gateway is an optimization for specific workloads.

```
Default (Python-only):
  Pod -> FastAPI (port 8080, exposed via Route)

With Go gateway (future):
  Pod -> Go gateway (port 8080, exposed) -> Python backend (port 8081, localhost only)
```

**Responsibility split with Go gateway:**

| Layer | Handles |
|-------|---------|
| Go gateway | HTTP routing, SSE connection lifecycle, heartbeats, rate limiting, graceful shutdown, request validation |
| Python backend | Agent logic, LLM calls, tool execution, RAG pipelines, prompt management |

This split keeps the agent developer focused on Python while the gateway handles the operational concerns that Go excels at.

---

## Roadmap

Ordered by impact and dependency. Items higher on the list unblock items lower on the list.

| Phase | Item | Repo | Effort | Unblocks |
|-------|------|------|--------|----------|
| **1** | Fix 12 template bugs (above) | agent-template | 1-2 days | Everything -- scaffolded projects must work before adding features |
| **2** | Add HTTP mode to template | agent-template | 3-5 days | Conversational agents, health probes, A2A |
| **3** | Add `--mode` flag to CLI | fips-agents-cli | 1-2 days | User-facing scaffolding of HTTP agents |
| **4** | Add OpenShift BuildConfig integration | agent-template | 1-2 days | Smoother deployment without external registry |
| **5** | Add A2A Agent Card | agent-template | 0.5 days | Agent-to-agent discovery |
| **6** | Add secret management tooling | agent-template | 1 day | Secure API key handling |
| **7** | Add UI template | fips-agents-cli + new repo | 3-5 days | Self-contained agent+UI deployments |
| **8** | Add Go gateway option | agent-template | 5-10 days | High-concurrency streaming workloads |
| **9** | Add session management | agent-template | 3-5 days | Stateful conversations |

### Phase 1: Fix What's Broken (Week 1)

All 12 template bugs. PRs against `redhat-ai-americas/agent-template`. No CLI changes needed -- the bugs are all in the template itself.

Key deliverables:
- Clean lint pass on scaffolded projects
- Working `make run-local`
- Working OpenShift BuildConfig builds
- Correct Helm release names per project

### Phase 2-3: HTTP Mode (Weeks 2-3)

The template gets a `server.py` with FastAPI, health endpoints, and OpenAI-compatible chat completions. The CLI gets `--mode=http|batch` on `create agent`.

Key deliverables:
- `fips-agents create agent my-agent --mode=http` produces a working HTTP agent
- Agent responds to `/v1/chat/completions` with sync and streaming responses
- Helm chart has probes enabled, port configured, Route created
- `make run-local` starts the HTTP server on port 8080

### Phase 4-6: Production Readiness (Weeks 4-5)

BuildConfig integration, A2A Agent Card, and secret management. These are incremental improvements that make the template production-ready without manual patching.

### Phase 7-9: Ecosystem (Months 2-3)

UI template, Go gateway, and session management. These are higher-effort items that expand what's possible rather than fixing what's broken.

---

## Appendix: Changes Required in fips-agents-cli

When the template gains HTTP mode, the CLI needs corresponding changes:

1. **`commands/create.py`** -- Add `--mode` option to `create agent` command (choices: `batch`, `http`; default: `batch`)
2. **`tools/project.py`** -- `customize_agent_project` needs to handle mode-specific file selection (include/exclude `server.py`, configure Helm probes, set Containerfile CMD)
3. **`tests/test_create.py`** -- Add test cases for `--mode=http` scaffolding
4. **`CLAUDE.md`** -- Document the new flag and its effects
5. **Validation** -- `--mode=http` should verify that the template version supports HTTP mode and fail with a clear message if not
