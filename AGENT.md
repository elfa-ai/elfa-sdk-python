# AGENT.md

This file provides base instructions for all AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) working with this repository.

## Project Overview

**Elfa Python SDK** - Official Python SDK for the Elfa API: social intelligence, AI chat, and the Auto condition engine for crypto. V2-only (no V1 surface).

### Technology Stack
- **Language**: Python 3.9+
- **HTTP Client**: httpx (sync/async support)
- **Data Models**: Pydantic v2 for type safety
- **Testing**: pytest + respx (sync/async mocking)
- **Code Quality**: black, isort, flake8, mypy
- **Build**: setuptools with pyproject.toml

## Development Workflow

### Essential Commands
```bash
# Setup
pip install -e ".[dev,docs]"

# Quality checks (run before commits)
make check  # Combines lint + type-check + test

# Individual checks
make lint      # flake8 linting
make type-check # mypy type checking  
make test      # pytest
make format    # black + isort formatting
```

### Code Quality Standards
- **100% type coverage** - All functions must have type hints
- **Comprehensive error handling** - Use custom exception hierarchy
- **Test coverage** - Maintain high test coverage for new code
- **Documentation** - Docstrings for all public APIs
- **Security** - Never commit API keys or sensitive data

## Architecture Principles

### Data policy
The SDK returns processed metadata and tweet links only — never raw tweet text.
For raw content, call the X (Twitter) API directly with those links/ids.

### Client Structure
- **Sync Client**: `ElfaClient` - data + AI chat (`chat`, `chat_stream`), with `.auto`
- **Async Client**: `AsyncElfaClient` - async mirror of `ElfaClient`
- **Auto engine**: `AutoClient` / `AsyncAutoClient` (`/v2/auto/*`) - EQL queries, drafts, sessions, executions, SSE streams
- **Transport**: `SyncTransport` / `AsyncTransport` (retries, error mapping, SSE)
- **Bodies**: Auto mutations send compact JSON via httpx `content=`, never `json=`.

### Error Handling Pattern
```python
from elfa.exceptions import ElfaAPIError, ElfaAuthenticationError

try:
    result = client.get_trending_tokens()
except ElfaAuthenticationError:
    # Handle auth errors
except ElfaAPIError as e:
    # Handle general API errors
```

## Code Patterns

### Model Definitions
Use Pydantic models for all data structures:
```python
from pydantic import BaseModel
from typing import Optional

class NewModel(BaseModel):
    required_field: str
    optional_field: Optional[int] = None
```

### Client Methods
Data param mapping lives once in `elfa/client/_params.py` (shared by sync + async).
Methods stay thin:
```python
def new_method(self, param: str) -> ResponseModel:
    """Method description."""
    path, params = build.new_endpoint(param)
    return parse_model(ResponseModel, self._get(path, params))
```

### Testing Patterns
```python
import pytest
from unittest.mock import Mock
import httpx

def test_method_success(mock_client):
    """Test successful API call."""
    # Arrange
    mock_response = Mock()
    mock_response.json.return_value = {"data": "test"}
    
    # Act
    result = mock_client.new_method("test")
    
    # Assert
    assert result.data == "test"

@pytest.mark.asyncio
async def test_async_method():
    """Test async method."""
    # Async test implementation
```

## File Organization

### Core Structure
```
elfa/
├── __init__.py          # Main package exports
├── client/              # Client implementations
│   ├── elfa_client.py   # Sync data + chat client (.auto)
│   ├── async_client.py  # Async mirror
│   ├── auto_client.py   # AutoClient / AsyncAutoClient
│   ├── base.py          # SignedClient + parse helpers
│   └── _params.py       # shared data param builders
├── models/              # Pydantic data models
├── exceptions/          # Custom exceptions
└── utils/               # Utility functions

tests/                   # Test suite
examples/                # Usage examples
```

### Adding New Features
1. **Models first** - Define Pydantic models in `elfa/models/`
2. **Client methods** - Add to appropriate client class
3. **Tests** - Create comprehensive test coverage
4. **Examples** - Add usage examples if public API
5. **Documentation** - Update docstrings and README if needed

### Before Merging a PR

**A green check does not mean a clean review.** Sourcery posts findings as a
`COMMENTED` review: it does not block, and its check run reports `pass` whatever
it found. All-green `gh pr checks` proves the reviewer ran, nothing more.

```bash
gh api repos/elfa-ai/elfa-sdk-python/pulls/<n>/reviews  --jq '.[]|"[\(.user.login)] \(.body)"'
gh api repos/elfa-ai/elfa-sdk-python/pulls/<n>/comments --jq '.[]|"\(.path):\(.line) \(.body)"'
```

