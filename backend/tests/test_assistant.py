from uuid import uuid4

from fastapi.testclient import TestClient

from app.api import get_llm_provider
from app.db import SessionLocal
from app.main import app
from app.models import Tool
from app.schemas import AssistantModelAnswer


class FakeAssistant:
    def __init__(self) -> None:
        self.evidence = []
        self.target_id = 0

    def answer_tools(self, _request, tools):
        self.evidence = tools
        return AssistantModelAnswer(
            answer=f"适合先试试库内记录 [{self.target_id}]。",
            tool_ids=[self.target_id, 999999],
        )


def test_assistant_uses_only_scoped_records_and_verifies_references() -> None:
    fake = FakeAssistant()
    app.dependency_overrides[get_llm_provider] = lambda: fake
    suffix = uuid4().hex[:8]
    try:
        with TestClient(app) as client:
            quant = client.post(
                "/api/tools",
                json={"name": f"Quant {suffix}", "summary": "量化研究", "tags": ["量化"]},
            ).json()
            fake.target_id = quant["id"]
            client.post(
                "/api/tools",
                json={"name": f"Project {suffix}", "summary": "项目排期", "tags": ["项目管理"]},
            )
            answer = client.post(
                "/api/assistant/ask",
                json={"question": "有什么量化工具？", "scope_tag": "量化", "history": []},
            )
            assert answer.status_code == 200
            assert [tool["id"] for tool in answer.json()["tools"]] == [quant["id"]]
            assert f"【工具 {quant['id']}】" in answer.json()["answer"]
            assert all("量化" in record["tags"] for record in fake.evidence)
            assert all("why_saved" not in record and "notes" not in record for record in fake.evidence)
            with SessionLocal() as session:
                assert session.get(Tool, quant["id"]).last_viewed_at is None
    finally:
        app.dependency_overrides.clear()
