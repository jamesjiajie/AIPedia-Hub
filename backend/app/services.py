from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import HTTPException, status
from sqlalchemy import Select, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Category, Tag, Tool
from app.schemas import TaxonomyRead, ToolListResponse, ToolPatch, ToolRead, ToolStatus, ToolWrite

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_NAMES = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def normalize_url(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="URL must be a valid http(s) address.")
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    port = f":{parsed.port}" if parsed.port and parsed.port not in {80, 443} else ""
    netloc = f"{hostname}{port}"
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, item)
            for key, item in parse_qsl(parsed.query, keep_blank_values=True)
            if not key.lower().startswith(TRACKING_QUERY_PREFIXES)
            and key.lower() not in TRACKING_QUERY_NAMES
        )
    )
    return urlunsplit((parsed.scheme.lower(), netloc, path, query, ""))


def json_list(value: str) -> list[str]:
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def normalized_names(values: list[str]) -> list[str]:
    unique: dict[str, str] = {}
    for value in values:
        clean = value.strip()
        if clean:
            unique.setdefault(clean.casefold(), clean)
    return list(unique.values())


def slugify(value: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if ascii_slug:
        return ascii_slug[:100]
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]
    return f"item-{digest}"


def unique_slug(
    session: Session, model: type[Tool] | type[Tag] | type[Category], value: str
) -> str:
    base = slugify(value)
    candidate = base
    suffix = 2
    while session.scalar(select(model.id).where(model.slug == candidate)) is not None:
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def get_or_create_category(session: Session, value: str | None) -> Category | None:
    if not value or not value.strip():
        return None
    clean = value.strip()
    existing = session.scalar(select(Category).where(func.lower(Category.name) == clean.casefold()))
    if existing:
        return existing
    category = Category(name=clean, slug=unique_slug(session, Category, clean))
    session.add(category)
    session.flush()
    return category


def get_or_create_tags(session: Session, values: list[str]) -> list[Tag]:
    tags: list[Tag] = []
    for name in normalized_names(values):
        tag = session.scalar(select(Tag).where(func.lower(Tag.name) == name.casefold()))
        if tag is None:
            tag = Tag(name=name, slug=unique_slug(session, Tag, name))
            session.add(tag)
            session.flush()
        tags.append(tag)
    return tags


def apply_tool_write(session: Session, tool: Tool, payload: ToolWrite | ToolPatch) -> Tool:
    canonical_url = normalize_url(payload.official_url)
    if canonical_url:
        duplicate = session.scalar(
            select(Tool).where(Tool.canonical_url == canonical_url, Tool.id != tool.id)
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "A tool with this URL already exists.",
                    "existing_tool_id": duplicate.id,
                },
            )

    tool.name = payload.name.strip()
    tool.aliases = json.dumps(normalized_names(payload.aliases), ensure_ascii=False)
    tool.official_url = normalize_url(payload.official_url)
    tool.canonical_url = canonical_url
    tool.source_url = normalize_url(payload.source_url)
    tool.summary = payload.summary or None
    tool.why_saved = payload.why_saved or None
    tool.use_cases = payload.use_cases or None
    tool.notes = payload.notes or None
    tool.category = get_or_create_category(session, payload.category)
    tool.tags = get_or_create_tags(session, payload.tags)
    tool.pricing_model = payload.pricing_model.value
    tool.platforms = json.dumps(normalized_names(payload.platforms), ensure_ascii=False)
    tool.is_favorite = payload.is_favorite
    tool.status = payload.status.value
    return tool


def to_tool_read(tool: Tool) -> ToolRead:
    return ToolRead(
        id=tool.id,
        name=tool.name,
        slug=tool.slug,
        aliases=json_list(tool.aliases),
        official_url=tool.official_url,
        canonical_url=tool.canonical_url,
        source_url=tool.source_url,
        summary=tool.summary,
        why_saved=tool.why_saved,
        use_cases=tool.use_cases,
        notes=tool.notes,
        category=tool.category.name if tool.category else None,
        tags=[tag.name for tag in tool.tags],
        pricing_model=tool.pricing_model,
        platforms=json_list(tool.platforms),
        is_favorite=tool.is_favorite,
        status=tool.status,
        created_at=tool.created_at,
        updated_at=tool.updated_at,
        last_viewed_at=tool.last_viewed_at,
    )


def get_tool_or_404(session: Session, tool_id: int) -> Tool:
    tool = session.scalar(
        select(Tool)
        .options(selectinload(Tool.category), selectinload(Tool.tags))
        .where(Tool.id == tool_id)
    )
    if tool is None:
        raise HTTPException(status_code=404, detail="Tool not found.")
    return tool


