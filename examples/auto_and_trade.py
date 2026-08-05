"""Auto condition engine + direct trading.

Notification-only Auto queries need no HMAC secret. Trade-action queries and all
``client.trade`` writes require ``hmac_secret`` (generate one in the dev portal)
and a Privy-linked exchange account. Sizes and prices are decimal strings.
"""

import os

from elfa import ElfaClient

NOTIFY_QUERY = {
    "query": {
        "conditions": {
            "AND": [
                {
                    "source": "price",
                    "method": "current",
                    "args": {"symbol": "BTC", "exchange": "hyperliquid"},
                    "operator": ">",
                    "value": 250_000,
                }
            ]
        },
        "actions": [
            {"stepId": "notify", "type": "notify", "params": {"message": "BTC > 250k"}}
        ],
        "expiresIn": "24h",
    },
    "title": "btc breakout alert",
}


def main() -> None:
    with ElfaClient(
        api_key=os.environ["ELFA_API_KEY"],
        hmac_secret=os.environ.get("ELFA_HMAC_SECRET"),
    ) as client:
        validation = client.auto.validate_query(NOTIFY_QUERY)
        print("valid:", validation.valid)

        created = client.auto.create_query(NOTIFY_QUERY)
        query_id = created.id or created.query_id
        print("created:", query_id)

        polled = client.auto.get_query(query_id)
        print("status:", polled.status)

        client.auto.cancel_query(query_id)
        client.auto.delete_query(query_id)

        # Preview an order (no execution). Requires a linked exchange account.
        preview = client.trade.preview_order(
            {
                "exchange": "hyperliquid",
                "symbol": "BTC",
                "side": "buy",
                "orderType": "market",
                "size": "0.001",
            }
        )
        print("would execute:", preview.would_execute)


if __name__ == "__main__":
    main()
