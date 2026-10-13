"""API v3 client: paths, exact query params, parsing, and errors."""

import httpx
import pytest
import respx

from elfa import AsyncElfaClient, AsyncV3Client, ElfaClient, V3Client
from elfa.exceptions import ElfaAPIError, ElfaValidationError
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
    assert exc.value.message == "Invalid parameters"
    assert exc.value.request_id == "req-1"


@respx.mock
def test_v3_403_on_free_key_raises_api_error():
    message = "The v3 API is free on the Pay-as-you-go and Grow plans. Upgrade at x"
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
