from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

import requests

GITHUB_API_BASE = "https://api.github.com"


class GitHubFetchError(RuntimeError):
    """Raised when GitHub API data cannot be fetched."""


def _build_headers(token: Optional[str]) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "pi4-vagas-prototype",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _normalize_issue(item: Dict[str, Any]) -> Dict[str, Any]:
    labels = [label.get("name", "") for label in item.get("labels", [])]
    return {
        "issue_id": item.get("id"),
        "issue_number": item.get("number"),
        "title": item.get("title") or "",
        "body": item.get("body") or "",
        "state": item.get("state"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "url": item.get("html_url"),
        "author": (item.get("user") or {}).get("login"),
        "labels": labels,
        "label_count": len(labels),
        "comments": item.get("comments", 0),
    }


def fetch_issues(
    owner: str,
    repo: str,
    limit: int = 100,
    state: str = "all",
    token: Optional[str] = None,
    since: Optional[str] = None,
    pause_seconds: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    Fetch repository issues from GitHub API and filter out pull requests.

    Parameters
    ----------
    owner, repo:
        Repository owner/name.
    limit:
        Max number of issues to return.
    state:
        all | open | closed.
    token:
        Optional GitHub token. If not provided, uses GITHUB_TOKEN env var.
    since:
        Optional ISO timestamp to fetch incremental updates.
    pause_seconds:
        Optional delay between paginated requests.
    """
    if limit <= 0:
        return []

    effective_token = token or os.getenv("GITHUB_TOKEN")
    headers = _build_headers(effective_token)

    session = requests.Session()
    issues: List[Dict[str, Any]] = []
    page = 1

    while len(issues) < limit:
        params: Dict[str, Any] = {
            "state": state,
            "sort": "created",
            "direction": "desc",
            "per_page": min(100, max(1, limit - len(issues))),
            "page": page,
        }
        if since:
            params["since"] = since

        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues"
        response = session.get(url, headers=headers, params=params, timeout=30)

        if response.status_code >= 400:
            if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
                reset_epoch = response.headers.get("X-RateLimit-Reset")
                raise GitHubFetchError(
                    "GitHub API rate limit exceeded. Configure GITHUB_TOKEN in environment variables "
                    f"and try again. Rate limit reset epoch: {reset_epoch}."
                )
            message = response.text[:300]
            raise GitHubFetchError(
                f"GitHub API error {response.status_code} while fetching {owner}/{repo}: {message}"
            )

        payload = response.json()
        if not payload:
            break

        for item in payload:
            # Endpoint can include PRs, so we keep only pure issues.
            if "pull_request" in item:
                continue
            issues.append(_normalize_issue(item))
            if len(issues) >= limit:
                break

        page += 1
        if pause_seconds > 0:
            time.sleep(pause_seconds)

    return issues[:limit]
