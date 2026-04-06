# Retrospective: Issue Triage and v0.3.0 Release

**Date:** 2026-04-06
**Effort:** Triage and fix both open issues, ship v0.3.0
**Issues:** #1, #2
**Commits:** 292d528, 6936c0f, 2311673

## What We Set Out To Do

Review the two open issues in the backlog, fix them, and publish a new release. Both issues were well-scoped and appeared straightforward.

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| Issue #2 flipped from "remove stale flags" to "add missing `--hook-type` option" | Good pivot | Audit revealed the flags never existed; the real gap was the CLI not providing a variable that deployed templates already used |
| Issue #2 description no longer matches the fix | Missed | The `Fixes #2` commit closes the issue, but the title/description describe the opposite of what was done |

## What Went Well

- Parallel sub-agent execution: both fixes developed simultaneously with no conflicts
- Review step confirmed correctness before committing
- Clean commit separation (one per issue + release commit)
- Established label taxonomy (bug, cleanup, test, generate-command, create-command) for future triage
- Issue #2 worker correctly identified the real problem rather than blindly following a potentially stale issue description

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| No integration test of `--hook-type` against a real Jinja2 template | Follow-up issue | #3 |
| Release commit message didn't follow convention (`release: vX.Y.Z — ...`) | Follow-up issue | #4 |
| Issue #2 description doesn't match the actual fix | Accept | Issue is closed; context is in the commit message |

## Action Items

- [ ] Add integration tests for `--hook-type` with real templates (#3)
- [ ] Document and enforce release commit format in CLAUDE.md and `release.sh` (#4)

## Patterns

**Start:** Audit before filing issues — #2 was based on an assumption that turned out wrong. A quick `grep` before writing the issue would have produced a more accurate description.
**Start:** Enforce release commit format via the release script itself, not human discipline.
**Continue:** Parallel sub-agent execution for independent fixes — worked cleanly here.
**Continue:** Review step before committing — caught nothing this time, but the cost is low and the safety net matters.
