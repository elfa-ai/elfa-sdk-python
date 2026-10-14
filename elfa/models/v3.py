"""Models for API v3 (`/v3/*`).

Times are unix seconds. Enum-valued response fields are typed as ``str`` so a
value the API adds later does not fail parsing; the ``Literal`` aliases below
type the request parameters.
"""

from typing import List, Optional

from pydantic import Field
from typing_extensions import Literal

from elfa.models.base import ElfaModel

MarketV3 = Literal["crypto", "equity"]
OrderV3 = Literal["desc", "asc"]
EntityTypeV3 = Literal["token", "equity", "project", "person", "organisation"]
EventClassV3 = Literal["market", "asset", "call"]
EventTypeV3 = Literal[
    "security",
    "listing",
    "regulatory",
    "macro",
    "protocol",
    "company",
    "marketFlow",
    "price",
    "social",
    "other",
]
ImplicationV3 = Literal["bullish", "bearish", "mixed", "unclear"]
NoveltyV3 = Literal["new", "update"]
AlertActionV3 = Literal["alert", "monitor"]
EventSortV3 = Literal["latest", "relevant"]
StorylineStatusV3 = Literal["open", "dormant", "any"]
StorylineRelationV3 = Literal[
    "origin",
    "update",
    "confirmation",
    "contradiction",
    "mitigation",
    "consequence",
    "reaction",
    "context",
]
ArcStatusV3 = Literal["active", "retired"]
ArcSortV3 = Literal["latest", "storylines", "events"]
MindsharePeriodV3 = Literal["1h", "4h", "24h", "7d"]
CallStatusV3 = Literal["open", "closed"]
CallDirectionV3 = Literal["long", "short"]
AccountMetricV3 = Literal["standing", "alphaScore", "hitRate", "avgReturn"]


class ExternalIdsV3(ElfaModel):
    coingecko_id: Optional[str] = Field(None, alias="coingeckoId")
    figi: Optional[str] = None
    cik: Optional[str] = None


class EntityMatchV3(ElfaModel):
    id: str
    entity_type: str = Field(alias="entityType")
    name: Optional[str] = None
    symbol: Optional[str] = None
    handle: Optional[str] = None
    matched_on: str = Field(alias="matchedOn")
    score: float
    external_ids: ExternalIdsV3 = Field(alias="externalIds")


