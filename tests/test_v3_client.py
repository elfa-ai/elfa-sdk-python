"""API v3 client: paths, exact query params, parsing, and errors."""

import json
from typing import get_args

import httpx
import pytest
import respx

from elfa import AsyncElfaClient, AsyncV3Client, ElfaClient, V3Client
from elfa.exceptions import ElfaAPIError, ElfaValidationError
from elfa.models import (
    AccountMetricV3,
    CalendarCategoryV3,
    CalendarConfidenceV3,
    CalendarStatusV3,
)
from elfa.utils.http import AsyncTransport, SyncTransport
from tests.conftest import BASE_URL

BTC = "360fd4a8-46e3-4713-8a91-3627b86029fc"
ETH = "5c1b6a2e-7a0f-4f55-9a43-1e0d2f6c9b10"

ENTITY = {
    "id": BTC,
    "entityType": "token",
    "name": "Bitcoin",
    "symbol": "BTC",
    "handle": None,
    "matchedOn": "symbol",
    "score": 0.9,
    "externalIds": {"coingeckoId": "bitcoin", "figi": None, "cik": None},
}

EVENT = {
    "id": "107519d5-0ca8-4fb5-a9de-47808bceb407",
    "eventClass": "market",
    "alertTitle": "Block adds 3% back in Bitcoin on Square Credit Card",
    "summary": "Eligible purchases earn 3% back in Bitcoin.",
    "implication": "bullish",
    "eventType": "company",
    "primaryEntities": [
        {"id": BTC, "symbol": "BTC", "name": "Bitcoin", "entityType": "token"}
    ],
    "relatedEntities": [],
    "alertAction": "alert",
    "originCount": 2,
    "impacts": [
        {
            "entityId": BTC,
            "symbol": "BTC",
            "priceChange1d": 0.0157,
            "movedFirst": False,
            "marketWide": None,
            "final": False,
        }
    ],
    "analyzedAt": 1791887446,
    "novelty": "new",
    "firstSeenAt": 1791886696,
    "storylineId": "75b85796-57a5-4556-adc6-b078650ea305",
    "citedSources": [
        {
            "source": "twitter",
            "sourceRecordId": "2109951850128486490",
            "handle": "BitcoinMagazine",
            "link": "https://x.com/BitcoinMagazine/status/2109951850128486490",
        }
    ],
    "positions": None,
}

STORYLINE = {
    "id": "ad29d7ce-20e3-4941-81d5-31559aa51f4a",
    "title": "Analyst downgrades AST SpaceMobile",
    "summary": "Cut to Neutral, citing launch delays.",
    "status": "open",
    "entities": [],
    "startedAt": 1791888054,
    "lastEventAt": 1791888054,
    "lastMaterialAt": 1791888054,
    "arcId": None,
    "events": [
        {
            "eventId": "3efa648d-0e9a-470b-8e07-24b79ed4a069",
            "relation": "origin",
            "material": True,
            "occurredAt": 1791888054,
        }
    ],
}

ARC = {
    "id": "bd236c7e-14f1-420c-bb52-a3c6bf3a8c7e",
    "name": "Fed calls for tighter policy",
    "summary": None,
    "status": "active",
    "storylineIds": ["1b1772a5-6f85-4ab7-bca8-cbe97eda33e0"],
    "updatedAt": 1791885723,
}

BAR = {
    "barAt": 1791888000,
    "live": True,
    "longShare": 97.41,
    "shortShare": 2.59,
    "crowdingPercentile": 82.7,
    "accountCount": 11433,
    "pulse24": 36.1,
    "pulse24LongShare": 84.2,
    "pulse6": None,
    "pulse6LongShare": None,
    "formulaVersion": "sentiment.v4",
    "computedAt": 1791888036,
}

MINDSHARE = {
    "rank": 1,
    "id": "9cc25a1a-ca6a-4dcb-a8dd-0963a9834750",
    "symbol": "JPM",
    "name": "JPMorgan Chase & Co.",
    "share": 4.15,
    "changePct": None,
    "hot": True,
    "share1h": 9.21,
    "share4h": 4.15,
    "ratio1h4h": 2.22,
    "capped1h": 14,
}

CONTRACT = {
    "rank": 1,
    "contractAddress": "68fn2tLABKmS7VA9Eaz3n6RfoXM3iBWUACckT9dwpump",
    "mentionCount": 63,
    "asset": None,
}

TRACK = {
    "alphaScore": -0.018,
    "hitRate": 0.5,
    "avgReturn": 0.047,
    "scoredEpisodes": 4,
    "totalEpisodes": 16,
}

ASSET = {"id": BTC, "symbol": "BTC", "name": "Bitcoin", "entityType": "token"}

CALL = {
    "id": "57d351ab-55df-440b-a471-5518a34ccced",
    "episodeId": "c31eadd7-890b-4aba-96a1-8606b8284ebb",
    "handle": "PostyXBT",
    "source": "twitter",
    "channel": None,
    "asset": ASSET,
    "callAction": "reaffirm",
    "setup": None,
    "thesis": None,
    "sourceRecordId": "2109956562370633964",
    "occurredAt": 1791887820,
}

