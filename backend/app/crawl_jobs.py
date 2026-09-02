from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock, Thread
from uuid import uuid4

import httpx
from fastapi import HTTPException

from app.crawler import CrawlError, CrawlTarget, fetch_page_text, github_repository_targets
from app.llm import LLMProvider
from app.schemas import CrawlEvent, CrawlJobRead, CrawlRequest, DiscoverySource, ToolDraftRequest


@dataclass
class _Job:
    job_id: str
    status: str = "queued"
    progress: int = 5
    message: str = "任务已创建，等待抓取。"
    draft: object | None = None
    error: str | None = None
    events: list[CrawlEvent] = field(default_factory=list)

    def read(self) -> CrawlJobRead:
        return CrawlJobRead(
            job_id=self.job_id,
            status=self.status,
            progress=self.progress,
            message=self.message,
            draft=self.draft,
            error=self.error,
            events=self.events,
        )


class CrawlJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, _Job] = {}
        self._lock = Lock()

    def start(self, request: CrawlRequest, provider: LLMProvider) -> CrawlJobRead:
        job = _Job(job_id=str(uuid4()))
        job.events.append(CrawlEvent(at=datetime.now(UTC), level="info", message=job.message))
        with self._lock:
            self._jobs[job.job_id] = job
        Thread(target=self._run, args=(job, request, provider), daemon=True).start()
        return job.read()

    def get(self, job_id: str) -> CrawlJobRead:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                raise HTTPException(status_code=404, detail="未找到抓取任务。")
            return job.read()

    def _update(self, job: _Job, *, progress: int, message: str) -> None:
        with self._lock:
            job.status, job.progress, job.message = "running", progress, message
            job.events.append(CrawlEvent(at=datetime.now(UTC), level="info", message=message))

    def _finish(self, job: _Job, *, status: str, message: str, error: str | None = None, draft=None) -> None:
        with self._lock:
            job.status, job.progress, job.message, job.error, job.draft = status, 100, message, error, draft
            job.events.append(CrawlEvent(at=datetime.now(UTC), level="error" if error else "success", message=error or message))

    def _run(self, job: _Job, request: CrawlRequest, provider: LLMProvider) -> None:
        try:
            urls = list(dict.fromkeys(url for url in (request.official_url, request.source_url) if url))
            targets: list[CrawlTarget] = []
            for url in urls:
                github_targets = github_repository_targets(url)
                if github_targets:
                    self._update(job, progress=10, message="识别到 GitHub 仓库，准备读取 README 与产品文档…")
                    targets.extend(github_targets)
                else:
                    targets.append(CrawlTarget(url, "official" if url == request.official_url else "source", "页面来源"))
            targets = list(dict.fromkeys(targets))[:8]
            sources: list[DiscoverySource] = []
            for index, target in enumerate(targets, start=1):
                progress = 12 + int((index - 1) / len(targets) * 50)
                self._update(job, progress=progress, message=f"正在验证并抓取第 {index}/{len(targets)} 份资料：{target.title}…")
                try:
                    final_url, excerpt = fetch_page_text(target.url, max_chars=10_000)
                except httpx.HTTPStatusError as exc:
                    if exc.response.status_code == 404:
                        self._update(job, progress=progress + 5, message=f"未找到 {target.title}，已跳过。")
                        continue
                    raise
                self._update(job, progress=progress + 5, message=f"已抓取 {target.title}，提取到 {len(excerpt)} 个字符。")
                sources.append(
                    DiscoverySource(
                        url=final_url,
                        title=target.title,
                        source_type=target.source_type,
                        excerpt=excerpt,
                    )
                )
            if not sources:
                raise CrawlError("没有抓取到可用于整理的公开资料。")
            self._update(job, progress=70, message="资料已收集，正在由 Agnes 生成项目研究总结…")
            draft = provider.build_tool_draft(
                ToolDraftRequest(
                    tool_name=request.tool_name,
                    user_hint=request.user_hint,
                    official_url=request.official_url,
                    sources=sources,
                )
            )
            self._finish(job, status="completed", message="草稿已生成，请人工审核后保存。", draft=draft)
        except (CrawlError, HTTPException) as exc:
            detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
            self._finish(job, status="failed", message="抓取或整理失败。", error=str(detail))
        except Exception:
            self._finish(job, status="failed", message="抓取或整理失败。", error="任务执行失败，请稍后重试。")


crawl_jobs = CrawlJobStore()
