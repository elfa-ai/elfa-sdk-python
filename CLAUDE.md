# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Important**: First read `AGENT.md` for base instructions that apply to all AI coding assistants. This file contains Claude Code-specific extensions and overrides.

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

### Multi-Tool Usage
- Batch multiple independent file reads in single tool calls for efficiency
- Use parallel bash commands when running multiple independent operations
- Prefer Edit/MultiEdit over Write for existing files

## Architecture Summary

See `AGENT.md` for complete architecture details. Key Claude Code considerations:

### File Navigation Patterns
When exploring the codebase, reference components by their file paths:
- `elfa/client/elfa_client.py` - Sync `ElfaClient` (data + chat, `.auto`/`.trade`)
- `elfa/client/async_client.py` - `AsyncElfaClient`
- `elfa/client/auto_client.py` / `trade_client.py` - Auto/Trade engines
- `elfa/client/_params.py` - shared data param builders
- `elfa/utils/{http,hmac,sse}.py` - transport, signing, SSE
- `elfa/models/__init__.py` - All available Pydantic models
- `elfa/exceptions/__init__.py` - Exception hierarchy

### Code Generation Guidelines
- Always import required types from `elfa.models` and `elfa.exceptions`
- Follow existing client method patterns for consistency
- Go through the transport (`self._transport.request_json(...)`) and `parse_model(...)`
- Add data param mapping to `elfa/client/_params.py`, not inline
- For Auto/Trade mutations, sign via `SignedClient` and send compact bytes (`content=`)

### Testing Approach
- Create both sync and async test variants for new client methods
- Mock HTTP responses using `respx` (works for sync and async httpx)
- Test error scenarios with appropriate exception assertions
- Maintain test coverage above 90% for new code