EPISODE = {
    "id": "c31eadd7-890b-4aba-96a1-8606b8284ebb",
    "handle": "PostyXBT",
    "source": "twitter",
    "channel": None,
    "asset": ASSET,
    "direction": "long",
    "horizon": "swing",
    "status": "open",
    "openedAt": 1791800000,
    "closedAt": None,
    "observedAt": 1791800013,
    "entryPrice": 112000.5,
    "exitPrice": None,
    "closeReason": None,
    "setup": "technical",
    "thesis": None,
    "statedTarget": None,
    "statedStop": None,
    "track": TRACK,
    "calls": [
        {
            "callId": "57d351ab-55df-440b-a471-5518a34ccced",
            "callAction": "open",
            "occurredAt": 1791800000,
        }
    ],
}

ACCOUNT = {
    "rank": 1,
    "handle": "blknoiz06",
    "name": "Ansem",
    "followerCount": 1448477,
    "verified": False,
    "standing": 1,
    "track": None,
}

KEY_STATUS = {
    "plan": "grow",
    "billingMode": "arrears",
    "owner": "user",
    "scopes": ["key-status", "events", "entities"],
    "credits": {
        "limit": 120000,
        "used": 36,
        "remaining": 119964,
        "resetsAt": 1793491200,
        "requestsPerMinute": 120,
    },
    "historyFrom": 1786665600,
}


CALENDAR_ENTRY = {
    "id": "0c4f9a52-2b8e-4d7c-9f1a-6e3d2b1c0a99",
    "title": "FOMC rate decision",
    "summary": None,
    "category": "macro",
    "startsAt": 1795111200,
    "endsAt": None,
    "precision": "exact",
    "date": None,
    "endDate": None,
    "timezone": "America/New_York",
    "status": "scheduled",
    "importance": 95,
    "confidence": "official",
    "entities": [],
    "eventIds": [EVENT["id"]],
    "storylineIds": [],
    "outcome": None,
}

PREDICTION_MARKETS = {
    "related": [
        {
            "id": "634a083e-7b5b-4a35-9f53-28ee58e2fb1b",
            "kind": "storyline",
            "markets": [
                {
                    "provider": "kalshi",
                    "marketId": "KXWTI-26NOV0414",
                    "title": "Oil Price (WTI) on Nov 4, 2026? Nov 4, 2026",
                    "url": "https://kalshi.com/markets/KXWTI-26NOV0414",
                    "closesAt": 1793820600,
                    "eventIds": ["55c71f1e-5fe6-44b0-a482-0277c6dfe7c7"],
                    "move": None,
                },
                {
                    "provider": "polymarket",
                    "marketId": "326475",
                    "title": "Iran agrees to end enrichment of uranium by December 31?",
                    "url": "https://polymarket.com/event/326475",
                    "closesAt": None,
                    "eventIds": ["126848ca-8cb2-4b7f-9664-7b94aa54da13"],
                    "move": {
                        "eventId": "126848ca-8cb2-4b7f-9664-7b94aa54da13",
                        "outcomeId": "1796138",
                        "outcome": None,
                        "before": 0.045,
                        "after": 0.072,
                        "unusual": True,
                    },
                },
            ],
        }
    ]
}


def _page(key, items, served=True):
    body = {key: items, "nextCursor": "abc.def", "hasMore": True}
    if served:
        body["servedFrom"] = 1791801662
    return body


def _client():
    return V3Client(transport=SyncTransport("k", BASE_URL, retries=0))


def _params(route):
    return dict(route.calls[-1].request.url.params)


@respx.mock
def test_get_entities_comma_joins_entity_type_and_parses():
    route = respx.get(f"{BASE_URL}/v3/entities").mock(
        return_value=httpx.Response(
            200, json={"entities": [ENTITY], "nextCursor": None, "hasMore": False}
        )
    )
    result = _client().get_entities("btc", entity_type=["token", "equity"], limit=1)

    assert _params(route) == {"q": "btc", "entityType": "token,equity", "limit": "1"}
    match = result.entities[0]
    assert match.id == BTC
    assert match.entity_type == "token"
    assert match.external_ids.coingecko_id == "bitcoin"
    assert result.next_cursor is None
    assert result.has_more is False


@respx.mock
def test_empty_list_raises_instead_of_dropping_the_filter():
    route = respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(200, json=_page("events", [EVENT]))
    )
    with pytest.raises(ElfaValidationError, match="entity_ids is empty"):
        _client().get_events(from_time=1, entity_ids=[])

    assert not route.called


def test_get_entities_requires_q():
    with pytest.raises(ElfaValidationError):
        _client().get_entities("")


@respx.mock
def test_get_events_maps_every_param():
    route = respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(200, json=_page("events", [EVENT]))
    )
    result = _client().get_events(
        q="etf",
        from_time=1791801662,
        to_time=1791888062,
        event_ids=["e1", "e2"],
        event_class="market",
        event_type="regulatory",
        implication="bearish",
        entity_ids=[BTC, ETH],
        asset_class="crypto",
        novelty="new",
        alert_action=["alert", "monitor"],
        sort="latest",
        has_storyline=True,
        arc_id="a1",
        notable=False,
        order="asc",
        limit=30,
        cursor="c1",
    )

    assert _params(route) == {
        "q": "etf",
        "from": "1791801662",
        "to": "1791888062",
        "eventIds": "e1,e2",
        "eventClass": "market",
        "eventType": "regulatory",
        "implication": "bearish",
        "entityIds": f"{BTC},{ETH}",
        "assetClass": "crypto",
        "novelty": "new",
        "alertAction": "alert,monitor",
        "sort": "latest",
        "hasStoryline": "true",
        "arcId": "a1",
        "notable": "false",
        "order": "asc",
        "limit": "30",
        "cursor": "c1",
    }
    event = result.events[0]
    assert event.alert_title.startswith("Block")
    assert event.primary_entities[0].symbol == "BTC"
    assert event.impacts[0].price_change_1d == 0.0157
    assert event.impacts[0].market_wide is None
    assert event.cited_sources[0].source_record_id == "2109951850128486490"
    assert event.positions is None
    assert result.next_cursor == "abc.def"
    assert result.served_from == 1791801662


