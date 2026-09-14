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
    CategoryRuleRead,
    CategoryRuleWrite,
    ClassificationApplyRequest,
    ClassificationPreviewRead,
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
    apply_classification,
    classification_preview,
    create_category_rule,
    create_taxonomy,
    create_tool,
    delete_category,
    delete_category_rule,
    delete_tag,
    list_category_rules,
    list_taxonomy,
    rename_category,
    rename_tag,
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


@router.patch("/categories/{category_id}", response_model=TaxonomyRead)
def edit_category(category_id: int, payload: TaxonomyWrite, session: SessionDependency) -> TaxonomyRead:
    return rename_category(session, category_id, payload.name)


@router.delete("/categories/{category_id}", status_code=204)
def remove_category(category_id: int, session: SessionDependency) -> None:
    delete_category(session, category_id)


@router.get("/category-rules", response_model=list[CategoryRuleRead])
def category_rules(session: SessionDependency) -> list[CategoryRuleRead]:
    return list_category_rules(session)


@router.post("/category-rules", response_model=CategoryRuleRead, status_code=201)
def add_category_rule(payload: CategoryRuleWrite, session: SessionDependency) -> CategoryRuleRead:
    return create_category_rule(session, payload.category_id, payload.tag_name)


@router.delete("/category-rules/{rule_id}", status_code=204)
def remove_category_rule(rule_id: int, session: SessionDependency) -> None:
    delete_category_rule(session, rule_id)


@router.get("/classification-preview", response_model=list[ClassificationPreviewRead])
def get_classification_preview(session: SessionDependency) -> list[ClassificationPreviewRead]:
    return classification_preview(session)


@router.post("/classify", response_model=list[ToolRead])
def classify_tools(payload: ClassificationApplyRequest, session: SessionDependency) -> list[ToolRead]:
    return apply_classification(session, payload)


@router.get("/tags", response_model=list[TaxonomyRead])
def tags(session: SessionDependency) -> list[TaxonomyRead]:
    return list_taxonomy(session, Tag)


@router.post("/tags", response_model=TaxonomyRead, status_code=201)
def add_tag(payload: TaxonomyWrite, session: SessionDependency) -> TaxonomyRead:
    return create_taxonomy(session, Tag, payload.name)


@router.patch("/tags/{tag_id}", response_model=TaxonomyRead)
def edit_tag(tag_id: int, payload: TaxonomyWrite, session: SessionDependency) -> TaxonomyRead:
    return rename_tag(session, tag_id, payload.name)


@router.delete("/tags/{tag_id}", status_code=204)
def remove_tag(tag_id: int, session: SessionDependency) -> None:
    delete_tag(session, tag_id)
