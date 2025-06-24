# Elfa AI Python SDK

[![PyPI version](https://badge.fury.io/py/elfa-sdk.svg)](https://badge.fury.io/py/elfa-sdk)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for the Elfa API - Social media analytics and insights for cryptocurrency and blockchain projects.

## Features

- 🚀 **Easy to use** - Simple, intuitive API
- ⚡ **Async support** - Both synchronous and asynchronous clients
- 🔒 **Type safe** - Full type hints with Pydantic models
- 🛡️ **Error handling** - Comprehensive error handling with custom exceptions
- 🔄 **Auto-retry** - Automatic retry logic with exponential backoff
- 📊 **Complete coverage** - All Elfa API v2 endpoints supported

## Installation

```bash
pip install elfa-sdk
```

Or with async support:

```bash
pip install elfa-sdk[dev]
```

## Quick Start

### Synchronous Client

```python
from elfa import ElfaClient

# Initialize the client
client = ElfaClient(api_key="your-api-key-here")

# Get trending tokens
trending = client.get_trending_tokens(time_window="24h")
print(f"Found {len(trending.data.data)} trending tokens")

for token in trending.data.data:
    print(f"{token.token}: {token.current_count} mentions ({token.change_percent:+.1f}%)")

# Search for keyword mentions
mentions = client.get_keyword_mentions(keywords="bitcoin,ethereum", limit=10)
print(f"Found {len(mentions.data)} mentions")

for mention in mentions.data:
    print(f"@{mention.account.username}: {mention.like_count} likes")
```

### Asynchronous Client

```python
import asyncio
from elfa import AsyncElfaClient

async def main():
    async with AsyncElfaClient(api_key="your-api-key-here") as client:
        # Get trending tokens
        trending = await client.get_trending_tokens(time_window="24h")
        
        # Get account stats
        stats = await client.get_account_smart_stats(username="elonmusk")
        
        print(f"Smart following count: {stats.data.smart_following_count}")

asyncio.run(main())
```

## API Reference

### Authentication

All API calls require an API key. Get yours at [elfa.ai](https://elfa.ai).

```python
from elfa import ElfaClient

client = ElfaClient(
    api_key="your-api-key",
    base_url="https://api.elfa.ai",  # Optional, defaults to production
    timeout=30.0,                    # Optional, request timeout in seconds
    max_retries=3,                   # Optional, max retries for failed requests
)
```

### Endpoints

#### Health Check

```python
# Ping the API
response = client.ping()
print(response.data.message)  # "pong"
```

#### API Key Status

```python
# Check your API key status and usage
status = client.get_api_key_status()
print(f"Daily usage: {status.data.usage.today}")
print(f"Monthly limit: {status.data.monthly_limit}")
```

#### Trending Tokens

```python
# Get trending cryptocurrency tokens
trending = client.get_trending_tokens(
    time_window="24h",    # "1h", "24h", "7d"
    page=1,               # Page number
    page_size=50,         # Results per page (max 100)
    min_mentions=5        # Minimum mentions required
)

for token in trending.data.data:
    print(f"{token.token}: {token.current_count} mentions")
```

#### Keyword Mentions

```python
# Search mentions by keywords
mentions = client.get_keyword_mentions(
    keywords="bitcoin,ethereum",     # Up to 5 keywords, comma-separated
    period="24h",                    # Time period
    limit=20,                        # Max results (max 30)
    search_type="or"                 # "and" or "or"
)

# Search by account name
mentions = client.get_keyword_mentions(
    account_name="elonmusk",
    period="7d"
)
```

#### Account Smart Stats

```python
# Get smart statistics for a Twitter account
stats = client.get_account_smart_stats(username="elonmusk")
print(f"Engagement ratio: {stats.data.follower_engagement_ratio}")
print(f"Smart following: {stats.data.smart_following_count}")
```

#### Token News

```python
# Get token-related news mentions
news = client.get_token_news(
    coin_ids="bitcoin,ethereum",     # CoinGecko coin IDs
    page=1,
    page_size=20
)
```

#### Trending Contract Addresses

```python
# Get trending contract addresses on Twitter
twitter_cas = client.get_trending_contract_addresses_twitter(
    time_window="24h",
    min_mentions=5
)

# Get trending contract addresses on Telegram  
telegram_cas = client.get_trending_contract_addresses_telegram(
    time_window="24h",
    min_mentions=5
)
```

## Error Handling

The SDK provides specific exception types for different error scenarios:

```python
from elfa import ElfaClient
from elfa.exceptions import (
    ElfaAPIError,
    ElfaAuthenticationError,
    ElfaRateLimitError,
    ElfaValidationError,
    ElfaNetworkError
)

client = ElfaClient(api_key="your-api-key")

try:
    trending = client.get_trending_tokens()
except ElfaAuthenticationError:
    print("Invalid API key")
except ElfaRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except ElfaValidationError as e:
    print(f"Invalid parameters: {e.validation_errors}")
except ElfaNetworkError:
    print("Network connection error")
except ElfaAPIError as e:
    print(f"API error: {e}")
```

## Configuration

### Environment Variables

You can set your API key using an environment variable:

```bash
export ELFA_API_KEY="your-api-key-here"
```

```python
import os
from elfa import ElfaClient

client = ElfaClient(api_key=os.getenv("ELFA_API_KEY"))
```

### Timeouts and Retries

```python
client = ElfaClient(
    api_key="your-api-key",
    timeout=60.0,        # 60 second timeout
    max_retries=5,       # Retry up to 5 times
    retry_delay=2.0      # Wait 2 seconds between retries
)
```

## Rate Limiting

The SDK automatically handles rate limiting and will retry requests when rate limits are hit. You can check your current usage:

```python
status = client.get_api_key_status()
print(f"Requests remaining today: {status.data.usage.remaining_daily}")
print(f"Requests remaining this month: {status.data.usage.remaining_monthly}")
```

## Development

### Installation for Development

```bash
git clone https://github.com/elfa-ai/elfa-sdk-python.git
cd elfa-sdk-python

# Install with development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=elfa --cov-report=html

# Run specific test file
pytest tests/test_sync_client.py
```

### Code Formatting

```bash
# Format code
black .
isort .

# Type checking
mypy elfa/

# Linting
flake8 elfa/
```

## Support

- 📚 [Documentation](https://docs.elfa.ai)
- 🐛 [Bug Reports](https://github.com/elfa-ai/elfa-sdk-python/issues)
- 💬 [Discord Community](https://discord.gg/elfa)
- 📧 [Email Support](mailto:support@elfa.ai)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### 2.0.0 (2024-06-20)

- Initial release of Python SDK for Elfa API v2
- Support for all v2 endpoints
- Both sync and async clients
- Comprehensive error handling
- Full type safety with Pydantic models
- Automatic retry logic
- Rate limiting support