@respx.mock
def test_get_events_sends_only_what_was_set():
    route = respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(200, json=_page("events", []))
    )
    _client().get_events(entity_ids=[BTC], from_time=1791801662)
    assert _params(route) == {"entityIds": BTC, "from": "1791801662"}


@respx.mock
def test_get_events_accepts_a_single_id_string():
    route = respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(200, json=_page("events", []))
    )
    _client().get_events(event_ids=BTC)
    assert _params(route) == {"eventIds": BTC}


@respx.mock
def test_get_storylines_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/events/storylines").mock(
        return_value=httpx.Response(200, json=_page("storylines", [STORYLINE]))
    )
    result = _client().get_storylines(
        from_time=1791801662,
        storyline_ids=["s1", "s2"],
        entity_ids=[BTC],
        status="any",
        relation=["origin", "update"],
        limit=2,
    )

    assert _params(route) == {
        "from": "1791801662",
        "storylineIds": "s1,s2",
        "entityIds": BTC,
        "status": "any",
        "relation": "origin,update",
        "limit": "2",
    }
    storyline = result.storylines[0]
    assert storyline.last_material_at == 1791888054
    assert storyline.events[0].relation == "origin"
    assert storyline.arc_id is None


@respx.mock
def test_get_arcs_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/events/arcs").mock(
        return_value=httpx.Response(200, json=_page("arcs", [ARC], served=False))
    )
    result = _client().get_arcs(
        arc_ids=["a1", "a2"], status="retired", order="desc", cursor="c"
    )

    assert _params(route) == {
        "arcIds": "a1,a2",
        "status": "retired",
        "order": "desc",
        "cursor": "c",
    }
    assert result.arcs[0].storyline_ids == ["1b1772a5-6f85-4ab7-bca8-cbe97eda33e0"]
    assert result.arcs[0].summary is None


@respx.mock
def test_get_arcs_narratives_params():
    route = respx.get(f"{BASE_URL}/v3/events/arcs").mock(
        return_value=httpx.Response(200, json=_page("arcs", [], served=False))
    )
    _client().get_arcs(asset_class="equity", entity_ids=[BTC, ETH], sort="events")
    assert _params(route) == {
        "assetClass": "equity",
        "entityIds": f"{BTC},{ETH}",
        "sort": "events",
    }


@pytest.mark.parametrize("market", ["crypto", "equity"])
@respx.mock
def test_get_call_book_maps_market_to_path(market):
    route = respx.get(f"{BASE_URL}/v3/market/{market}/call-book").mock(
        return_value=httpx.Response(200, json=_page("bars", [BAR]))
    )
    result = _client().get_call_book(
        market, from_time=1791801662, to_time=1791888062, order="asc", limit=168
    )

    assert _params(route) == {
        "from": "1791801662",
        "to": "1791888062",
        "order": "asc",
        "limit": "168",
    }
    bar = result.bars[0]
    assert bar.live is True
    assert bar.account_count == 11433
    assert bar.pulse6 is None
    assert result.served_from == 1791801662


@pytest.mark.parametrize("market", ["crypto", "equity"])
@respx.mock
def test_get_mindshare_maps_market_to_path(market):
    route = respx.get(f"{BASE_URL}/v3/market/{market}/mindshare").mock(
        return_value=httpx.Response(200, json=_page("assets", [MINDSHARE], False))
    )
    result = _client().get_mindshare(market, period="24h", to_time=1791888000)

    assert _params(route) == {"period": "24h", "to": "1791888000"}
    asset = result.assets[0]
    assert asset.hot is True
    assert asset.ratio_1h_4h == 2.22
    assert asset.capped_1h == 14
    assert asset.change_pct is None


def test_market_must_be_crypto_or_equity():
    client = _client()
    with pytest.raises(ElfaValidationError):
        client.get_call_book("forex", from_time=1)
    with pytest.raises(ElfaValidationError):
        client.get_mindshare("crypto/../x")


@respx.mock
def test_get_trending_contracts_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/market/crypto/trending-contracts").mock(
        return_value=httpx.Response(200, json=_page("contracts", [CONTRACT]))
    )
    result = _client().get_trending_contracts(
        from_time=1791801662, min_mentions=10, limit=200
    )

    assert _params(route) == {
        "from": "1791801662",
        "minMentions": "10",
        "limit": "200",
    }
    assert result.contracts[0].mention_count == 63
    assert result.contracts[0].asset is None


