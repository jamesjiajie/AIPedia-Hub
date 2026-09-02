from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx


class CrawlError(ValueError):
    pass


PROXY_MAPPED_NETWORK = ipaddress.ip_network("198.18.0.0/15")


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    source_type: str
    title: str


def github_repository_targets(url: str) -> list[CrawlTarget] | None:
    """Return a small, high-signal document set for a public GitHub repository."""
    parsed = urlparse(url)
    if parsed.hostname not in {"github.com", "www.github.com"}:
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    owner, repository = parts[:2]
    if owner in {"features", "topics", "search", "settings", "marketplace"}:
        return None
    raw_base = f"https://raw.githubusercontent.com/{owner}/{repository}"
    return [
        CrawlTarget(f"{raw_base}/main/README.md", "github_readme", "GitHub README"),
        CrawlTarget(f"{raw_base}/main/README_ZH.md", "github_readme_zh", "GitHub 中文 README"),
        CrawlTarget(f"{raw_base}/main/README.zh-CN.md", "github_readme_zh", "GitHub 中文 README"),
        CrawlTarget(f"{raw_base}/main/PRODUCT.md", "github_product", "GitHub 产品文档"),
        CrawlTarget(f"{raw_base}/master/README.md", "github_readme", "GitHub README（master）"),
    ]


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, _attrs) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg", "template"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data.strip():
            self.parts.append(data.strip())

    def text(self) -> str:
        return " ".join(self.parts)


def _ensure_public_http_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise CrawlError("只支持公开的 http(s) 链接。")
    # A literal address bypasses DNS and must always be directly globally routable.
    try:
        literal_address = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        literal_address = None
    if literal_address and not literal_address.is_global:
        raise CrawlError("不允许抓取内网、本机或保留地址。")
    if parsed.hostname.lower() == "localhost" or parsed.hostname.lower().endswith(".local"):
        raise CrawlError("不允许抓取内网、本机或保留地址。")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, None)}
    except socket.gaierror as exc:
        raise CrawlError("无法解析目标域名。") from exc
    # This runtime's egress proxy maps public DNS names to 198.18.0.0/15 before forwarding
    # them. Treat only that proxy-mapped range as an exception; all other non-public results
    # (including loopback and private addresses) remain blocked.
    unsafe_addresses = [
        address
        for address in addresses
        if not ipaddress.ip_address(address).is_global
        and ipaddress.ip_address(address) not in PROXY_MAPPED_NETWORK
    ]
    if not addresses or unsafe_addresses:
        raise CrawlError("不允许抓取内网、本机或保留地址。")


def _robots_allows(client: httpx.Client, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = client.get(robots_url)
    except httpx.HTTPError as exc:
        raise CrawlError("无法确认目标网站的 robots 规则。") from exc
    if response.status_code == 404:
        return True
    if response.status_code >= 400:
        raise CrawlError("目标网站拒绝读取 robots 规则。")
    robots = RobotFileParser()
    robots.parse(response.text.splitlines())
    return robots.can_fetch("AIpediaHubBot", url)


def fetch_page_text(url: str, *, max_chars: int = 12_000) -> tuple[str, str]:
    """Fetch one user-supplied public page, respecting robots and blocking SSRF targets."""
    current_url = url
    headers = {"User-Agent": "AIpediaHubBot/0.1 (+personal knowledge library)"}
    with httpx.Client(timeout=httpx.Timeout(20.0, connect=8.0), headers=headers, follow_redirects=False) as client:
        for _ in range(4):
            _ensure_public_http_url(current_url)
            if not _robots_allows(client, current_url):
                raise CrawlError("目标网站的 robots 规则不允许抓取此页面。")
            response = client.get(current_url)
            if response.is_redirect:
                location = response.headers.get("location")
                if not location:
                    raise CrawlError("目标页面返回了无效重定向。")
                current_url = urljoin(current_url, location)
                continue
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "html" not in content_type and "text/plain" not in content_type:
                raise CrawlError("仅支持抓取 HTML 或纯文本页面。")
            extractor = _TextExtractor()
            extractor.feed(response.text)
            text = extractor.text()[:max_chars]
            if not text:
                raise CrawlError("页面没有可用于整理的文本内容。")
            return current_url, text
    raise CrawlError("重定向次数过多。")
