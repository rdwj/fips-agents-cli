# Retrospective: Full Stack Integration and Agent Template Fixes

**Date:** 2026-04-10
**Effort:** Integration test UI → Gateway → Agent on OpenShift, fix all agent template bugs, close gateway/UI issues, release v0.5.1, build a working search agent, plan composable capabilities
**Issues closed:** gateway-template #1, #4, #5; ui-template #2, #5; agent-template 12 bugs (no issue tracker)
**Filed:** agent-template #19 (tool_use message ordering)
**Release:** v0.5.1 (PyPI)
**Commits:** 9748e0b..03927b7 (CLI), 4993c05..cc36289 (gateway), add7901..84ef204 (UI), 9efa650..4093298 (agent-template)

## What We Set Out To Do

1. Integration test the full stack (UI → Gateway → Agent) on OpenShift
2. Fix bugs found during testing
3. Close high-priority issues on gateway (#5 tests, #1 logging, #4 BuildConfig) and UI (#5 tests, #2 markdown)
4. Fix all 12 agent-template bugs from the gap analysis
5. Add HTTP mode to the agent template (stretch goal)

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| Added reverse proxy to UI server | Good pivot | CORS issue discovered during integration — browser can't cross-origin fetch to gateway. Proxy is the correct architecture (keeps internal URLs internal). |
| HTTP mode deferred | Scope deferral | Enough shipped without it. Building `add` command framework first makes the feature composable rather than baked-in. |
| Composable capabilities planning | Good pivot | Search agent experience crystallized the vision — agents need layered capabilities, not monolithic templates. |
| Agent registry research | Good pivot | User-initiated strategic planning. AWS launched Agent Registry the same day — validated the concept. |
| v0.5.0 → v0.5.1 re-cut | Missed | Pre-existing Black formatting drift in two test files. Local `black --check` caught it but only on changed files; CI checks all files. |

## What Went Well

- **Full stack worked on first deploy** — agent, gateway, UI all running and streaming through three layers with no proxy/SSE bugs
- **Parallel agent execution** — gateway tests, UI tests, and markdown rendering all built concurrently. Agent-template Python fixes and infra fixes also ran in parallel. Significant time savings.
- **OpenShift BuildConfig** replaced ec2-dev remote builds cleanly — simpler, no external dependency
- **Search agent validated the scaffolding end-to-end** — `create agent` → customize → real Tavily + Anthropic → working agent in minutes
- **Bug fix thoroughness** — all 12 template bugs fixed, verified by separate review agent, 360 tests passing
- **Chat UI was surprisingly polished** — streaming, markdown rendering, responsive design all worked well in the browser

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| v0.5.0 CI failed (Black drift in test files we didn't touch) | Fixed | Committed formatting, re-cut as v0.5.1 |
| Tool_use/tool_result message ordering bug in example agent | Follow-up issue | agent-template#19 |
| No CI workflows on gateway-template or ui-template repos | Follow-up | Tests exist and pass locally but no GitHub Actions |
| `generate tool` vs `add tool` command overlap unresolved | Follow-up | Design captured in planning/composable-agent-capabilities.md |
| ResearchAssistant example is overcomplex for a starting point | Accept | Will simplify when HTTP mode ships |

## Action Items

- [ ] Fix agent-template#19 (tool_use ordering) — blocks Anthropic-powered agents
- [ ] Add CI workflows to gateway-template and ui-template repos
- [ ] Build HTTP mode and `add` command framework (next session priority)
- [ ] Add MemoryHub and web-search as first `add` capabilities

## Patterns

**Start:** Run `black --check src tests` (all files, not just changed) before cutting a release. The CI checks everything; local checks should match.

**Start:** When building agent step loops that use tool calling, always append the assistant message (with tool_calls) before appending tool results. This is an Anthropic API requirement and should be documented in the template.

**Continue:** Parallel sub-agent execution for independent work streams — consistently saves time with no coordination overhead.

**Continue:** OpenShift BuildConfig for builds — simpler than remote builds, no external infrastructure needed.

**Continue:** Deploying and testing the real stack on OpenShift rather than just running unit tests locally. The CORS issue, WORKDIR permissions, and tool_use ordering bug were all found only through integration testing.