@respx.mock
def test_get_calls_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/calls").mock(
        return_value=httpx.Response(200, json=_page("calls", [CALL]))
    )
    result = _client().get_calls(
        from_time=1791801662,
        call_ids=["c1", "c2"],
        handle="PostyXBT",
        entity_ids=[BTC],
        order="desc",
    )

    assert _params(route) == {
        "from": "1791801662",
        "callIds": "c1,c2",
        "handle": "PostyXBT",
        "entityIds": BTC,
        "order": "desc",
    }
    call = result.calls[0]
    assert call.call_action == "reaffirm"
    assert call.asset is not None and call.asset.entity_type == "token"
    assert call.channel is None


@respx.mock
def test_get_call_episodes_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/calls/episodes").mock(
        return_value=httpx.Response(200, json=_page("episodes", [EPISODE]))
    )
    result = _client().get_call_episodes(
        from_time=1791801662,
        to_time=1791888062,
        episode_ids=["p1", "p2"],
        handle="PostyXBT",
        entity_ids=[BTC, ETH],
        status="open",
        direction="long",
        asset_class="crypto",
        order="asc",
        limit=5,
        cursor="c",
    )

    assert _params(route) == {
        "from": "1791801662",
        "to": "1791888062",
        "episodeIds": "p1,p2",
        "handle": "PostyXBT",
        "entityIds": f"{BTC},{ETH}",
        "status": "open",
        "direction": "long",
        "assetClass": "crypto",
        "order": "asc",
        "limit": "5",
        "cursor": "c",
    }
    episode = result.episodes[0]
    assert episode.entry_price == 112000.5
    assert episode.closed_at is None
    assert episode.track is not None and episode.track.scored_episodes == 4
    assert episode.calls[0].call_action == "open"


@respx.mock
def test_get_positioning_sends_singular_entity_id():
    route = respx.get(f"{BASE_URL}/v3/calls/positioning").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": BTC,
                "symbol": "BTC",
                "name": "Bitcoin",
                "openLong": 4344,
                "openShort": 588,
                "asOf": 1791887832,
            },
        )
    )
    result = _client().get_positioning(BTC)

    assert _params(route) == {"entityId": BTC}
    assert result.open_long == 4344
    assert result.open_short == 588
    assert result.as_of == 1791887832


def test_get_positioning_requires_entity_id():
    with pytest.raises(ElfaValidationError):
        _client().get_positioning("")


@respx.mock
def test_get_top_accounts_maps_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/people/accounts").mock(
        return_value=httpx.Response(200, json=_page("accounts", [ACCOUNT], False))
    )
    result = _client().get_top_accounts(metric="standing", order="asc", limit=3)

    assert _params(route) == {"metric": "standing", "order": "asc", "limit": "3"}
    account = result.accounts[0]
    assert account.handle == "blknoiz06"
    assert account.standing == 1.0
    assert account.track is None


def test_account_metric_matches_spec():
    assert get_args(AccountMetricV3) == (
        "standing",
        "alphaScore",
        "hitRate",
        "avgReturn",
    )


@respx.mock
@pytest.mark.parametrize("metric", ["alphaScore", "hitRate", "avgReturn"])
def test_get_top_accounts_ranks_by_track_metric(metric):
    route = respx.get(f"{BASE_URL}/v3/people/accounts").mock(
        return_value=httpx.Response(200, json=_page("accounts", [ACCOUNT], False))
    )
    _client().get_top_accounts(metric=metric, limit=2)

    assert _params(route) == {"metric": metric, "limit": "2"}


@respx.mock
def test_get_key_status_sends_no_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/key-status").mock(
        return_value=httpx.Response(200, json=KEY_STATUS)
    )
    result = _client().get_key_status()

    assert _params(route) == {}
    assert result.plan == "grow"
    assert result.billing_mode == "arrears"
    assert result.credits.requests_per_minute == 120
    assert result.credits.resets_at == 1793491200
    assert result.history_from == 1786665600


@respx.mock
def test_get_prediction_markets_comma_joins_ids_and_parses():
    route = respx.get(f"{BASE_URL}/v3/events/prediction-markets").mock(
        return_value=httpx.Response(200, json=PREDICTION_MARKETS)
    )
    result = _client().get_prediction_markets(["e1", "s1"], limit=5)

    assert _params(route) == {"ids": "e1,s1", "limit": "5"}
    related = result.related[0]
    assert related.kind == "storyline"
    daily, iran = related.markets
    assert daily.move is None
    assert daily.closes_at == 1793820600
    assert iran.market_id == "326475"
    assert iran.closes_at is None
    assert iran.move is not None
    assert iran.move.outcome is None
    assert iran.move.after == 0.072
    assert iran.move.unusual is True


@pytest.mark.parametrize("ids", [[], ""])
def test_get_prediction_markets_requires_ids(ids):
    with pytest.raises(ElfaValidationError):
        _client().get_prediction_markets(ids)


@respx.mock
def test_get_calendar_sends_no_range_by_default():
    route = respx.get(f"{BASE_URL}/v3/events/calendar").mock(
        return_value=httpx.Response(200, json=_page("entries", [CALENDAR_ENTRY]))
    )
    result = _client().get_calendar()

    assert _params(route) == {}
    entry = result.entries[0]
    assert entry.starts_at == 1795111200
    assert entry.ends_at is None
    assert entry.precision == "exact"
    assert entry.importance == 95
    assert entry.event_ids == [EVENT["id"]]
    assert entry.outcome is None
    assert result.next_cursor == "abc.def"
    assert result.served_from == 1791801662


