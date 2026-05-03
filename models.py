from dataclasses import dataclass, field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


@dataclass
class VoiceProfile:
    tone: str
    allowed_vocab: List[str]
    taboos: List[str]
    formality: str
    language_preference: str


@dataclass
class OfferTemplate:
    service: str
    price_range: str
    typical_duration: Optional[str] = None


@dataclass
class PeerStats:
    avg_rating: float
    avg_reviews: int
    avg_ctr: float
    locality: str


@dataclass
class DigestItem:
    title: str
    source: str
    summary: str
    relevance: str
    published_date: str


@dataclass
class SeasonalBeat:
    months: str
    pattern: str
    opportunity: str


@dataclass
class CategoryContext:
    slug: str
    offer_catalog: List[OfferTemplate]
    voice: VoiceProfile
    peer_stats: PeerStats
    digest: List[DigestItem]
    seasonal_beats: List[SeasonalBeat]


@dataclass
class Identity:
    name: str
    owner_name: Optional[str]
    place_id: str
    locality: str
    city: str
    verified: bool
    languages: List[str]


@dataclass
class Subscription:
    status: str
    days_remaining: int
    plan: str


@dataclass
class PerformanceSnapshot:
    views_30d: int
    calls_30d: int
    directions_30d: int
    ctr_30d: float
    views_7d_delta: float
    calls_7d_delta: float


@dataclass
class MerchantOffer:
    service: str
    price: str
    status: str
    created_date: str
    expiry_date: Optional[str] = None


@dataclass
class ConversationHistory:
    turns: List[Dict[str, Any]]
    last_merchant_reply: Optional[str]
    last_vera_message: Optional[str]
    engagement_score: float


@dataclass
class CustomerAggregate:
    total_customers: int
    active_customers: int
    lapsed_customers: int
    retention_rate: float
    segments: Dict[str, int]


@dataclass
class DerivedSignal:
    signal_type: str
    value: Any
    detected_at: str


@dataclass
class MerchantContext:
    merchant_id: str
    identity: Identity
    subscription: Subscription
    performance: PerformanceSnapshot
    offers: List[MerchantOffer]
    conversation_history: ConversationHistory
    customer_aggregate: CustomerAggregate
    signals: List[DerivedSignal]


@dataclass
class TriggerContext:
    id: str
    scope: Literal["merchant", "customer"]
    kind: str
    source: Literal["external", "internal"]
    payload: Dict[str, Any]
    urgency: int
    suppression_key: str
    expires_at: str


@dataclass
class CustomerIdentity:
    name: str
    phone: str
    language_pref: str


@dataclass
class Relationship:
    first_visit: str
    last_visit: str
    visits_total: int
    services_received: List[str]


@dataclass
class CustomerContext:
    customer_id: str
    merchant_id: str
    identity: CustomerIdentity
    relationship: Relationship
    state: Literal["new", "active", "lapsed_soft", "lapsed_hard", "churned"]
    preferences: Dict[str, Any]
    consent: Dict[str, Any]


class ComposedMessage(BaseModel):
    body: str = Field(..., description="WhatsApp message text")
    cta: Literal["YES/STOP", "open_ended", "none"] = Field(..., description="Call-to-action type")
    send_as: Literal["vera", "merchant_on_behalf"] = Field(..., description="Sender role")
    suppression_key: str = Field(..., description="Deduplication key")
    rationale: str = Field(..., description="Message rationale")
    conversation_id: Optional[str] = None
    merchant_id: Optional[str] = None
    customer_id: Optional[str] = None
    trigger_id: Optional[str] = None
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None


class ContextUpdate(BaseModel):
    scope: Literal["category", "merchant", "customer", "trigger"]
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: str


class TickRequest(BaseModel):
    now: str
    available_triggers: List[str]


class TickResponse(BaseModel):
    actions: List[ComposedMessage]


class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: str
    from_role: Literal["merchant", "customer"]
    message: str
    received_at: str
    turn_number: int


class ReplyResponse(BaseModel):
    action: Literal["send", "wait", "end"]
    body: Optional[str] = None
    cta: Optional[str] = None
    rationale: str
    wait_seconds: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    uptime_seconds: int
    contexts_loaded: Dict[str, int]


class MetadataResponse(BaseModel):
    team_name: str
    model: str
    approach: str
    version: str
