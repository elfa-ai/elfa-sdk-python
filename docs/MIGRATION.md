# Migration Guide

This guide helps you migrate from direct Elfa API calls to using the official Elfa AI Python SDK.

## Overview

The Elfa AI Python SDK provides a modern, type-safe way to interact with the Elfa API v2, with optional Twitter API enhancement for raw tweet content. This guide covers migration from manual HTTP requests to the SDK.

**Key improvements the SDK provides:**
- **Type Safety**: Full Pydantic model support with IDE IntelliSense and runtime validation
- **Authentication**: Automatic API key management and header injection
- **Error Handling**: Specific exception classes instead of generic HTTP errors
- **Rate Limiting**: Built-in respect for API rate limits and retry logic with exponential backoff
- **Enhancement**: Optional Twitter API integration for raw tweet content
- **Consistency**: Unified response format and parameter naming across all endpoints
- **Future-Proof**: Automatic compatibility with new API versions and features
- **Async Support**: Both synchronous and asynchronous client implementations

## Installation

```bash
pip install elfa-ai
```

## Migration Steps

### Step 1: Replace Direct API Calls

**Before (Direct HTTP Requests):**
```python
import requests

api_key = 'your-elfa-api-key'
base_url = 'https://api.elfa.ai'

# Manual trending tokens request
trending_response = requests.get(
    f'{base_url}/v2/trending-tokens',
    headers={
        'x-elfa-api-key': api_key,
        'Content-Type': 'application/json'
    },
    params={
        'timeWindow': '24h',
        'pageSize': 50
    }
)
trending = trending_response.json()

# Manual keyword mentions request
mentions_response = requests.get(
    f'{base_url}/v2/data/keyword-mentions',
    headers={
        'x-elfa-api-key': api_key,
        'Content-Type': 'application/json'
    },
    params={
        'keywords': 'bitcoin',
        'period': '1h',
        'limit': 20
    }
)
mentions = mentions_response.json()
```

**After (Using SDK):**
```python
from elfa import ElfaClient

# Context manager automatically handles resource cleanup
with ElfaClient(
    api_key='your-elfa-api-key',
    twitter_bearer_token='your-twitter-bearer-token'  # Optional for enhanced features
) as elfa:
    
    # Clean method calls with Pydantic model validation
    trending = elfa.get_trending_tokens(
        time_window='24h',
        page_size=50
    )
    
    mentions = elfa.get_keyword_mentions(
        keywords='bitcoin',
        period='1h',
        limit=20,
        fetch_raw_tweets=True  # Optional: get raw tweet content
    )
```

**Async Version:**
```python
from elfa import AsyncElfaClient

async with AsyncElfaClient(api_key='your-elfa-api-key') as elfa:
    # All methods are awaitable
    trending = await elfa.get_trending_tokens(time_window='24h')
    mentions = await elfa.get_keyword_mentions(keywords='bitcoin')
```

### Step 2: Error Handling Improvements

**Before (Manual Error Handling):**
```python
import requests

try:
    response = requests.get(f'{base_url}/v2/trending-tokens', headers=headers)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    if response.status_code == 401:
        print('Authentication failed')
    elif response.status_code == 429:
        print('Rate limited')
    else:
        print(f'API error: {e}')
except requests.exceptions.RequestException as e:
    print(f'Request error: {e}')
```

**After (Built-in Exception Types):**
```python
from elfa import ElfaClient
from elfa.exceptions import (
    ElfaAuthenticationError,
    ElfaRateLimitError,
    ElfaAPIError,
    ElfaNetworkError
)

with ElfaClient(api_key='your-api-key') as elfa:
    try:
        trending = elfa.get_trending_tokens(time_window='24h')
    except ElfaAuthenticationError:
        print('Invalid API key')
    except ElfaRateLimitError as e:
        print(f'Rate limited, retry after: {e.retry_after} seconds')
    except ElfaAPIError as e:
        print(f'API error: {e.message} (Status: {e.status_code})')
    except ElfaNetworkError:
        print('Network connection error')
```

### Step 3: Enhanced Features

The SDK provides features not easily available with direct API calls:

#### Twitter API Enhancement
```python
from elfa import ElfaClient

with ElfaClient(
    api_key='your-elfa-api-key',
    twitter_bearer_token='your-twitter-bearer-token',
    fetch_raw_tweets=True  # Global setting
) as elfa:
    
    # Get keyword mentions with raw tweet content
    enhanced_mentions = elfa.get_keyword_mentions(
        keywords='bitcoin',
        period='1h',
        fetch_raw_tweets=True  # Override global setting
    )
    
    for mention in enhanced_mentions.data:
        print(f'Processed data: {mention.processed_content}')
        if hasattr(mention, 'content'):  # Enhanced with Twitter API
            print(f'Raw tweet: {mention.content}')
        print(f'Data source: {mention.data_source}')  # 'elfa+twitter'
```

#### Built-in Retry and Rate Limiting
```python
from elfa import ElfaClient

client = ElfaClient(
    api_key='your-api-key',
    max_retries=5,           # Automatic retries with exponential backoff
    retry_delay=1.0,         # Base delay between retries
    timeout=30.0,            # Request timeout
    enhancement_timeout=45.0  # Twitter API timeout
)

# The SDK automatically handles retries and rate limiting
with client:
    # This will automatically retry on transient failures
    trending = client.get_trending_tokens(time_window='24h')
```

#### Response Validation with Pydantic
```python
from elfa import ElfaClient
from elfa.models import TrendingTokensResponse, KeywordMentionsV2Response

with ElfaClient(api_key='your-api-key') as elfa:
    # Responses are automatically validated and typed
    trending: TrendingTokensResponse = elfa.get_trending_tokens()
    
    # Full IDE support and type checking
    print(f"Found {len(trending.data)} trending tokens")
    for token in trending.data:
        print(f"{token.name}: {token.mentions_count} mentions")
```

## Method Mapping

This section maps raw API endpoints to SDK methods for easy migration.

### V2 API Endpoints

#### Ping & Status
```python
# Direct API
# GET /v2/ping

# SDK
await elfa.ping()

# Direct API  
# GET /v2/key-status

# SDK
await elfa.get_api_key_status()
```

#### Trending Tokens
```python
# Direct API
# GET /v2/trending-tokens?timeWindow=24h&pageSize=50

# SDK
await elfa.get_trending_tokens(time_window='24h', page_size=50)
```

#### Keyword Mentions
```python
# Direct API
# GET /v2/data/keyword-mentions?keywords=bitcoin&period=1h&limit=20

# SDK
await elfa.get_keyword_mentions(
    keywords='bitcoin',
    period='1h',
    limit=20
)
```

#### Token News
```python
# Direct API
# GET /v2/data/token-news?coinIds=bitcoin,ethereum&pageSize=20

# SDK
await elfa.get_token_news(
    coin_ids='bitcoin,ethereum',
    page_size=20
)
```

#### Trending Contract Addresses
```python
# Direct API
# GET /v2/data/trending-cas?timeWindow=24h&minMentions=10

# SDK  
await elfa.get_trending_contract_addresses_twitter(
    time_window='24h',
    min_mentions=10
)

# Direct API
# GET /v2/data/trending-cas-telegram?timeWindow=24h&minMentions=10

# SDK
await elfa.get_trending_contract_addresses_telegram(
    time_window='24h',
    min_mentions=10
)
```

#### Account Stats
```python
# Direct API
# GET /v2/account/smart-stats?username=elonmusk

# SDK
await elfa.get_account_smart_stats(username='elonmusk')
```

#### Top Mentions
```python
# Direct API
# GET /v2/top-mentions?ticker=bitcoin&timeWindow=24h&pageSize=50

# SDK
await elfa.get_top_mentions(
    ticker='bitcoin',
    time_window='24h',
    page_size=50
)
```

### V1 Legacy Endpoints (for backward compatibility)

#### V1 Mentions by Keywords
```python
# Direct V1 API
# GET /v1/mentions/search?keywords=bitcoin&from=1640995200&to=1641081600&limit=10

# SDK (V2 method - recommended)
await elfa.get_keyword_mentions(
    keywords='bitcoin',
    period='custom',
    start_time=1640995200,
    end_time=1641081600,
    limit=10
)

# SDK (V1 compatibility method)
await elfa.get_mentions_by_keywords_v1(
    keywords='bitcoin',
    from_timestamp=1640995200,
    to_timestamp=1641081600,
    limit=10
)
```

#### V1 Mentions with Smart Engagement
```python
# Direct V1 API
# GET /v1/mentions?limit=50&offset=0

# SDK (V1 compatibility method)
await elfa.get_mentions_with_smart_engagement(
    limit=50,
    offset=0
)
```

## V1 Compatibility Layer

