"""
Codeforces MCP Server

Exposes Codeforces data as tools for Claude Desktop (or any MCP client).
Run via stdio transport — intended for local use with Claude Desktop.

Usage:
    uv run main.py
"""

import logging
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Logging — MUST write to stderr only when using stdio transport.
# Writing anything to stdout would corrupt the JSON-RPC stream.
# ---------------------------------------------------------------------------
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("codeforces-mcp")

# ---------------------------------------------------------------------------
# Server init
# ---------------------------------------------------------------------------
mcp = FastMCP("Codeforces Assistant")

CF_API = "https://codeforces.com/api"
HEADERS = {"User-Agent": "codeforces-mcp/1.0"}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
async def cf_get(endpoint: str, params: dict[str, Any] | None = None) -> dict:
    """Make a GET request to the Codeforces API and raise on errors."""
    url = f"{CF_API}/{endpoint}"
    logger.info("CF API request: %s params=%s", endpoint, params)
    async with httpx.AsyncClient(headers=HEADERS, timeout=30.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
    data = response.json()
    if data.get("status") != "OK":
        raise ValueError(f"Codeforces API error: {data.get('comment', 'Unknown error')}")
    return data["result"]


# ---------------------------------------------------------------------------
# Tool 1 — User profile
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_user_profile(handle: str) -> dict:
    """
    Get a Codeforces user's public profile.

    Returns current rating, max rating, rank, max rank, and contribution.

    Args:
        handle: Codeforces username (e.g. "tourist")
    """
    if not handle or not handle.strip():
        raise ValueError("handle must not be empty")

    result = await cf_get("user.info", {"handles": handle.strip()})
    user = result[0]

    return {
        "handle": user["handle"],
        "rating": user.get("rating", "unrated"),
        "max_rating": user.get("maxRating", "unrated"),
        "rank": user.get("rank", "unrated"),
        "max_rank": user.get("maxRank", "unrated"),
        "contribution": user.get("contribution", 0),
        "friend_of_count": user.get("friendOfCount", 0),
        "registered_at": user.get("registrationTimeSeconds"),
    }


# ---------------------------------------------------------------------------
# Tool 2 — Submission history
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_submission_history(handle: str, count: int = 20) -> list[dict]:
    """
    Get a user's most recent submissions on Codeforces.

    Args:
        handle: Codeforces username
        count:  How many recent submissions to return (default 20, max 100)
    """
    if not handle or not handle.strip():
        raise ValueError("handle must not be empty")
    if not (1 <= count <= 100):
        raise ValueError("count must be between 1 and 100")

    result = await cf_get("user.status", {"handle": handle.strip(), "from": 1, "count": count})

    submissions = []
    for sub in result:
        problem = sub.get("problem", {})
        submissions.append({
            "id": sub["id"],
            "problem": f"{problem.get('contestId', '?')}{problem.get('index', '?')} — {problem.get('name', '?')}",
            "tags": problem.get("tags", []),
            "rating": problem.get("rating"),
            "verdict": sub.get("verdict", "UNKNOWN"),
            "language": sub.get("programmingLanguage", "?"),
            "time_ms": sub.get("timeConsumedMillis"),
            "memory_kb": sub.get("memoryConsumedBytes", 0) // 1024,
            "submitted_at": sub.get("creationTimeSeconds"),
        })

    return submissions


# ---------------------------------------------------------------------------
# Tool 3 — Problem finder
# ---------------------------------------------------------------------------
@mcp.tool()
async def find_problems(
    min_rating: int = 800,
    max_rating: int = 3500,
    tags: str = "",
) -> list[dict]:
    """
    Search for Codeforces problems filtered by rating range and/or tags.

    Args:
        min_rating: Minimum problem difficulty rating (default 800)
        max_rating: Maximum problem difficulty rating (default 3500)
        tags:       Comma-separated list of topic tags to filter by,
                    e.g. "dp,greedy" or "graphs". Leave empty for no tag filter.
    """
    if min_rating > max_rating:
        raise ValueError("min_rating must be <= max_rating")

    params: dict[str, Any] = {}
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    if tag_list:
        params["tags"] = ";".join(tag_list)

    result = await cf_get("problemset.problems", params if params else None)
    problems: list[dict] = result.get("problems", [])

    filtered = [
        {
            "id": f"{p.get('contestId', '?')}{p.get('index', '?')}",
            "name": p["name"],
            "rating": p.get("rating"),
            "tags": p.get("tags", []),
            "url": f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}",
        }
        for p in problems
        if p.get("rating") and min_rating <= p["rating"] <= max_rating
    ]

    # Return up to 20 problems so the response stays concise
    return filtered[:20]


