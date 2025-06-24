"""
Async usage examples for the Elfa Python SDK

This example demonstrates how to use the async client for better performance
when making multiple API calls or integrating with async applications.

Requirements:
- Set ELFA_API_KEY environment variable with your API key
- Install the SDK: pip install elfa-ai
"""

import asyncio
import os
from typing import Any, Dict, List

from elfa import AsyncElfaClient
from elfa.exceptions import ElfaAPIError


async def get_trending_analysis(client: AsyncElfaClient) -> Dict[str, Any]:
    """Get trending tokens and analyze them"""
    print("🔍 Analyzing trending tokens...")

    # Get trending tokens for different time windows concurrently
    tasks = [
        client.get_trending_tokens(time_window="1h", page_size=10),
        client.get_trending_tokens(time_window="24h", page_size=10),
        client.get_trending_tokens(time_window="7d", page_size=10),
    ]

    try:
        hourly, daily, weekly = await asyncio.gather(*tasks)

        # Extract token names
        hourly_tokens = {t.token for t in hourly.data.data}
        daily_tokens = {t.token for t in daily.data.data}
        weekly_tokens = {t.token for t in weekly.data.data}

        # Find tokens that are trending across all timeframes
        consistent_trending = hourly_tokens & daily_tokens & weekly_tokens

        return {
            "hourly_count": len(hourly_tokens),
            "daily_count": len(daily_tokens),
            "weekly_count": len(weekly_tokens),
            "consistent_trending": list(consistent_trending),
            "top_daily": daily.data.data[:5],
        }
    except ElfaAPIError as e:
        print(f"❌ Error getting trending analysis: {e}")
        return {}


async def search_multiple_keywords(
    client: AsyncElfaClient, keywords: List[str]
) -> Dict[str, int]:
    """Search for multiple keywords concurrently"""
    print(f"🔍 Searching for keywords: {', '.join(keywords)}")

    # Create search tasks for each keyword
    tasks = []
    for keyword in keywords:
        task = client.get_keyword_mentions(keywords=keyword, period="24h", limit=10)
        tasks.append(task)

    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)

        mention_counts = {}
        for keyword, result in zip(keywords, results):
            if isinstance(result, Exception):
                print(f"❌ Error searching for '{keyword}': {result}")
                mention_counts[keyword] = 0
            else:
                mention_counts[keyword] = len(result.data)

        return mention_counts
    except Exception as e:
        print(f"💥 Unexpected error in keyword search: {e}")
        return {}


async def analyze_top_accounts(
    client: AsyncElfaClient, usernames: List[str]
) -> List[Dict[str, Any]]:
    """Analyze smart stats for multiple accounts concurrently"""
    print(f"👥 Analyzing accounts: {', '.join(usernames)}")

    # Create tasks for each account
    tasks = []
    for username in usernames:
        task = client.get_account_smart_stats(username=username)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    account_stats = []
    for username, result in zip(usernames, results):
        if isinstance(result, Exception):
            print(f"❌ Error getting stats for @{username}: {result}")
            account_stats.append(
                {
                    "username": username,
                    "error": str(result),
                    "smart_following": 0,
                    "engagement_ratio": 0,
                }
            )
        else:
            account_stats.append(
                {
                    "username": username,
                    "smart_following": result.data.smart_following_count,
                    "engagement_ratio": result.data.follower_engagement_ratio,
                    "avg_engagement": result.data.average_engagement,
                }
            )

    return account_stats


async def get_market_overview(client: AsyncElfaClient) -> Dict[str, Any]:
    """Get a comprehensive market overview"""
    print("📊 Getting market overview...")

    # Get multiple data points concurrently
    tasks = [
        client.get_trending_tokens(time_window="24h", page_size=20),
        client.get_trending_contract_addresses_twitter(time_window="24h", page_size=10),
        client.get_trending_contract_addresses_telegram(
            time_window="24h", page_size=10
        ),
        client.get_token_news(page_size=10),
    ]

    try:
        trending_tokens, twitter_cas, telegram_cas, news = await asyncio.gather(*tasks)

        return {
            "trending_tokens_count": len(trending_tokens.data.data),
            "top_tokens": [t.token for t in trending_tokens.data.data[:5]],
            "twitter_contracts": len(twitter_cas.data.data),
            "telegram_contracts": len(telegram_cas.data.data),
            "recent_news": len(news.data),
            "top_token_changes": [
                {
                    "token": t.token,
                    "mentions": t.current_count,
                    "change": t.change_percent,
                }
                for t in trending_tokens.data.data[:3]
            ],
        }
    except ElfaAPIError as e:
        print(f"❌ Error getting market overview: {e}")
        return {}