For users who had custom V1-style implementations, the SDK provides backward compatibility:

```python
from elfa import ElfaClient

# The main client includes V1 compatibility methods
with ElfaClient(
    api_key='your-elfa-api-key',
    twitter_bearer_token='your-twitter-bearer-token'
) as client:
    
    # V1-style method signatures with deprecation warnings
    mentions = client.get_mentions_by_keywords_v1(
        keywords='ethereum',
        from_timestamp=1640995200,
        to_timestamp=1641081600
    )
    
    smart_mentions = client.get_mentions_with_smart_engagement(
        limit=50,
        offset=0
    )
```

## Configuration Options

The SDK provides extensive configuration options:

```python
from elfa import ElfaClient, AsyncElfaClient

# Synchronous client
client = ElfaClient(
    # Required
    api_key='your-elfa-api-key',
    
    # Optional enhancements
    twitter_bearer_token='your-twitter-bearer-token',
    fetch_raw_tweets=False,  # Global setting
    
    # API configuration
    base_url='https://api.elfa.ai',  # Custom base URL
    timeout=30.0,                    # Request timeout
    enhancement_timeout=45.0,        # Twitter API timeout
    max_batch_size=50,              # Max tweets per batch
    
    # Retry behavior
    max_retries=3,                  # Retry attempts
    retry_delay=1.0,                # Base retry delay
    
    # Enhancement behavior
    strict_mode=False,              # Fail if Twitter unavailable
    cache_enhancements=True,        # Cache Twitter responses
    
    # Other options
    user_agent='MyApp/1.0',         # Custom user agent
)

# Asynchronous client with same options
async_client = AsyncElfaClient(
    api_key='your-elfa-api-key',
    # ... same configuration options
)
```

## Benefits of Migration

1. **Type Safety**: Full Pydantic model definitions with IDE autocomplete and runtime validation
2. **Error Handling**: Specific exception classes for different failure modes
3. **Rate Limiting**: Built-in retry logic with exponential backoff
4. **Enhancement**: Optional Twitter API integration for raw content
5. **Consistency**: Unified response format across all endpoints
6. **Maintenance**: Regular updates and bug fixes
7. **Documentation**: Comprehensive docstrings and type hints
8. **Async Support**: Native async/await support for high-performance applications
9. **Context Management**: Automatic resource cleanup with context managers

## Examples

The SDK includes comprehensive examples:

```python
# Basic synchronous usage
from elfa import ElfaClient

def basic_example():
    with ElfaClient(api_key='your-api-key') as client:
        # Health check
        ping_result = client.ping()
        print(f"API Status: {ping_result.status}")
        
        # Get trending tokens
        trending = client.get_trending_tokens(time_window='24h')
        print(f"Found {len(trending.data)} trending tokens")
        
        # Search mentions
        mentions = client.get_keyword_mentions(
            keywords='bitcoin',
            period='1h',
            limit=10
        )
        for mention in mentions.data:
            print(f"Mention: {mention.processed_content}")

# Enhanced usage with Twitter API
def enhanced_example():
    with ElfaClient(
        api_key='your-elfa-api-key',
        twitter_bearer_token='your-twitter-token',
        fetch_raw_tweets=True
    ) as client:
        
        mentions = client.get_keyword_mentions(
            keywords='ethereum',
            period='1h',
            fetch_raw_tweets=True
        )
        
        for mention in mentions.data:
            print(f"Processed: {mention.processed_content}")
            if hasattr(mention, 'content'):
                print(f"Raw tweet: {mention.content}")

# Asynchronous usage
import asyncio

async def async_example():
    async with AsyncElfaClient(api_key='your-api-key') as client:
        # Concurrent requests
        trending_task = client.get_trending_tokens(time_window='24h')
        mentions_task = client.get_keyword_mentions(keywords='bitcoin')
        
        trending, mentions = await asyncio.gather(trending_task, mentions_task)
        
        print(f"Trending tokens: {len(trending.data)}")
        print(f"Bitcoin mentions: {len(mentions.data)}")

# Run examples
if __name__ == '__main__':
    basic_example()
    enhanced_example()
    asyncio.run(async_example())
```

## Need Help?

- 📖 [Full Documentation](https://docs.elfa.ai)
- 🔍 [View Examples](./examples/)
- 🐛 [Report Issues](https://github.com/elfa-ai/elfa-sdk-python/issues)
- 📧 [Email Support](mailto:support@elfa.ai)