# ---------------------------------------------------------------------------
# Tool 4 — Upcoming contests
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_upcoming_contests() -> list[dict]:
    """
    Get a list of upcoming Codeforces contests with start time and duration.
    """
    result = await cf_get("contest.list", {"gym": False})

    upcoming = [
        {
            "id": c["id"],
            "name": c["name"],
            "type": c["type"],
            "phase": c["phase"],
            "start_time_seconds": c.get("startTimeSeconds"),
            "duration_minutes": c.get("durationSeconds", 0) // 60,
        }
        for c in result
        if c.get("phase") == "BEFORE"
    ]

    # Sort by start time ascending
    upcoming.sort(key=lambda x: x.get("start_time_seconds") or 0)
    return upcoming[:10]


# ---------------------------------------------------------------------------
# Tool 5 — Practice recommendation
# ---------------------------------------------------------------------------
@mcp.tool()
async def get_practice_recommendation(handle: str) -> dict:
    """
    Analyse a user's submission history and recommend problems to practice.

    Logic:
    1. Collect last 200 submissions.
    2. Find tags with the most Wrong Answer / Time Limit Exceeded verdicts.
    3. Estimate the user's current "comfort" rating from their recent ACs.
    4. Suggest problems at comfort_rating + 100~300 from the weak tags.

    Args:
        handle: Codeforces username
    """
    if not handle or not handle.strip():
        raise ValueError("handle must not be empty")

    handle = handle.strip()

    # --- fetch submissions ---
    submissions = await cf_get(
        "user.status", {"handle": handle, "from": 1, "count": 200}
    )

    failed_tags: dict[str, int] = {}
    ac_ratings: list[int] = []

    for sub in submissions:
        verdict = sub.get("verdict", "")
        problem = sub.get("problem", {})
        tags = problem.get("tags", [])
        rating = problem.get("rating")

        if verdict == "OK" and rating:
            ac_ratings.append(rating)
        elif verdict in ("WRONG_ANSWER", "TIME_LIMIT_EXCEEDED", "RUNTIME_ERROR"):
            for tag in tags:
                failed_tags[tag] = failed_tags.get(tag, 0) + 1

    # Comfort rating = median of last-20 AC ratings, fallback 1000
    comfort_rating = 1000
    if ac_ratings:
        recent = sorted(ac_ratings[:20])
        comfort_rating = recent[len(recent) // 2]

    target_min = comfort_rating + 100
    target_max = comfort_rating + 300

    # Weak tags = top 3 by failed attempts
    weak_tags = sorted(failed_tags, key=lambda t: failed_tags[t], reverse=True)[:3]

    # Fetch problems matching weak tags in target range
    recommended: list[dict] = []
    seen_ids: set[str] = set()

    for tag in weak_tags:
        result = await cf_get("problemset.problems", {"tags": tag})
        for p in result.get("problems", []):
            pid = f"{p.get('contestId')}{p.get('index')}"
            r = p.get("rating")
            if r and target_min <= r <= target_max and pid not in seen_ids:
                seen_ids.add(pid)
                recommended.append({
                    "id": pid,
                    "name": p["name"],
                    "rating": r,
                    "tags": p.get("tags", []),
                    "url": f"https://codeforces.com/problemset/problem/{p.get('contestId')}/{p.get('index')}",
                    "why": f"You had {failed_tags[tag]} failed attempt(s) on '{tag}' problems",
                })
                if len(recommended) >= 9:
                    break
        if len(recommended) >= 9:
            break

    return {
        "handle": handle,
        "comfort_rating": comfort_rating,
        "target_range": f"{target_min}–{target_max}",
        "weak_tags": [{"tag": t, "failed_attempts": failed_tags[t]} for t in weak_tags],
        "recommended_problems": recommended,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # stdio transport — standard for local Claude Desktop integration
    logger.info("Starting Codeforces MCP server (stdio transport)")
    mcp.run(transport="stdio")