class EntitiesResponseV3(ElfaModel):
    entities: List[EntityMatchV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class EventEntityV3(ElfaModel):
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    entity_type: str = Field(alias="entityType")


class EventImpactV3(ElfaModel):
    entity_id: str = Field(alias="entityId")
    symbol: str
    price_change_1d: Optional[float] = Field(None, alias="priceChange1d")
    moved_first: Optional[bool] = Field(None, alias="movedFirst")
    market_wide: Optional[bool] = Field(None, alias="marketWide")
    final: bool


class EventCitedSourceV3(ElfaModel):
    source: str
    source_record_id: str = Field(alias="sourceRecordId")
    handle: Optional[str] = None
    link: Optional[str] = None


class EventPositionsV3(ElfaModel):
    long: int
    short: int
    side: Optional[str] = None


class EventV3(ElfaModel):
    id: str
    event_class: str = Field(alias="eventClass")
    alert_title: Optional[str] = Field(None, alias="alertTitle")
    summary: Optional[str] = None
    implication: Optional[str] = None
    event_type: Optional[str] = Field(None, alias="eventType")
    primary_entities: List[EventEntityV3] = Field(alias="primaryEntities")
    related_entities: List[EventEntityV3] = Field(alias="relatedEntities")
    alert_action: Optional[str] = Field(None, alias="alertAction")
    origin_count: int = Field(alias="originCount")
    impacts: List[EventImpactV3]
    analyzed_at: int = Field(alias="analyzedAt")
    novelty: str
    first_seen_at: Optional[int] = Field(None, alias="firstSeenAt")
    storyline_id: Optional[str] = Field(None, alias="storylineId")
    cited_sources: List[EventCitedSourceV3] = Field(alias="citedSources")
    positions: Optional[EventPositionsV3] = None


class EventsResponseV3(ElfaModel):
    events: List[EventV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class StorylineEventV3(ElfaModel):
    event_id: str = Field(alias="eventId")
    relation: str
    material: bool
    occurred_at: int = Field(alias="occurredAt")


class StorylineV3(ElfaModel):
    id: str
    title: str
    summary: str
    status: str
    entities: List[EventEntityV3]
    started_at: int = Field(alias="startedAt")
    last_event_at: int = Field(alias="lastEventAt")
    last_material_at: int = Field(alias="lastMaterialAt")
    arc_id: Optional[str] = Field(None, alias="arcId")
    events: List[StorylineEventV3]


class StorylinesResponseV3(ElfaModel):
    storylines: List[StorylineV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class ArcV3(ElfaModel):
    id: str
    name: str
    summary: Optional[str] = None
    status: str
    storyline_ids: List[str] = Field(alias="storylineIds")
    updated_at: int = Field(alias="updatedAt")


class ArcsResponseV3(ElfaModel):
    arcs: List[ArcV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class CallBookBarV3(ElfaModel):
    bar_at: int = Field(alias="barAt")
    live: bool
    long_share: float = Field(alias="longShare")
    short_share: float = Field(alias="shortShare")
    crowding_percentile: Optional[float] = Field(None, alias="crowdingPercentile")
    account_count: int = Field(alias="accountCount")
    pulse24: Optional[float] = None
    pulse24_long_share: Optional[float] = Field(None, alias="pulse24LongShare")
    pulse6: Optional[float] = None
    pulse6_long_share: Optional[float] = Field(None, alias="pulse6LongShare")
    formula_version: str = Field(alias="formulaVersion")
    computed_at: int = Field(alias="computedAt")


class CallBookResponseV3(ElfaModel):
    bars: List[CallBookBarV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class MindshareAssetV3(ElfaModel):
    rank: int
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    share: float
    change_pct: Optional[float] = Field(None, alias="changePct")
    hot: Optional[bool] = None
    share_1h: float = Field(alias="share1h")
    share_4h: float = Field(alias="share4h")
    ratio_1h_4h: Optional[float] = Field(None, alias="ratio1h4h")
    capped_1h: int = Field(alias="capped1h")


class MindshareResponseV3(ElfaModel):
    assets: List[MindshareAssetV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class TrendingContractAssetV3(ElfaModel):
    symbol: str
    name: str
    id: str
    chains: List[str]


class TrendingContractV3(ElfaModel):
    rank: int
    contract_address: str = Field(alias="contractAddress")
    mention_count: int = Field(alias="mentionCount")
    asset: Optional[TrendingContractAssetV3] = None


class TrendingContractsResponseV3(ElfaModel):
    contracts: List[TrendingContractV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class CallAssetV3(ElfaModel):
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    entity_type: str = Field(alias="entityType")


class CallV3(ElfaModel):
    id: str
    episode_id: str = Field(alias="episodeId")
    handle: Optional[str] = None
    source: Optional[str] = None
    channel: Optional[str] = None
    asset: Optional[CallAssetV3] = None
    call_action: str = Field(alias="callAction")
    setup: Optional[str] = None
    thesis: Optional[str] = None
    source_record_id: str = Field(alias="sourceRecordId")
    occurred_at: int = Field(alias="occurredAt")


class CallsResponseV3(ElfaModel):
    calls: List[CallV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class CallerTrackV3(ElfaModel):
    alpha_score: Optional[float] = Field(None, alias="alphaScore")
    hit_rate: Optional[float] = Field(None, alias="hitRate")
    avg_return: Optional[float] = Field(None, alias="avgReturn")
    scored_episodes: int = Field(alias="scoredEpisodes")
    total_episodes: int = Field(alias="totalEpisodes")


class EpisodeCallV3(ElfaModel):
    call_id: str = Field(alias="callId")
    call_action: str = Field(alias="callAction")
    occurred_at: int = Field(alias="occurredAt")


class CallEpisodeV3(ElfaModel):
    id: str
    handle: Optional[str] = None
    source: Optional[str] = None
    channel: Optional[str] = None
    asset: Optional[CallAssetV3] = None
    direction: str
    horizon: str
    status: str
    opened_at: int = Field(alias="openedAt")
    closed_at: Optional[int] = Field(None, alias="closedAt")
    observed_at: int = Field(alias="observedAt")
    entry_price: Optional[float] = Field(None, alias="entryPrice")
    exit_price: Optional[float] = Field(None, alias="exitPrice")
    close_reason: Optional[str] = Field(None, alias="closeReason")
    setup: Optional[str] = None
    thesis: Optional[str] = None
    stated_target: Optional[float] = Field(None, alias="statedTarget")
    stated_stop: Optional[float] = Field(None, alias="statedStop")
    track: Optional[CallerTrackV3] = None
    calls: List[EpisodeCallV3]


class CallEpisodesResponseV3(ElfaModel):
    episodes: List[CallEpisodeV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")
    served_from: Optional[int] = Field(None, alias="servedFrom")


class PositioningResponseV3(ElfaModel):
    id: str
    symbol: Optional[str] = None
    name: Optional[str] = None
    open_long: int = Field(alias="openLong")
    open_short: int = Field(alias="openShort")
    as_of: int = Field(alias="asOf")


class TopAccountV3(ElfaModel):
    rank: int
    handle: str
    name: Optional[str] = None
    follower_count: Optional[int] = Field(None, alias="followerCount")
    verified: bool
    standing: float
    track: Optional[CallerTrackV3] = None


class TopAccountsResponseV3(ElfaModel):
    accounts: List[TopAccountV3]
    next_cursor: Optional[str] = Field(None, alias="nextCursor")
    has_more: bool = Field(alias="hasMore")


class KeyStatusCreditsV3(ElfaModel):
    limit: Optional[float] = None
    used: float
    remaining: float
    resets_at: Optional[int] = Field(None, alias="resetsAt")
    requests_per_minute: int = Field(alias="requestsPerMinute")


class KeyStatusV3(ElfaModel):
    plan: str
    billing_mode: str = Field(alias="billingMode")
    owner: str
    scopes: List[str]
    credits: KeyStatusCreditsV3
    history_from: int = Field(alias="historyFrom")