@respx.mock
def test_get_calendar_maps_every_param():
    route = respx.get(f"{BASE_URL}/v3/events/calendar").mock(
        return_value=httpx.Response(
            200,
            json=_page(
                "entries",
                [
                    {
                        **CALENDAR_ENTRY,
                        "precision": "day",
                        "date": "2026-11-20",
                        "status": "occurred",
                        "outcome": {"eventId": EVENT["id"], "implication": None},
                    }
                ],
            ),
        )
    )
    result = _client().get_calendar(
        from_time=1791801662,
        to_time=1794393662,
        entity_ids=[BTC, ETH],
        asset_class="crypto",
        category=["unlock", "listing"],
        status=["scheduled", "rescheduled"],
        confidence=["official"],
        min_importance=80,
        order="desc",
        limit=30,
        cursor="abc.def",
    )

    assert _params(route) == {
        "from": "1791801662",
        "to": "1794393662",
        "entityIds": f"{BTC},{ETH}",
        "assetClass": "crypto",
        "category": "unlock,listing",
        "status": "scheduled,rescheduled",
        "confidence": "official",
        "minImportance": "80",
        "order": "desc",
        "limit": "30",
        "cursor": "abc.def",
    }
    entry = result.entries[0]
    assert entry.date == "2026-11-20"
    assert entry.outcome is not None
    assert entry.outcome.event_id == EVENT["id"]
    assert entry.outcome.implication is None


def test_calendar_enums_match_spec():
    assert get_args(CalendarCategoryV3) == (
        "macro",
        "earnings",
        "unlock",
        "governance",
        "listing",
        "launch",
        "airdrop",
        "conference",
        "regulatory",
        "protocolUpgrade",
        "corporateAction",
        "marketResolution",
        "campaign",
        "expiry",
        "deadline",
        "geopolitics",
        "other",
    )
    assert get_args(CalendarStatusV3) == (
        "scheduled",
        "rescheduled",
        "postponed",
        "cancelled",
        "past",
        "occurred",
    )
    assert get_args(CalendarConfidenceV3) == ("official", "reported", "rumored")


@respx.mock
def test_v3_400_raises_validation_error_with_request_id():
    respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(
            400,
            json={
                "code": "ERR_INVALID_PARAMETER",
                "message": "Invalid parameters",
                "details": [{"field": "query.from", "message": "from is required"}],
                "errorId": "8d935689",
                "requestId": "req-1",
            },
            headers={"x-request-id": "req-1"},
        )
    )
    with pytest.raises(ElfaValidationError) as exc:
        _client().get_events(entity_ids=[BTC])
    assert exc.value.status_code == 400
    assert exc.value.message == "Invalid parameters: query.from: from is required"
    assert exc.value.validation_errors == [
        {"field": "query.from", "message": "from is required"}
    ]
    assert exc.value.request_id == "req-1"


@respx.mock
def test_v3_403_raises_api_error():
    message = "Forbidden"
    respx.get(f"{BASE_URL}/v3/calls/positioning").mock(
        return_value=httpx.Response(
            403,
            json={
                "code": "ERR_FORBIDDEN",
                "message": message,
                "errorId": "e",
                "requestId": "r",
            },
        )
    )
    with pytest.raises(ElfaAPIError) as exc:
        _client().get_positioning(BTC)
    assert exc.value.status_code == 403
    assert exc.value.message == message


@respx.mock
def test_elfa_client_v3_shares_transport_and_headers():
    route = respx.get(f"{BASE_URL}/v3/key-status").mock(
        return_value=httpx.Response(200, json=KEY_STATUS)
    )
    client = ElfaClient(api_key="k", base_url=BASE_URL, app_name="my-bot/1.2")
    assert client.v3._transport is client._transport
    assert client.v3._owns_transport is False

    client.v3.get_key_status()
    headers = route.calls[-1].request.headers
    assert headers["x-elfa-api-key"] == "k"
    assert headers["user-agent"].endswith(" my-bot/1.2")
    client.close()


def test_standalone_requires_api_key():
    with pytest.raises(ElfaValidationError):
        V3Client()
    with pytest.raises(ElfaValidationError):
        AsyncV3Client()


def test_close_only_affects_owned_transport():
    shared = SyncTransport("k", BASE_URL, retries=0)
    composed = V3Client(transport=shared)
    composed.close()
    assert shared._client.is_closed is False
    shared.close()

    standalone = V3Client(api_key="k", base_url=BASE_URL)
    assert standalone._owns_transport is True
    standalone.close()
    assert standalone._transport._client.is_closed is True


@respx.mock
async def test_async_get_events_and_positioning():
    events = respx.get(f"{BASE_URL}/v3/events").mock(
        return_value=httpx.Response(200, json=_page("events", [EVENT]))
    )
    respx.get(f"{BASE_URL}/v3/calls/positioning").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": BTC,
                "symbol": "BTC",
                "name": "Bitcoin",
                "openLong": 1,
                "openShort": 2,
                "asOf": 3,
            },
        )
    )
    async with AsyncElfaClient(api_key="k", base_url=BASE_URL, retries=0) as client:
        assert client.v3._transport is client._transport
        result = await client.v3.get_events(
            entity_ids=[BTC, ETH], from_time=1791801662, alert_action=["alert"]
        )
        positioning = await client.v3.get_positioning(BTC)

    assert _params(events) == {
        "entityIds": f"{BTC},{ETH}",
        "from": "1791801662",
        "alertAction": "alert",
    }
    assert result.events[0].id == EVENT["id"]
    assert positioning.open_short == 2


