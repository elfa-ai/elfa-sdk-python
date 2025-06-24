"""
Enhanced Elfa API Usage Examples

Demonstrates the new features added to match the JavaScript SDK:
- V1 endpoint compatibility
- Twitter API integration
- Enhanced response types
- V1 compatibility layer
"""

import asyncio
import time

from elfa import AsyncElfaClient, ElfaClient
from elfa.client import (
    AsyncV1CompatibilityLayer,
    EnhancementConfig,
    ResponseEnhancer,
    TwitterClient,
    TwitterConfig,
    V1CompatibilityLayer,
)


def v1_endpoints_example():
    """Example using the new V1 endpoints for additional functionality"""

    client = ElfaClient(api_key="your-api-key")

    # Calculate time range (last 24 hours)
    end_time = int(time.time())
    start_time = end_time - (24 * 60 * 60)

    # Get mentions with smart engagement (V1 endpoint)
    print("Getting mentions with smart engagement...")
    smart_mentions = client.get_mentions_with_smart_engagement(
        from_timestamp=start_time,
        to_timestamp=end_time,
        limit=20,
        mentioned_by_type="smart",
        sentiment="bullish",
        include_account_info=True,
        include_coins=True,
    )

    print(f"Found {len(smart_mentions.data)} smart mentions")
    for mention in smart_mentions.data[:3]:
        print(f"- {mention.content[:100]}...")
        if mention.account:
            print(f"  By: {mention.account.username}")

    # Search mentions by keywords (V1 endpoint)
    print("\nSearching mentions by keywords (V1)...")
    keyword_mentions = client.get_mentions_by_keywords_v1(
        keywords="bitcoin,ethereum,crypto",
        from_timestamp=start_time,
        to_timestamp=end_time,
        limit=30,
        search_type="or",
    )

    print(f"Found {len(keyword_mentions.data)} keyword mentions")
    for mention in keyword_mentions.data[:3]:
        print(f"- {mention.content[:100]}...")


async def twitter_integration_example():
    """Example showing Twitter API integration for enhanced responses"""

    # Setup Twitter API client
    twitter_config = TwitterConfig(
        bearer_token="your-twitter-bearer-token"  # Get from Twitter Developer Portal
    )
    twitter_client = TwitterClient(twitter_config)

    # Setup response enhancer
    enhancement_config = EnhancementConfig(
        fetch_raw_tweets=True,
        enhancement_timeout=60.0,
        max_batch_size=50,
        strict_mode=False,
        cache_enhancements=True,
        include_user_data=True,
    )
    enhancer = ResponseEnhancer(twitter_client, enhancement_config)

    # Create Elfa client
    async_client = AsyncElfaClient(api_key="your-api-key")

    try:
        # Get Elfa API response
        print("Getting keyword mentions from Elfa API...")
        elfa_response = await async_client.get_keyword_mentions(
            keywords="bitcoin,ethereum", period="24h", limit=10
        )

        print(f"Elfa API returned {len(elfa_response.data)} mentions")

        # Enhance with Twitter data
        print("Enhancing with Twitter API data...")
        enhanced_response = await enhancer.enhance_mentions_response(elfa_response)

        print("Enhanced response:")
        for mention in enhanced_response.data:
            print(f"\nTweet ID: {mention.tweet_id}")
            print(f"Elfa data: {mention.link}")

            # Check if we have enhanced Twitter data
            if mention.data_source.twitter_api and mention.raw_tweet_text:
                print(f"Full tweet text: {mention.raw_tweet_text}")

                if mention.twitter_user:
                    print(
                        f"Twitter user: @{mention.twitter_user.username} ({mention.twitter_user.name})"
                    )
                    if mention.twitter_user.verified:
                        print("✓ Verified account")

                if mention.twitter_metrics:
                    print(f"Twitter metrics: {mention.twitter_metrics}")

                if mention.context_annotations:
                    print(f"Context: {len(mention.context_annotations)} annotations")
            else:
                print("No Twitter enhancement available for this tweet")

    finally:
        await async_client.close()
        await enhancer.close()


