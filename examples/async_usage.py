"""Basic asynchronous usage. Run with ELFA_API_KEY set."""

import asyncio
import os

from elfa import AsyncElfaClient


async def main() -> None:
    async with AsyncElfaClient(api_key=os.environ["ELFA_API_KEY"]) as client:
        ping, trending = await asyncio.gather(
            client.ping(),
            client.get_trending_tokens(time_window="24h", page_size=5),
        )
        print("ping:", ping.data.message)
        for token in trending.data.data:
            print(token.token, token.current_count)

        narratives = await client.get_trending_narratives(
            time_frame="day", max_narratives=3
        )
        for item in narratives.data.trending_narratives:
            print("narrative:", item.narrative)


if __name__ == "__main__":
    asyncio.run(main())
