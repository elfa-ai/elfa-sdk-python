# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Important**: First read `AGENT.md` for base instructions that apply to all AI coding assistants. This file contains Claude Code-specific extensions and overrides.

## This repository is public

Everything here is world-readable and permanent: code, comments, commit messages, branch names, PR titles and descriptions, review replies and issue comments. Forks and archives keep copies after a force-push, and GitHub keeps every earlier version of an edited PR description where anyone can read it. So never write any of the following, in the repo or on GitHub:

- names of Elfa's private repositories, or links to their PRs, issues or commits (`org/repo#123`, `repo#123`, URLs)
- internal service names or codenames. Name the public thing instead: "the API", "Auto", "the published spec", "docs.elfa.ai"
- paths into private source code, internal hostnames, staging or preview URLs
- teammates' names in prose, internal threads or decisions ("X confirmed in-thread"). A `Co-authored-by:` trailer crediting a contributor is fine and must be kept
- anything not yet live on docs.elfa.ai: unreleased, flag-gated or staging-only work
- deployment, infrastructure, incident or business detail
- secrets, local machine paths, personal editor or agent config (`.mcp.json`, `.claude/`)

To say where a change came from, cite the public source ("matches the spec published on docs.elfa.ai"), not the internal change behind it. Before pushing, reread the diff, commit messages and PR description as an outsider would. If a sentence would tell a competitor something about how Elfa builds software, cut it.

## Claude Code Specific Instructions

### Task Management
- Always use TodoWrite and TodoRead tools to track progress on multi-step tasks
- Mark todos as completed immediately after finishing each task
- Break down complex features into specific, actionable todo items

### Development Workflow
Use these commands frequently during development:
- `make check` - Essential pre-commit validation (lint + type-check + test)
- `pytest tests/test_specific_file.py` - Run specific test files
- `make test-coverage` - Verify test coverage for new code

### Before Merging a PR
**A green check does not mean a clean review.** Sourcery reviews this repo and
posts its findings as a `COMMENTED` review — which does not block, and whose
check run reports `pass` regardless of what it found. `gh pr checks` showing all
green proves the reviewer *ran*, not that it had nothing to say.

Read the review content itself before merging:

```bash
gh api repos/elfa-ai/elfa-sdk-python/pulls/<n>/reviews  --jq '.[]|"[\(.user.login)] \(.body)"'
gh api repos/elfa-ai/elfa-sdk-python/pulls/<n>/comments --jq '.[]|"\(.path):\(.line) \(.body)"'
gh pr view <n> --comments
```

Triage every finding: fix it, or reply on the comment saying why not. This is
not hypothetical — three PRs were merged in `elfa-sdk-js` on the strength of a
green Sourcery check and every one of them carried a valid finding that had to
be fixed afterwards.

**Squash merges discard commit authorship.** GitHub attributes the squashed
commit to whoever opened the PR. When a PR contains someone else's commits, put
a `Co-authored-by:` trailer in your own commit *before* merging — afterwards the
attribution cannot be recovered without rewriting `main`.

### Multi-Tool Usage
- Batch multiple independent file reads in single tool calls for efficiency
- Use parallel bash commands when running multiple independent operations
- Prefer Edit/MultiEdit over Write for existing files

## Architecture Summary

See `AGENT.md` for complete architecture details. Key Claude Code considerations:

### File Navigation Patterns
When exploring the codebase, reference components by their file paths:
- `elfa/client/elfa_client.py` - Sync `ElfaClient` (data + chat, `.auto`, `.v3`)
- `elfa/client/async_client.py` - `AsyncElfaClient`
- `elfa/client/auto_client.py` - Auto engine
- `elfa/client/v3_client.py` - API v3 (`V3Client` / `AsyncV3Client`), models in `elfa/models/v3.py`
- `elfa/client/_params.py` - shared data param builders
- `elfa/utils/{http,sse}.py` - transport, SSE
- `elfa/models/__init__.py` - All available Pydantic models
- `elfa/exceptions/__init__.py` - Exception hierarchy

### API v3
`client.v3` covers the fourteen `/v3` `GET` endpoints: events, storylines and arcs; call
books, mindshare and trending contracts; calls, call episodes and positioning; ranked
accounts; key status.
```python
import time

bitcoin = client.v3.get_entities("btc", entity_type=["token"], limit=1).entities[0]
since = int(time.time()) - 86400
events = client.v3.get_events(entity_ids=[bitcoin.id], from_time=since, limit=10)
positioning = client.v3.get_positioning(bitcoin.id)
```
Rules to respect in code and tests:
- Times are unix seconds; milliseconds are a `400`. `from_time` is required except when
  fetching by id or searching with `q`, and `get_events(sort="relevant")` refuses it;
  entities, arcs, positioning and top accounts take no range.
- Entity filters take an id from `get_entities`, never a ticker or name.
- History is 30 days, 60 days or 2 years back, by plan: `get_key_status().history_from`.
- PAYG, Grow and Enterprise keys can call every v3 endpoint; a Free key only
  `get_key_status()`, the rest answer `403` ("The v3 API is free on the Pay-as-you-go and
  Grow plans. Upgrade at …").
- Unknown parameters are a `400`: never send one the endpoint does not declare. Lists go
  out comma-separated.
- Chat takes `include_sources`; sources come back on `data.sources` or the stream's
  `complete` event.

### Code Generation Guidelines
- Always import required types from `elfa.models` and `elfa.exceptions`
- Follow existing client method patterns for consistency
- Go through the transport (`self._transport.request_json(...)`) and `parse_model(...)`
- Add data param mapping to `elfa/client/_params.py`, not inline
- For Auto mutations, go through `MountedClient` and send compact bytes (`content=`)

### Testing Approach
- Create both sync and async test variants for new client methods
- Mock HTTP responses using `respx` (works for sync and async httpx)
- Test error scenarios with appropriate exception assertions
- Maintain test coverage above 90% for new code