async def main():
    """Main async function demonstrating various SDK capabilities"""
    # Get API key from environment variable
    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("Please set the ELFA_API_KEY environment variable")
        return

    # Use async context manager for proper resource cleanup
    async with AsyncElfaClient(api_key=api_key) as client:
        try:
            # 1. Basic health check
            print("🏥 Checking API health...")
            ping = await client.ping()
            print(f"✅ API is healthy: {ping.data['message']}")
            print()

            # 2. Get trending analysis
            trending_analysis = await get_trending_analysis(client)
            if trending_analysis:
                print(f"📈 Trending Analysis:")
                print(
                    f"   • Hourly trending: {trending_analysis['hourly_count']} tokens"
                )
                print(f"   • Daily trending: {trending_analysis['daily_count']} tokens")
                print(
                    f"   • Weekly trending: {trending_analysis['weekly_count']} tokens"
                )
                print(
                    f"   • Consistently trending: {trending_analysis['consistent_trending']}"
                )
                print()

                # Show top daily tokens
                print("🏆 Top trending tokens (24h):")
                for i, token in enumerate(trending_analysis["top_daily"], 1):
                    change_emoji = "📈" if token.change_percent > 0 else "📉"
                    print(
                        f"   {i}. {token.token}: {token.current_count} mentions "
                        f"({change_emoji} {token.change_percent:+.1f}%)"
                    )
                print()

            # 3. Search multiple keywords concurrently
            keywords = ["bitcoin", "ethereum", "solana", "cardano", "polkadot"]
            mention_counts = await search_multiple_keywords(client, keywords)

            if mention_counts:
                print("🔍 Keyword mention counts (24h):")
                sorted_keywords = sorted(
                    mention_counts.items(), key=lambda x: x[1], reverse=True
                )
                for keyword, count in sorted_keywords:
                    print(f"   • {keyword}: {count} mentions")
                print()

            # 4. Analyze top crypto accounts
            crypto_accounts = [
                "elonmusk",
                "VitalikButerin",
                "michael_saylor",
                "cz_binance",
            ]
            account_stats = await analyze_top_accounts(client, crypto_accounts)

            print("👥 Account analysis:")
            # Sort by smart following count
            account_stats.sort(key=lambda x: x.get("smart_following", 0), reverse=True)
            for stats in account_stats:
                if "error" not in stats:
                    print(
                        f"   • @{stats['username']}: "
                        f"{stats['smart_following']:.0f} smart following, "
                        f"{stats['engagement_ratio']:.3f} engagement ratio"
                    )
                else:
                    print(f"   • @{stats['username']}: Error - {stats['error']}")
            print()

            # 5. Get comprehensive market overview
            market_overview = await get_market_overview(client)
            if market_overview:
                print("📊 Market Overview:")
                print(
                    f"   • Trending tokens: {market_overview['trending_tokens_count']}"
                )
                print(f"   • Twitter contracts: {market_overview['twitter_contracts']}")
                print(
                    f"   • Telegram contracts: {market_overview['telegram_contracts']}"
                )
                print(f"   • Recent news items: {market_overview['recent_news']}")
                print()

                print("🚀 Top movers:")
                for token_data in market_overview["top_token_changes"]:
                    change_emoji = "📈" if token_data["change"] > 0 else "📉"
                    print(
                        f"   • {token_data['token']}: {token_data['mentions']} mentions "
                        f"({change_emoji} {token_data['change']:+.1f}%)"
                    )

            # 6. Demonstrate concurrent API key status and account search
            print("\n⚡ Concurrent operations...")
            start_time = asyncio.get_event_loop().time()

            # Run multiple operations concurrently
            status_task = client.get_api_key_status()
            search_task = client.get_keyword_mentions(keywords="defi", limit=5)

            status, search_results = await asyncio.gather(status_task, search_task)

            end_time = asyncio.get_event_loop().time()
            print(
                f"✅ Completed concurrent operations in {end_time - start_time:.2f} seconds"
            )
            print(
                f"   • API usage: {status.data.usage.today}/{status.data.daily_limit} daily"
            )
            print(f"   • DeFi mentions found: {len(search_results.data)}")

        except ElfaAPIError as e:
            print(f"❌ API Error: {e}")
        except Exception as e:
            print(f"💥 Unexpected error: {e}")


def run_async_example():
    """Entry point for running the async example"""
    print("🚀 Starting Elfa SDK Async Example")
    print("=" * 50)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Example interrupted by user")
    except Exception as e:
        print(f"💥 Failed to run async example: {e}")

    print("\n✅ Async example completed!")


if __name__ == "__main__":
    run_async_example()