Fix each finding or reply saying why not. Three `elfa-sdk-js` PRs were merged off
a green check with unread findings; all three were valid and needed a follow-up.

**Squash merges discard commit authorship** — the squashed commit is attributed
to whoever opened the PR. If a PR carries someone else's commits, add a
`Co-authored-by:` trailer to your own commit before merging; afterwards it
cannot be fixed without rewriting `main`.

### Release Process

Releases run through `.github/workflows/release.yml`, which publishes to PyPI and
creates the GitHub release. Do not publish by hand.

1. Land the version bump in `pyproject.toml` (and `elfa/version.py`) plus the
   matching `## <version>` entry in `CHANGELOG.md` — the release body is
   extracted from that section
2. Either push a `v*.*.*` tag or dispatch **Actions → Release → Run workflow**
   from `main`
3. The workflow runs lint, type-check and the test suite, then builds, publishes
   and creates the release

`validate` compares `pyproject.toml` against the version the release asks for —
the dispatch input, or the tag name minus its `v` — and fails on a mismatch. So
if you release by tag, tag the commit whose `pyproject.toml` already carries that
version. The `release` environment has no branch policy, which is why a tag push
reaches it (the JS SDK needed an explicit `tag v*` rule added for this).

Without a `CHANGELOG.md` entry for the version, the release falls back to the
commit log since the previous tag — a release still gets notes, just thin ones.

**Publishing uses OIDC trusted publishing — there is no PyPI token.** The trust
relationship is configured on pypi.org against values that must keep matching the
workflow:

| PyPI setting      | Value              |
| ----------------- | ------------------ |
| Repository        | `elfa-sdk-python`  |
| Workflow filename | `release.yml`      |
| Environment name  | `release`          |

Renaming the workflow file or the `release` environment breaks publishing until
the PyPI-side config is updated to match. Note the repo has both a `production`
and a `release` environment; PyPI is wired to `release`.

PyPI's JSON API is CDN-cached, so `pypi.org/pypi/elfa-sdk/json` can report the
previous version for a while after a successful publish. Confirm against
`https://pypi.org/pypi/elfa-sdk/<version>/json` or the simple index instead of
concluding the publish failed.

## CI Gates

`.github/workflows/ci.yml` runs the test matrix, an integration smoke test, the
security audit and a publish-readiness check; `codeql.yml` runs static analysis.

**The security job is allowed to fail, and that is deliberate.** It previously
ended both steps in `|| true`, so it reported green whatever it found — and
`safety check` had been deprecated in safety 3, which needs an account for the
full advisory database, so it was likely finding nothing anyway. A check that
cannot fail is worse than no check: the green tick implies coverage that is not
there. If you touch this job, do not reintroduce a swallow.

- `pip-audit --progress-spinner off .` — the trailing `.` matters. It audits the
  project's declared dependency tree in an isolated build env. Auditing the
  ambient environment instead flags the runner's own `setuptools`/`pip`, build
  tooling this package never ships, and fails the job over something no release
  of ours can fix. Same scope as `npm audit --omit=dev` on the JS SDK.
- `bandit -r elfa/ -ll` — medium severity and above.
- Both tools are pinned with `~=`. They decide whether CI passes, so an
  unannounced major would move the gate without anyone choosing it. Pinning does
  not stale the findings: both fetch advisory data at run time.

## Dependencies

### Core Dependencies
- `httpx>=0.24.0` - HTTP client with sync/async support
- `pydantic>=2.0.0` - Data validation and serialization
- `typing-extensions>=4.0.0` - Extended typing support

### Development Dependencies
- `pytest` + `pytest-asyncio` + `respx` - Testing framework
- `black` + `isort` - Code formatting
- `mypy` - Type checking
- `flake8` - Linting
- `coverage` - Test coverage

## Security Guidelines

- **API Keys**: Store in environment variables, never in code
- **Rate Limiting**: Respect API rate limits and implement backoff
- **Input Validation**: Validate all user inputs with Pydantic
- **Error Messages**: Don't expose internal details in error messages
- **Dependencies**: Keep dependencies updated for security patches

## Performance Considerations

- **Async Operations**: Use async client for concurrent requests
- **Batching**: Implement batching for bulk operations
- **Caching**: Cache responses when appropriate
- **Connection Pooling**: Leverage httpx connection pooling
- **Timeout Handling**: Set appropriate timeouts for all requests

## Common Patterns to Follow

1. **Consistent naming**: Use snake_case for Python, follow existing patterns
2. **Type safety**: Always use type hints, run mypy
3. **Error propagation**: Use custom exceptions, don't suppress errors
4. **Documentation**: Write clear docstrings with examples
5. **Backwards compatibility**: Consider API compatibility when making changes
6. **Resource cleanup**: Use context managers for resource management