"""Basic synchronous usage. Run with ELFA_API_KEY set."""

import os

from elfa import ElfaClient


def main() -> None:
    with ElfaClient(api_key=os.environ["ELFA_API_KEY"]) as client:
        print("ping:", client.ping().data.message)

        trending = client.get_trending_tokens(time_window="24h", page_size=5)
        for token in trending.data.data:
            print(
                f"{token.token}: {token.current_count} ({token.change_percent:+.1f}%)"
            )

        mentions = client.get_keyword_mentions(
            keywords="bitcoin", time_window="1h", limit=5
        )
        print(f"{mentions.metadata.total} mentions; showing {len(mentions.data)}")
        for mention in mentions.data:
            print(mention.link, mention.like_count)

        stats = client.get_account_smart_stats("elonmusk")
        print("smart following:", stats.data.smart_following_count)

        answer = client.chat("What's the market sentiment on Bitcoin today?")
        print("chat:", answer.data.message)


if __name__ == "__main__":
    main()
