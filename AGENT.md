# AGENT.md

This file provides base instructions for all AI coding assistants (Claude Code, Cursor, GitHub Copilot, etc.) working with this repository.

## Project Overview

**Elfa Python SDK** - Official Python SDK for the Elfa API: social intelligence, AI chat, and the Auto/Trade engines for crypto. V2-only (no V1 surface).

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
- **Sync Client**: `ElfaClient` - data + AI chat, with `.auto` and `.trade`
- **Async Client**: `AsyncElfaClient` - async mirror of `ElfaClient`
- **Auto engine**: `AutoClient` / `AsyncAutoClient` (`/v2/auto/*`) - EQL queries, drafts, sessions, executions, exchanges, SSE streams
- **Trade**: `TradeClient` / `AsyncTradeClient` (`/v2/trade/*`) - orders and positions
- **Transport**: `SyncTransport` / `AsyncTransport` (retries, error mapping, SSE)
- **Signing**: Auto/Trade mutations are HMAC-signed when `hmac_secret` is set. Sign `timestamp+METHOD+mounted_path+body`; the body must be the exact compact-JSON bytes sent (httpx `content=`, never `json=`).

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
│   ├── elfa_client.py   # Sync data + chat client (.auto/.trade)
│   ├── async_client.py  # Async mirror
│   ├── auto_client.py   # AutoClient / AsyncAutoClient
│   ├── trade_client.py  # TradeClient / AsyncTradeClient
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