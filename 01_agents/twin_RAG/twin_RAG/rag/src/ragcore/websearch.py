from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, TypedDict
import os
import httpx


class WebResult(TypedDict):
    title: str
    snippet: str
    url: str


class WebSearchError(RuntimeError):
    pass


@dataclass
class TavilySearchClient:
    """Tavily Search API client using httpx.

    Env vars:
      - TAVILY_ENDPOINT (default: https://api.tavily.com/search)
      - TAVILY_API_KEY (required)
    """

    timeout_sec: float = 10.0
    endpoint: Optional[str] = None
    api_key: Optional[str] = None

    def _get_endpoint(self) -> str:
        return self.endpoint or os.getenv(
            "TAVILY_ENDPOINT", "https://api.tavily.com/search"
        )

    def _get_key(self) -> str:
        key = self.api_key or os.getenv("TAVILY_API_KEY", "")
        if not key:
            raise WebSearchError("Missing TAVILY_API_KEY")
        return key

    def search(self, query: str, count: int = 5) -> List[WebResult]:
        if not query.strip():
            return []
        payload = {
            "query": query,
            "max_results": int(count),
            "search_depth": "basic",
            "include_answer": False,
            "include_raw_content": False,
        }
        api_key = self._get_key()
        headers = {
            "Content-Type": "application/json",
            # Official REST examples use Authorization: Bearer
            "Authorization": f"Bearer {api_key}",
            # Keep x-api-key for compatibility in some environments
            "x-api-key": api_key,
        }
        url = self._get_endpoint()
        try:
            with httpx.Client(timeout=self.timeout_sec) as client:
                resp = client.post(url, json=payload, headers=headers)
        except httpx.RequestError as e:  # pragma: no cover - transport error
            raise WebSearchError(f"Request error: {e}") from e
        if resp.status_code == 401 or resp.status_code == 403:
            raise WebSearchError("Invalid or unauthorized API key")
        if resp.status_code >= 400:
            raise WebSearchError(f"HTTP {resp.status_code}")

        data = resp.json()
        items = []
        if isinstance(data, dict):
            items = data.get("results") or data.get("data") or []
        results: List[WebResult] = []
        for item in items or []:
            title = (item.get("title") if isinstance(item, dict) else "") or ""
            snippet = ""
            if isinstance(item, dict):
                # Prefer 'content' then 'snippet' if present
                snippet = item.get("content") or item.get("snippet") or ""
            url_item = (item.get("url") if isinstance(item, dict) else "") or ""
            if not url_item:
                continue
            results.append(
                WebResult(title=str(title), snippet=str(snippet), url=str(url_item))
            )
        return results