@respx.mock
async def test_async_get_prediction_markets():
    route = respx.get(f"{BASE_URL}/v3/events/prediction-markets").mock(
        return_value=httpx.Response(200, json=PREDICTION_MARKETS)
    )
    client = AsyncV3Client(transport=AsyncTransport("k", BASE_URL, retries=0))
    result = await client.get_prediction_markets(["e1"])

    assert _params(route) == {"ids": "e1"}
    assert result.related[0].markets[1].move is not None
    await client._transport.close()


@respx.mock
async def test_async_market_paths_and_key_status():
    book = respx.get(f"{BASE_URL}/v3/market/equity/call-book").mock(
        return_value=httpx.Response(200, json=_page("bars", [BAR]))
    )
    respx.get(f"{BASE_URL}/v3/market/crypto/mindshare").mock(
        return_value=httpx.Response(200, json=_page("assets", [], False))
    )
    respx.get(f"{BASE_URL}/v3/key-status").mock(
        return_value=httpx.Response(200, json=KEY_STATUS)
    )
    client = AsyncV3Client(transport=AsyncTransport("k", BASE_URL, retries=0))
    await client.get_call_book("equity", from_time=1791801662)
    mindshare = await client.get_mindshare("crypto")
    status = await client.get_key_status()

    assert _params(book) == {"from": "1791801662"}
    assert mindshare.assets == []
    assert status.history_from == 1786665600
    await client._transport.close()


@respx.mock
async def test_async_v3_error_propagates():
    respx.get(f"{BASE_URL}/v3/entities").mock(
        return_value=httpx.Response(
            400,
            json={
                "code": "ERR_INVALID_PARAMETER",
                "message": "Invalid parameters",
                "errorId": "e",
                "requestId": "r",
            },
        )
    )
    client = AsyncV3Client(transport=AsyncTransport("k", BASE_URL, retries=0))
    with pytest.raises(ElfaValidationError):
        await client.get_entities("btc")
    await client._transport.close()


@respx.mock
@pytest.mark.parametrize(
    "method, path, key, kwargs",
    [
        ("get_storylines", "/v3/events/storylines", "storylines", {"from_time": 1}),
        ("get_arcs", "/v3/events/arcs", "arcs", {}),
        ("get_calendar", "/v3/events/calendar", "entries", {}),
        (
            "get_trending_contracts",
            "/v3/market/crypto/trending-contracts",
            "contracts",
            {"from_time": 1},
        ),
        ("get_calls", "/v3/calls", "calls", {"from_time": 1}),
        ("get_call_episodes", "/v3/calls/episodes", "episodes", {"from_time": 1}),
        ("get_top_accounts", "/v3/people/accounts", "accounts", {}),
    ],
)
async def test_async_list_methods_hit_their_paths(method, path, key, kwargs):
    route = respx.get(f"{BASE_URL}{path}").mock(
        return_value=httpx.Response(200, json=_page(key, [], False))
    )
    client = AsyncV3Client(api_key="k", base_url=BASE_URL, retries=0)
    result = await getattr(client, method)(**kwargs)
    await client.close()

    assert route.called
    assert getattr(result, key) == []
    assert client._transport._client.is_closed is True


MONITOR_ID = "5b0c6f8e-2f7a-4f43-9a8e-3c1d2a9b7e10"

VERIFY = {
    "verdict": "supported",
    "probabilities": {
        "supported": 0.91,
        "contradicted": 0.03,
        "notEnoughEvidence": 0.06,
    },
    "decision": {"type": "yesNo", "yes": 0.9},
    "evidence": {
        "twitter": [
            {
                "link": "https://x.com/SECGov/status/1986070012345678901",
                "decisiveness": 0.95,
                "basis": True,
            }
        ],
        "telegram": [],
        "web": [],
    },
    "asOf": 1794960000,
    "searchedFrom": 1794355200,
    "coverage": {
        "complete": False,
        "sources": {"twitter": "complete", "telegram": "partial", "web": "complete"},
        "captions": "unavailable",
    },
}

MONITOR = {
    "id": MONITOR_ID,
    "query": "OpenAI, Google or Anthropic launches a new AI model",
    "webhookUrl": "https://example.com/elfa-webhook",
    "webhookSecret": "whsec_dGVzdA==",
    "status": "active",
    "createdAt": 1794981600,
    "updatedAt": 1794981600,
}

MATCH = {
    "id": "msg_2pQ",
    "monitorId": MONITOR_ID,
    "matchedAt": 1794985200,
    "items": [
        {
            "source": "event",
            "id": "107519d5-0ca8-4fb5-a9de-47808bceb407",
            "alertTitle": "Anthropic releases a new model",
            "summary": None,
            "analyzedAt": 1794985100,
            "citedSources": [
                {"source": "twitter", "sourceRecordId": None, "link": None}
            ],
        },
        {
            "source": "web",
            "id": "w1",
            "url": "https://www.example.com/news/model",
            "publishedAt": 1794980000,
            "publishedDayOnly": True,
        },
    ],
}


