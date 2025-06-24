"""
Basic usage examples for the Elfa Python SDK

This example demonstrates the most common use cases for the Elfa API,
including getting trending tokens, searching mentions, and checking account stats.

Requirements:
- Set ELFA_API_KEY environment variable with your API key
- Install the SDK: pip install elfa-ai
"""

import os

from elfa import ElfaClient
from elfa.exceptions import ElfaAPIError


def main():
    # Get API key from environment variable
    api_key = os.getenv("ELFA_API_KEY")
    if not api_key:
        print("Please set the ELFA_API_KEY environment variable")
        return

    # Initialize the client
    client = ElfaClient(api_key=api_key)

    try:
        # 1. Health check
        print("🏥 Checking API health...")
        ping = client.ping()
        print(f"✅ API is healthy: {ping.data['message']}")
        print()

        # 2. Check API key status
        print("🔑 Checking API key status...")
        status = client.get_api_key_status()
        print(f"📊 API Key: {status.data.name}")
        print(f"📈 Daily usage: {status.data.usage.today}/{status.data.daily_limit}")
        print(
            f"📅 Monthly usage: {status.data.usage.month}/{status.data.monthly_limit}"
        )
        print()

        # 3. Get trending tokens
        print("🔥 Getting trending tokens...")
        trending = client.get_trending_tokens(
            time_window="24h", page_size=10, min_mentions=5
        )

        print(f"📈 Found {len(trending.data.data)} trending tokens:")
        for i, token in enumerate(trending.data.data[:5], 1):
            change_emoji = "📈" if token.change_percent > 0 else "📉"
            print(
                f"  {i}. {token.token}: {token.current_count} mentions "
                f"({change_emoji} {token.change_percent:+.1f}%)"
            )
        print()

        # 4. Search for Bitcoin mentions
        print("₿ Searching for Bitcoin mentions...")
        mentions = client.get_keyword_mentions(
            keywords="bitcoin", period="24h", limit=5
        )

        print(f"💬 Found {len(mentions.data)} Bitcoin mentions:")
        for i, mention in enumerate(mentions.data, 1):
            account = mention.account
            verified = "✅" if account and account.is_verified else ""
            username = account.username if account else "unknown"

            print(f"  {i}. @{username} {verified}")
            print(
                f"     ❤️ {mention.like_count or 0} likes | "
                f"🔄 {mention.repost_count or 0} reposts | "
                f"👁️ {mention.view_count or 0} views"
            )
            print(f"     🔗 {mention.link}")
            print()

        # 5. Get account smart stats for a popular crypto account
        print("📊 Getting smart stats for @elonmusk...")
        try:
            stats = client.get_account_smart_stats(username="elonmusk")
            print(f"🧠 Smart following count: {stats.data.smart_following_count}")
            print(
                f"📊 Follower engagement ratio: {stats.data.follower_engagement_ratio:.3f}"
            )
            print(f"⭐ Average engagement: {stats.data.average_engagement:.3f}")
        except ElfaAPIError as e:
            print(f"❌ Could not get stats for @elonmusk: {e}")
        print()

        # 6. Get trending contract addresses
        print("📄 Getting trending contract addresses on Twitter...")
        try:
            cas = client.get_trending_contract_addresses_twitter(
                time_window="24h", page_size=5, min_mentions=3
            )

            print(f"🏆 Found {len(cas.data.data)} trending contracts:")
            for i, ca in enumerate(cas.data.data, 1):
                chain_emoji = "🔷" if ca.chain == "ethereum" else "☀️"
                print(
                    f"  {i}. {ca.contract_address[:10]}... ({chain_emoji} {ca.chain})"
                )
                print(
                    f"     💬 {ca.mention_count} mentions ({ca.change_percent:+.1f}%)"
                )
        except ElfaAPIError as e:
            print(f"❌ Could not get trending contracts: {e}")
        print()

        # 7. Get token news
        print("📰 Getting recent token news...")
        try:
            news = client.get_token_news(coin_ids="bitcoin,ethereum", page_size=3)

            print(f"📰 Found {len(news.data)} news mentions:")
            for i, item in enumerate(news.data, 1):
                account = item.account
                verified = "✅" if account and account.is_verified else ""
                username = account.username if account else "unknown"

                print(f"  {i}. @{username} {verified}")
                print(
                    f"     📊 {item.like_count or 0} likes | "
                    f"{item.repost_count or 0} reposts"
                )
                print(f"     🔗 {item.link}")
        except ElfaAPIError as e:
            print(f"❌ Could not get token news: {e}")

    except ElfaAPIError as e:
        print(f"❌ API Error: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
    finally:
        # Clean up the client
        client.close()


if __name__ == "__main__":
    main()
