from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import get_llm_provider
from app.crawler import CrawlError, _ensure_public_http_url, github_repository_targets
from app.llm import AgnesProvider
from app.main import app
from app.schemas import (
    CandidateAssessmentRead,
    DiscoverySource,
    ToolDraftRead,
    ToolDraftRequest,
    ToolWrite,
)


class FakeLLMProvider:
    def assess_candidate(self, _request):
        return CandidateAssessmentRead(
            candidate_id="official",
            decision="match",
            confidence=0.98,
            reasons=["Official domain matches."],
        )

    def build_tool_draft(self, _request):
        return ToolDraftRead(
            tool=ToolWrite(
                name="Archify",
                official_url="https://archify.example.com",
                source_url="https://archify.example.com",
                summary="An architecture discovery tool.",
                category="Developer tools",
                tags=["architecture"],
                platforms=["Web"],
            ),
            field_evidence=[
                {
                    "field": "summary",
                    "source_url": "https://archify.example.com",
                    "quote": "Architecture discovery.",
                    "confidence": "confirmed",
                }
            ],
        )


def test_crawler_blocks_direct_private_address_but_allows_proxy_mapped_public_hostname(monkeypatch) -> None:
    with pytest.raises(CrawlError, match="不允许抓取"):
        _ensure_public_http_url("http://127.0.0.1:8001/api/health")

    monkeypatch.setattr(
        "app.crawler.socket.getaddrinfo",
        lambda *_args, **_kwargs: [(None, None, None, None, ("198.18.1.43", 0))],
    )
    _ensure_public_http_url("https://github.com/tt-a1i/archify")


def test_llm_parser_extracts_json_after_model_preamble() -> None:
    result = AgnesProvider._validate(
        '思考内容…\n{"candidate_id":"official","decision":"match","confidence":0.9,"reasons":[]}',
        CandidateAssessmentRead,
    )
    assert result.candidate_id == "official"


def test_fallback_draft_keeps_process_status_out_of_tool_summary() -> None:
    draft = AgnesProvider._fallback_draft(
        ToolDraftRequest(
            tool_name="Archify",
            sources=[DiscoverySource(url="https://github.com/tt-a1i/archify", source_type="official", excerpt="x")],
        )
    )
    assert draft.tool.summary is None
    assert draft.tool.official_url == "https://github.com/tt-a1i/archify"


def test_github_repository_targets_prioritize_readme_documents() -> None:
    targets = github_repository_targets("https://github.com/tt-a1i/archify/issues/10")
    assert targets is not None
    assert targets[0].url == "https://raw.githubusercontent.com/tt-a1i/archify/main/README.md"
    assert targets[0].source_type == "github_readme"
    assert any(target.source_type == "github_product" for target in targets)


def test_fallback_draft_keeps_research_summary_for_review() -> None:
    draft = AgnesProvider._fallback_draft(
        ToolDraftRequest(
            tool_name="Archify",
            official_url="https://github.com/tt-a1i/archify",
            sources=[DiscoverySource(url="https://raw.githubusercontent.com/tt-a1i/archify/main/README.md", source_type="github_readme", excerpt="x")],
        ),
        "一句话定位：将自然语言描述转成可交互技术架构图的 AI Agent Skill。\n\n## 核心功能\n- 五种图表类型 [SRC 1]",
    )
    assert draft.tool.summary == "将自然语言描述转成可交互技术架构图的 AI Agent Skill。"
    assert draft.research_summary is not None


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ready"}


def test_create_search_and_archive_tool() -> None:
    suffix = uuid4().hex[:8]
    with TestClient(app) as client:
        create_response = client.post(
            "/api/tools",
            json={
                "name": f"Archify {suffix}",
                "official_url": f"https://example.com/archify-{suffix}?utm_source=test",
                "why_saved": "Useful when evaluating architecture discovery tools.",
                "use_cases": "Review an unfamiliar codebase.",
                "category": "Developer tools",
                "tags": ["codebase", "architecture"],
                "is_favorite": True,
            },
        )
        assert create_response.status_code == 201
        tool = create_response.json()
        assert tool["canonical_url"] == f"https://example.com/archify-{suffix}"

        search_response = client.get("/api/tools", params={"q": "architecture"})
        assert search_response.status_code == 200
        assert search_response.json()["total"] >= 1

        archive_response = client.post(f"/api/tools/{tool['id']}/archive")
        assert archive_response.status_code == 200
        assert archive_response.json()["status"] == "archived"


def test_discovery_endpoints_use_server_side_provider() -> None:
    app.dependency_overrides[get_llm_provider] = FakeLLMProvider
    try:
        with TestClient(app) as client:
            assess_response = client.post(
                "/api/discovery/assess",
                json={
                    "tool_name": "Archify",
                    "candidates": [{"id": "official", "name": "Archify", "url": "https://archify.example.com"}],
                },
            )
            assert assess_response.status_code == 200
            assert assess_response.json()["decision"] == "match"

            draft_response = client.post(
                "/api/discovery/draft",
                json={
                    "tool_name": "Archify",
                    "sources": [
                        {
                            "url": "https://archify.example.com",
                            "source_type": "official",
                            "excerpt": "Archify is an architecture discovery tool.",
                        }
                    ],
                },
            )
            assert draft_response.status_code == 200
            assert draft_response.json()["tool"]["why_saved"] is None
    finally:
        app.dependency_overrides.clear()
