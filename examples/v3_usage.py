"""API v3. Run with ELFA_API_KEY set to a PAYG, Grow or Enterprise key."""

import os
import time

from elfa import ElfaClient


def main() -> None:
    with ElfaClient(api_key=os.environ["ELFA_API_KEY"]) as client:
        entities = client.v3.get_entities("btc", entity_type=["token"], limit=1)
        if not entities.entities:
            raise SystemExit("no exact match")
        bitcoin = entities.entities[0]
        print("resolved:", bitcoin.name, bitcoin.id)

        since = int(time.time()) - 86400
        events = client.v3.get_events(
            entity_ids=[bitcoin.id], from_time=since, limit=10
        )
        for event in events.events:
            print(event.implication, event.alert_title)

        positioning = client.v3.get_positioning(bitcoin.id)
        print("open long:", positioning.open_long, "short:", positioning.open_short)

        status = client.v3.get_key_status()
        print("plan:", status.plan, "history from:", status.history_from)


if __name__ == "__main__":
    main()