def _body(route):
    return json.loads(route.calls[-1].request.content)


@respx.mock
def test_verify_posts_compact_body_and_parses():
    route = respx.post(f"{BASE_URL}/v3/verify").mock(
        return_value=httpx.Response(200, json=VERIFY)
    )
    result = _client().verify(
        "The SEC approved a spot Solana ETF.",
        as_of=1794960000.0,
        context="Resolves yes on an SEC order.",
        decision={"type": "yesNo", "yes": "Approved"},
    )

    request = route.calls[-1].request
    assert request.headers["content-type"] == "application/json"
    assert request.content == (
        b'{"statement":"The SEC approved a spot Solana ETF.","asOf":1794960000,'
        b'"context":"Resolves yes on an SEC order.",'
        b'"decision":{"type":"yesNo","yes":"Approved"}}'
    )
    assert result.verdict == "supported"
    assert result.probabilities.not_enough_evidence == 0.06
    assert result.decision is not None
    assert result.decision.type == "yesNo"
    assert result.decision.yes == 0.9
    assert result.evidence.twitter[0].basis is True
    assert result.evidence.web == []
    assert result.as_of == 1794960000
    assert result.coverage.complete is False
    assert result.coverage.sources.telegram == "partial"


@respx.mock
def test_verify_sends_only_statement_by_default_and_parses_null_decision():
    route = respx.post(f"{BASE_URL}/v3/verify").mock(
        return_value=httpx.Response(200, json={**VERIFY, "decision": None})
    )
    result = _client().verify("Binance will list HYPE for spot trading.")

    assert _body(route) == {"statement": "Binance will list HYPE for spot trading."}
    assert result.decision is None


@respx.mock
def test_verify_parses_choice_and_score_decisions():
    route = respx.post(f"{BASE_URL}/v3/verify").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    **VERIFY,
                    "decision": {
                        "type": "choice",
                        "choice": "Yes",
                        "probabilities": {"Yes": 0.8, "No": 0.2},
                    },
                },
            ),
            httpx.Response(
                200,
                json={
                    **VERIFY,
                    "decision": {
                        "type": "score",
                        "score": 1.4,
                        "levelProbabilities": [0.1, 0.4, 0.5],
                    },
                },
            ),
        ]
    )
    client = _client()
    choice = client.verify(
        "s",
        decision={
            "type": "choice",
            "options": [
                {"label": "Yes", "definition": "It happened"},
                {"label": "No", "definition": "It did not"},
            ],
        },
    )
    assert _body(route)["decision"]["options"][1]["label"] == "No"
    score = client.verify("s", decision={"type": "score", "levels": ["a", "b", "c"]})

    assert choice.decision is not None
    assert choice.decision.choice == "Yes"
    assert choice.decision.probabilities == {"Yes": 0.8, "No": 0.2}
    assert score.decision is not None
    assert score.decision.score == 1.4
    assert score.decision.level_probabilities == [0.1, 0.4, 0.5]


def test_verify_requires_statement():
    with pytest.raises(ElfaValidationError):
        _client().verify("")


@respx.mock
def test_verify_is_not_retried():
    route = respx.post(f"{BASE_URL}/v3/verify").mock(
        return_value=httpx.Response(
            503,
            json={"code": "ERR_SERVICE_UNAVAILABLE", "message": "Unavailable"},
        )
    )
    client = V3Client(transport=SyncTransport("k", BASE_URL, retries=3))
    with pytest.raises(ElfaAPIError) as exc:
        client.verify("s")
    assert exc.value.status_code == 503
    assert route.call_count == 1


@respx.mock
def test_verify_403_raises_api_error():
    respx.post(f"{BASE_URL}/v3/verify").mock(
        return_value=httpx.Response(
            403, json={"code": "ERR_FORBIDDEN", "message": "Forbidden"}
        )
    )
    with pytest.raises(ElfaAPIError) as exc:
        _client().verify("s")
    assert exc.value.status_code == 403


@respx.mock
def test_create_monitor_posts_query_and_webhook_url():
    route = respx.post(f"{BASE_URL}/v3/monitors").mock(
        return_value=httpx.Response(201, json=MONITOR)
    )
    result = _client().create_monitor(
        MONITOR["query"], "https://example.com/elfa-webhook"
    )

    assert _body(route) == {
        "query": MONITOR["query"],
        "webhookUrl": "https://example.com/elfa-webhook",
    }
    assert result.id == MONITOR_ID
    assert result.webhook_url == "https://example.com/elfa-webhook"
    assert result.webhook_secret.startswith("whsec_")
    assert result.status == "active"
    assert result.created_at == 1794981600


@respx.mock
def test_get_monitors_sends_no_params_and_parses():
    route = respx.get(f"{BASE_URL}/v3/monitors").mock(
        return_value=httpx.Response(
            200, json={"data": [MONITOR, {**MONITOR, "status": "ended"}], "total": 2}
        )
    )
    result = _client().get_monitors()

    assert _params(route) == {}
    assert result.total == 2
    assert [m.status for m in result.data] == ["active", "ended"]


