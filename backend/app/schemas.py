from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PricingModel(StrEnum):
    UNKNOWN = "unknown"
    FREE = "free"
    FREEMIUM = "freemium"
    PAID = "paid"
    OPEN_SOURCE = "open_source"


class ToolStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    UNAVAILABLE = "unavailable"


class ToolWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    aliases: list[str] = Field(default_factory=list)
    official_url: str | None = None
    source_url: str | None = None
    summary: str | None = None
    why_saved: str | None = None
    use_cases: str | None = None
    notes: str | None = None
    category: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    pricing_model: PricingModel = PricingModel.UNKNOWN
    platforms: list[str] = Field(default_factory=list)
    is_favorite: bool = False
    status: ToolStatus = ToolStatus.ACTIVE

    @model_validator(mode="after")
    def requires_recall_context(self) -> ToolWrite:
        if not any((self.official_url, self.summary, self.why_saved)):
            raise ValueError("Provide an official URL, summary, or why_saved note.")
        return self


class ToolPatch(ToolWrite):
    pass


class ToolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    aliases: list[str]
    official_url: str | None
    canonical_url: str | None
    source_url: str | None
    summary: str | None
    why_saved: str | None
    use_cases: str | None
    notes: str | None
    category: str | None
    tags: list[str]
    pricing_model: PricingModel
    platforms: list[str]
    is_favorite: bool
    status: ToolStatus
    created_at: datetime
    updated_at: datetime
    last_viewed_at: datetime | None


class ToolListResponse(BaseModel):
    items: list[ToolRead]
    page: int
    page_size: int
    total: int


class TaxonomyWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)


class TaxonomyRead(BaseModel):
    id: int
    name: str
    slug: str
    usage_count: int


class HealthRead(BaseModel):
    status: str
    database: str


class DiscoverySource(BaseModel):
    """A pre-filtered source excerpt. Webpage instructions are always untrusted data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    url: str = Field(min_length=1, max_length=2_048)
    title: str | None = Field(default=None, max_length=500)
    source_type: str = Field(default="other", max_length=50)
    excerpt: str = Field(min_length=1, max_length=12_000)


class CandidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    url: str | None = Field(default=None, max_length=2_048)
    title: str | None = Field(default=None, max_length=500)
    snippet: str | None = Field(default=None, max_length=3_000)
    source_type: str = Field(default="other", max_length=50)


class CandidateAssessmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tool_name: str = Field(min_length=1, max_length=255)
    user_hint: str | None = Field(default=None, max_length=2_000)
    candidates: list[CandidateInput] = Field(min_length=1, max_length=8)


class CandidateAssessmentRead(BaseModel):
    candidate_id: str
    decision: str
    confidence: float = Field(ge=0, le=1)
    reasons: list[str] = Field(default_factory=list)
    needed_clue: str | None = None


class ToolDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tool_name: str = Field(min_length=1, max_length=255)
    user_hint: str | None = Field(default=None, max_length=2_000)
    official_url: str | None = Field(default=None, max_length=2_048)
    sources: list[DiscoverySource] = Field(min_length=1, max_length=8)


class FieldEvidence(BaseModel):
    field: str
    source_url: str
    quote: str | None = None
    confidence: str = "unconfirmed"


class ToolDraftRead(BaseModel):
    tool: ToolWrite
    field_evidence: list[FieldEvidence] = Field(default_factory=list)
    unsupported_fields: list[str] = Field(default_factory=list)
    review_needed: bool = True
    research_summary: str | None = None


class CrawlRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    tool_name: str = Field(min_length=1, max_length=255)
    official_url: str | None = Field(default=None, max_length=2_048)
    source_url: str | None = Field(default=None, max_length=2_048)
    user_hint: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def requires_crawl_url(self) -> CrawlRequest:
        if not self.official_url and not self.source_url:
            raise ValueError("Provide an official_url or source_url to crawl.")
        return self


class CrawlEvent(BaseModel):
    at: datetime
    level: str
    message: str


class CrawlJobRead(BaseModel):
    job_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    draft: ToolDraftRead | None = None
    error: str | None = None
    events: list[CrawlEvent] = Field(default_factory=list)
