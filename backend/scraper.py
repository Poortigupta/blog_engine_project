"""
scraper.py — Async SERP scraper using SearXNG (self-hosted) + BeautifulSoup4.

Queries a local SearXNG instance (http://localhost:8888) for organic results,
then scrapes the top-3 URLs for h1, h2, and paragraph content to build
a SERP gap-analysis payload.

If SearXNG is unavailable, falls back to DuckDuckGo HTML search, then DDG Lite.
"""

import asyncio
import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, unquote, urlparse

logger = logging.getLogger("blog_engine.scraper")

SEARXNG_URL    = "http://localhost:8888/search"
DDG_URL        = "https://html.duckduckgo.com/html/"
DDG_LITE_URL   = "https://lite.duckduckgo.com/lite/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
MAX_RESULTS     = 3
REQUEST_TIMEOUT = 15.0


def _normalize_url(raw: str) -> str:
    """Normalize raw search links into absolute HTTP(S) URLs."""
    if not raw:
        return ""
    if raw.startswith("//"):
        return f"https:{raw}"
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return ""


def _extract_uddg_target(raw: str) -> str:
    """Decode DuckDuckGo redirect links and return the target URL if present."""
    if "uddg=" not in raw:
        return ""
    target = parse_qs(urlparse(raw).query).get("uddg", [])
    if not target:
        return ""
    return _normalize_url(unquote(target[0]))


async def _fetch(client: httpx.AsyncClient, url: str) -> str | None:
    """Fetch a URL and return raw HTML, or None on error."""
    try:
        resp = await client.get(
            url, headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True
        )
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.debug("_fetch failed for %s: %s", url, exc)
        return None


async def _search_searxng(keyword: str, client: httpx.AsyncClient) -> list[str]:
    """Query SearXNG and extract organic result URLs."""
    params = {
        "q": keyword,
        "format": "json",
        "categories": "general",
        "language": "en",
    }
    try:
        resp = await client.get(SEARXNG_URL, params=params, timeout=10.0)
        data = resp.json()
        urls = [r["url"] for r in data.get("results", [])[:MAX_RESULTS]]
        logger.info("SearXNG returned %d URL(s)", len(urls))
        return urls
    except Exception as exc:
        logger.debug("SearXNG unavailable: %s", exc)
        return []


async def _search_ddg(keyword: str, client: httpx.AsyncClient) -> list[str]:
    """
    Fallback: DuckDuckGo HTML search.

    BUG FIX: The original selector 'a.result__a, a.result__url' matches
    display anchors that contain the visible URL text, NOT the actual href
    to the result page.  DDG wraps real result links inside <a class="result__a">
    whose href is a /l/?uddg=… redirect, OR (on the lite endpoint) in plain
    anchors.  We decode both patterns here so we actually get destination URLs.
    """
    try:
        resp = await client.post(
            DDG_URL,
            data={"q": keyword},
            headers={**HEADERS, "Content-Type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            logger.debug("DDG returned status %d", resp.status_code)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        links: list[str] = []

        # Primary: result__a anchors whose href is a /l/?uddg= redirect
        for a in soup.select("a.result__a"):
            href = a.get("href", "")
            # Try redirect decode first
            target = _extract_uddg_target(href)
            if not target:
                # Fallback: href may already be a direct URL
                target = _normalize_url(href)
            if target:
                links.append(target)
            if len(links) >= MAX_RESULTS:
                break

        # Secondary selector used by some DDG variants
        if not links:
            for a in soup.select("div.result__body a[href]"):
                href = a.get("href", "")
                target = _extract_uddg_target(href) or _normalize_url(href)
                if target:
                    links.append(target)
                if len(links) >= MAX_RESULTS:
                    break

        logger.info("DDG HTML returned %d URL(s)", len(links))
        return links
    except Exception as exc:
        logger.debug("DDG HTML search failed: %s", exc)
        return []


async def _search_ddg_lite(keyword: str, client: httpx.AsyncClient) -> list[str]:
    """
    Fallback: DuckDuckGo Lite — redirect-link decoding.

    BUG FIX: Original code iterated all <a href> tags.  DDG Lite wraps real
    result links in <a> tags inside <td class="result-link"> cells.  Scoping
    to those cells prevents picking up nav/ad/footer links.
    """
    try:
        resp = await client.get(DDG_LITE_URL, params={"q": keyword}, timeout=10.0)
        if resp.status_code != 200:
            logger.debug("DDG Lite returned status %d", resp.status_code)
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        links: list[str] = []

        # Preferred: <td class="result-link"> contains the result anchor
        for td in soup.select("td.result-link"):
            a = td.find("a", href=True)
            if not a:
                continue
            href = a["href"]
            target = _extract_uddg_target(href) or _normalize_url(href)
            if target:
                links.append(target)
            if len(links) >= MAX_RESULTS:
                break

        # Fallback: scan all anchors for uddg= redirects (old lite layout)
        if not links:
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                target = _extract_uddg_target(href)
                if target:
                    links.append(target)
                if len(links) >= MAX_RESULTS:
                    break

        logger.info("DDG Lite returned %d URL(s)", len(links))
        return links
    except Exception as exc:
        logger.debug("DDG Lite search failed: %s", exc)
        return []


def _extract_content(html: str) -> dict:
    """
    Parse HTML with BeautifulSoup4.
    Returns dict with { headings, paragraphs, combined }.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove boilerplate
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    headings: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3"]):
        text = tag.get_text(strip=True)
        if text and len(text) > 3:
            headings.append(text)

    paragraphs: list[str] = []
    for tag in soup.find_all("p"):
        text = tag.get_text(strip=True)
        if len(text) > 60:
            paragraphs.append(text)

    combined = "\n".join(headings + paragraphs[:20])
    return {"headings": headings, "paragraphs": paragraphs[:20], "combined": combined}


async def scrape_serp(keyword: str) -> dict:
    """
    Main entry point.
    1. Search for keyword via SearXNG (fallback: DDG HTML → DDG Lite)
    2. Fetch top-3 URLs concurrently
    3. Extract h1/h2/p content with BS4
    4. Return aggregated SERP payload
    """
    async with httpx.AsyncClient(headers=HEADERS) as client:
        urls = await _search_searxng(keyword, client)

        if not urls:
            logger.info("SearXNG empty — trying DDG HTML")
            urls = await _search_ddg(keyword, client)

        if not urls:
            logger.info("DDG HTML empty — trying DDG Lite")
            urls = await _search_ddg_lite(keyword, client)

        if not urls:
            logger.warning("All search backends returned no URLs for %r", keyword)
            return {
                "keyword": keyword,
                "combined_text": "",
                "headings": [],
                "source_urls": [],
            }

        logger.info("Fetching %d page(s): %s", len(urls), urls)
        pages = await asyncio.gather(*[_fetch(client, url) for url in urls])

    all_headings: list[str] = []
    all_text_parts: list[str] = []

    for html in pages:
        if html:
            extracted = _extract_content(html)
            all_headings.extend(extracted["headings"])
            all_text_parts.append(extracted["combined"])

    # Deduplicate headings while preserving order
    seen: set[str] = set()
    unique_headings: list[str] = []
    for h in all_headings:
        key = h.lower().strip()
        if key not in seen:
            seen.add(key)
            unique_headings.append(h)

    combined_text = "\n\n".join(all_text_parts)
    logger.info(
        "SERP extraction complete | headings=%d text_chars=%d",
        len(unique_headings),
        len(combined_text),
    )

    return {
        "keyword": keyword,
        "combined_text": combined_text[:8000],
        "headings": unique_headings[:40],
        "source_urls": urls,
    }