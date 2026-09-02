from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crawl_jobs import crawl_jobs
from app.db import get_session
from app.llm import LLMProvider, get_llm_provider
from app.models import Category, Tag
from app.schemas import (
    CandidateAssessmentRead,
    CandidateAssessmentRequest,
    CrawlJobRead,
    CrawlRequest,
    HealthRead,
    TaxonomyRead,
    TaxonomyWrite,
    ToolDraftRead,
    ToolDraftRequest,
    ToolListResponse,
    ToolPatch,
    ToolRead,
    ToolStatus,
    ToolWrite,
)
from app.services import (
    create_taxonomy,
    create_tool,
    list_taxonomy,
    search_tools,
    set_tool_status,
    update_tool,
    view_tool,
)

router = APIRouter(prefix="/api")
SessionDependency = Annotated[Session, Depends(get_session)]
LLMDependency = Annotated[LLMProvider, Depends(get_llm_provider)]


@router.get("/health", response_model=HealthRead)
def health() -> HealthRead:
    return HealthRead(status="ok", database="ready")


@router.post("/discovery/assess", response_model=CandidateAssessmentRead)
def assess_candidate(payload: CandidateAssessmentRequest, provider: LLMDependency) -> CandidateAssessmentRead:
    return provider.assess_candidate(payload)


@router.post("/discovery/draft", response_model=ToolDraftRead)
def build_tool_draft(payload: ToolDraftRequest, provider: LLMDependency) -> ToolDraftRead:
    return provider.build_tool_draft(payload)


@router.post("/discovery/crawl", response_model=CrawlJobRead, status_code=202)
def start_crawl(payload: CrawlRequest, provider: LLMDependency) -> CrawlJobRead:
    return crawl_jobs.start(payload, provider)


@router.get("/discovery/crawl/{job_id}", response_model=CrawlJobRead)
def get_crawl(job_id: str) -> CrawlJobRead:
    return crawl_jobs.get(job_id)


@router.get("/tools", response_model=ToolListResponse)
def list_tools(
    session: SessionDependency,
    q: str | None = None,
    category: str | None = None,
    tag: Annotated[list[str], Query()] = [],
    pricing_model: str | None = None,
    is_favorite: bool | None = None,
    status: ToolStatus = ToolStatus.ACTIVE,
    sort: Literal["updated_desc", "created_desc", "viewed_desc", "name_asc"] = "updated_desc",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> ToolListResponse:
    return search_tools(
        session,
        q=q,
        category=category,
        tags=tag,
        pricing_model=pricing_model,
        is_favorite=is_favorite,
        status_value=status,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.post("/tools", response_model=ToolRead, status_code=201)
def add_tool(payload: ToolWrite, session: SessionDependency) -> ToolRead:
    return create_tool(session, payload)


@router.get("/tools/{tool_id}", response_model=ToolRead)
def get_tool(tool_id: int, session: SessionDependency) -> ToolRead:
    return view_tool(session, tool_id)


@router.patch("/tools/{tool_id}", response_model=ToolRead)
def edit_tool(tool_id: int, payload: ToolPatch, session: SessionDependency) -> ToolRead:
    return update_tool(session, tool_id, payload)


@router.post("/tools/{tool_id}/archive", response_model=ToolRead)
def archive_tool(tool_id: int, session: SessionDependency) -> ToolRead:
    return set_tool_status(session, tool_id, ToolStatus.ARCHIVED)


@router.post("/tools/{tool_id}/restore", response_model=ToolRead)
def restore_tool(tool_id: int, session: SessionDependency) -> ToolRead:
    return set_tool_status(session, tool_id, ToolStatus.ACTIVE)


@router.get("/categories", response_model=list[TaxonomyRead])
def categories(session: SessionDependency) -> list[TaxonomyRead]:
    return list_taxonomy(session, Category)


@router.post("/categories", response_model=TaxonomyRead, status_code=201)
def add_category(payload: TaxonomyWrite, session: SessionDependency) -> TaxonomyRead:
    return create_taxonomy(session, Category, payload.name)


@router.get("/tags", response_model=list[TaxonomyRead])
def tags(session: SessionDependency) -> list[TaxonomyRead]:
    return list_taxonomy(session, Tag)


@router.post("/tags", response_model=TaxonomyRead, status_code=201)
def add_tag(payload: TaxonomyWrite, session: SessionDependency) -> TaxonomyRead:
    return create_taxonomy(session, Tag, payload.name)