def create_tool(session: Session, payload: ToolWrite) -> ToolRead:
    tool = Tool(slug=unique_slug(session, Tool, payload.name))
    session.add(tool)
    apply_tool_write(session, tool, payload)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Tool could not be saved due to a duplicate value."
        ) from error
    return to_tool_read(get_tool_or_404(session, tool.id))


def update_tool(session: Session, tool_id: int, payload: ToolPatch) -> ToolRead:
    tool = get_tool_or_404(session, tool_id)
    apply_tool_write(session, tool, payload)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Tool could not be updated due to a duplicate value."
        ) from error
    return to_tool_read(get_tool_or_404(session, tool_id))


def view_tool(session: Session, tool_id: int) -> ToolRead:
    tool = get_tool_or_404(session, tool_id)
    tool.last_viewed_at = datetime.now(UTC)
    session.commit()
    return to_tool_read(tool)


def set_tool_status(session: Session, tool_id: int, value: ToolStatus) -> ToolRead:
    tool = get_tool_or_404(session, tool_id)
    tool.status = value.value
    session.commit()
    return to_tool_read(tool)


def search_tools(
    session: Session,
    *,
    q: str | None,
    category: str | None,
    tags: list[str],
    pricing_model: str | None,
    is_favorite: bool | None,
    status_value: ToolStatus,
    sort: Literal["updated_desc", "created_desc", "viewed_desc", "name_asc"],
    page: int,
    page_size: int,
) -> ToolListResponse:
    query: Select[tuple[Tool]] = select(Tool).options(
        selectinload(Tool.category), selectinload(Tool.tags)
    )
    query = query.where(Tool.status == status_value.value)
    if category:
        query = query.join(Tool.category).where(Category.slug == slugify(category))
    if pricing_model:
        query = query.where(Tool.pricing_model == pricing_model)
    if is_favorite is not None:
        query = query.where(Tool.is_favorite == is_favorite)
    for tag in normalized_names(tags):
        query = query.where(Tool.tags.any(Tag.slug == slugify(tag)))

    if q and q.strip():
        needle = q.strip()
        pattern = f"%{needle}%"
        fts_ids: list[int] = []
        if len(needle) >= 3:
            fts_ids = list(
                session.scalars(
                    text(
                        "SELECT rowid FROM tools_fts WHERE tools_fts MATCH :query ORDER BY bm25(tools_fts)"
                    ).bindparams(query=needle)
                )
            )
        text_match = or_(
            Tool.name.ilike(pattern),
            Tool.aliases.ilike(pattern),
            Tool.summary.ilike(pattern),
            Tool.why_saved.ilike(pattern),
            Tool.use_cases.ilike(pattern),
            Tool.notes.ilike(pattern),
            Tool.category.has(Category.name.ilike(pattern)),
            Tool.tags.any(Tag.name.ilike(pattern)),
        )
        query = query.where(or_(Tool.id.in_(fts_ids), text_match))

    if sort == "name_asc":
        query = query.order_by(Tool.name.asc())
    elif sort == "created_desc":
        query = query.order_by(Tool.created_at.desc())
    elif sort == "viewed_desc":
        query = query.order_by(Tool.last_viewed_at.desc().nullslast(), Tool.updated_at.desc())
    else:
        query = query.order_by(Tool.updated_at.desc())

    tools = list(session.scalars(query).unique())
    if q and q.strip():
        normalized_query = q.strip().casefold()
        tools.sort(
            key=lambda tool: (
                0 if tool.name.casefold() == normalized_query else 1,
                0 if tool.name.casefold().startswith(normalized_query) else 1,
            )
        )
    total = len(tools)
    start = (page - 1) * page_size
    return ToolListResponse(
        items=[to_tool_read(tool) for tool in tools[start : start + page_size]],
        page=page,
        page_size=page_size,
        total=total,
    )


def list_taxonomy(session: Session, model: type[Category] | type[Tag]) -> list[TaxonomyRead]:
    items = list(session.scalars(select(model).order_by(model.name.asc())))
    return [
        TaxonomyRead(id=item.id, name=item.name, slug=item.slug, usage_count=len(item.tools))
        for item in items
    ]


def create_taxonomy(session: Session, model: type[Category] | type[Tag], name: str) -> TaxonomyRead:
    clean = name.strip()
    existing = session.scalar(select(model).where(func.lower(model.name) == clean.casefold()))
    if existing:
        return TaxonomyRead(
            id=existing.id, name=existing.name, slug=existing.slug, usage_count=len(existing.tools)
        )
    item = model(name=clean, slug=unique_slug(session, model, clean))
    session.add(item)
    session.commit()
    return TaxonomyRead(id=item.id, name=item.name, slug=item.slug, usage_count=0)