@respx.mock
def test_get_monitor_hits_its_path():
    route = respx.get(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json=MONITOR)
    )
    result = _client().get_monitor(MONITOR_ID)

    assert route.called
    assert result.webhook_secret == MONITOR["webhookSecret"]


@respx.mock
def test_update_monitor_patches_only_given_fields():
    route = respx.patch(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json={**MONITOR, "updatedAt": 1794990000})
    )
    client = _client()
    client.update_monitor(MONITOR_ID, query="Binance announces it will delist a token")
    assert _body(route) == {"query": "Binance announces it will delist a token"}

    result = client.update_monitor(
        MONITOR_ID, query="q12", webhook_url="https://example.com/new"
    )
    assert _body(route) == {"query": "q12", "webhookUrl": "https://example.com/new"}
    assert result.updated_at == 1794990000


def test_update_monitor_requires_a_field():
    with pytest.raises(ElfaValidationError):
        _client().update_monitor(MONITOR_ID)


@respx.mock
def test_delete_monitor_sends_delete_and_parses():
    route = respx.delete(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json={"id": MONITOR_ID, "deleted": True})
    )
    result = _client().delete_monitor(MONITOR_ID)

    assert route.calls[-1].request.content == b""
    assert result.id == MONITOR_ID
    assert result.deleted is True


@respx.mock
def test_get_monitor_matches_maps_params_and_parses_both_item_kinds():
    route = respx.get(f"{BASE_URL}/v3/monitors/{MONITOR_ID}/events").mock(
        return_value=httpx.Response(200, json={"data": [MATCH], "nextCursor": "c2"})
    )
    result = _client().get_monitor_matches(MONITOR_ID, limit=100, cursor="c1")

    assert _params(route) == {"limit": "100", "cursor": "c1"}
    assert result.next_cursor == "c2"
    match = result.data[0]
    assert match.monitor_id == MONITOR_ID
    assert match.matched_at == 1794985200
    event, web = match.items
    assert event.source == "event"
    assert event.alert_title == "Anthropic releases a new model"
    assert event.cited_sources is not None
    assert event.cited_sources[0].source_record_id is None
    assert event.url is None
    assert web.source == "web"
    assert web.url == "https://www.example.com/news/model"
    assert web.published_day_only is True
    assert web.cited_sources is None


@respx.mock
def test_get_monitor_matches_last_page():
    respx.get(f"{BASE_URL}/v3/monitors/{MONITOR_ID}/events").mock(
        return_value=httpx.Response(200, json={"data": [], "nextCursor": None})
    )
    result = _client().get_monitor_matches(MONITOR_ID)

    assert result.data == []
    assert result.next_cursor is None


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.get_monitor(""),
        lambda c: c.update_monitor("", query="abc"),
        lambda c: c.delete_monitor(""),
        lambda c: c.get_monitor_matches(""),
    ],
)
def test_monitor_methods_require_id(call):
    with pytest.raises(ElfaValidationError):
        call(_client())


@respx.mock
def test_monitor_409_raises_api_error():
    respx.patch(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(
            409, json={"code": "ERR_CONFLICT", "message": "Conflict"}
        )
    )
    with pytest.raises(ElfaAPIError) as exc:
        _client().update_monitor(MONITOR_ID, query="abc")
    assert exc.value.status_code == 409


@respx.mock
async def test_async_verify_and_monitors():
    verify = respx.post(f"{BASE_URL}/v3/verify").mock(
        return_value=httpx.Response(200, json=VERIFY)
    )
    create = respx.post(f"{BASE_URL}/v3/monitors").mock(
        return_value=httpx.Response(201, json=MONITOR)
    )
    respx.get(f"{BASE_URL}/v3/monitors").mock(
        return_value=httpx.Response(200, json={"data": [MONITOR], "total": 1})
    )
    respx.get(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json=MONITOR)
    )
    update = respx.patch(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json=MONITOR)
    )
    respx.delete(f"{BASE_URL}/v3/monitors/{MONITOR_ID}").mock(
        return_value=httpx.Response(200, json={"id": MONITOR_ID, "deleted": True})
    )
    matches = respx.get(f"{BASE_URL}/v3/monitors/{MONITOR_ID}/events").mock(
        return_value=httpx.Response(200, json={"data": [MATCH], "nextCursor": None})
    )
    client = AsyncElfaClient(api_key="k", base_url=BASE_URL, retries=0).v3

    result = await client.verify("s", decision={"type": "yesNo"})
    assert _body(verify) == {"statement": "s", "decision": {"type": "yesNo"}}
    assert result.verdict == "supported"

    created = await client.create_monitor("abc", "https://example.com/h")
    assert _body(create) == {"query": "abc", "webhookUrl": "https://example.com/h"}
    assert created.id == MONITOR_ID
    assert (await client.get_monitors()).total == 1
    assert (await client.get_monitor(MONITOR_ID)).status == "active"
    await client.update_monitor(MONITOR_ID, webhook_url="https://example.com/n")
    assert _body(update) == {"webhookUrl": "https://example.com/n"}
    page = await client.get_monitor_matches(MONITOR_ID, limit=5)
    assert _params(matches) == {"limit": "5"}
    assert len(page.data[0].items) == 2
    assert (await client.delete_monitor(MONITOR_ID)).deleted is True
    await client._transport.close()