def enhanced_configuration_example():
    """Example showing enhanced configuration options"""

    # Create client with enhanced configuration
    client = ElfaClient(
        api_key="your-api-key",
        # Basic HTTP settings
        timeout=60.0,
        max_retries=5,
        retry_delay=2.0,
        # Enhanced settings (similar to JS SDK)
        fetch_raw_tweets=True,
        enhancement_timeout=45.0,
        max_batch_size=100,
        strict_mode=False,
        cache_enhancements=True,
    )

    print("Client configured with enhanced options:")
    print(f"- fetch_raw_tweets: {client.fetch_raw_tweets}")
    print(f"- enhancement_timeout: {client.enhancement_timeout}")
    print(f"- max_batch_size: {client.max_batch_size}")
    print(f"- strict_mode: {client.strict_mode}")
    print(f"- cache_enhancements: {client.cache_enhancements}")

    # Use the client normally - enhancement settings will be applied
    # when Twitter integration is used
    trending = client.get_trending_tokens(time_window="24h", page_size=20)
    print(f"\nGot {len(trending.data.data)} trending tokens")


def v1_compatibility_example():
    """Example showing V1 compatibility layer for migration"""

    # Create V2 client
    client = ElfaClient(api_key="your-api-key")

    # Wrap with V1 compatibility layer
    v1_compat = V1CompatibilityLayer(client, show_deprecation_warnings=True)

    # Use V1-style method signatures (with deprecation warnings)
    print("Using V1-compatible methods...")

    # V1-style trending tokens (camelCase parameters)
    trending = v1_compat.get_trending_tokens(
        timeWindow="24h",  # V1 style: camelCase
        pageSize=20,  # V1 style: camelCase
        minMentions=5,  # V1 style: camelCase
    )
    print(f"Trending tokens: {len(trending.data.data)} results")

    # V1-style keyword search (with timestamps)
    end_time = int(time.time())
    start_time = end_time - (24 * 60 * 60)

    mentions = v1_compat.get_mentions_by_keywords(
        keywords="bitcoin,ethereum",
        from_timestamp=start_time,  # V1 style: required timestamps
        to_timestamp=end_time,  # V1 style: required timestamps
        searchType="or",  # V1 style: camelCase
    )
    print(f"Keyword mentions: {len(mentions.data)} results")

    # Get migration guide
    print("\nMigration guide:")
    migration_guide = v1_compat.get_migration_guide()
    for old_method, new_method in migration_guide.items():
        print(f"- {old_method}")
        print(f"  → {new_method}")

    # List deprecated methods
    print(f"\nDeprecated methods: {v1_compat.list_deprecated_methods()}")


async def async_v1_compatibility_example():
    """Example showing async V1 compatibility layer"""

    # Create async V2 client
    async_client = AsyncElfaClient(api_key="your-api-key")

    # Wrap with async V1 compatibility layer
    async_v1_compat = AsyncV1CompatibilityLayer(async_client)

    try:
        # Use V1-style async methods
        print("Using async V1-compatible methods...")

        # V1-style trending tokens
        trending = await async_v1_compat.get_trending_tokens(
            timeWindow="24h", pageSize=10
        )
        print(f"Async trending tokens: {len(trending.data.data)} results")

        # V1-style smart engagement
        end_time = int(time.time())
        start_time = end_time - (12 * 60 * 60)  # Last 12 hours

        smart_mentions = await async_v1_compat.get_mentions_with_smart_engagement(
            from_timestamp=start_time,
            to_timestamp=end_time,
            mentionedByType="smart",  # V1 style: camelCase
            includeAccountInfo=True,  # V1 style: camelCase
        )
        print(f"Smart mentions: {len(smart_mentions.data)} results")

    finally:
        await async_client.close()


def main():
    """Run all examples"""

    print("=== V1 Endpoints Example ===")
    try:
        v1_endpoints_example()
    except Exception as e:
        print(f"V1 endpoints example failed: {e}")

    print("\n=== Enhanced Configuration Example ===")
    try:
        enhanced_configuration_example()
    except Exception as e:
        print(f"Enhanced configuration example failed: {e}")

    print("\n=== V1 Compatibility Example ===")
    try:
        v1_compatibility_example()
    except Exception as e:
        print(f"V1 compatibility example failed: {e}")

    print("\n=== Async Examples ===")
    try:
        # Run async examples
        asyncio.run(twitter_integration_example())
        asyncio.run(async_v1_compatibility_example())
    except Exception as e:
        print(f"Async examples failed: {e}")


if __name__ == "__main__":
    main()
