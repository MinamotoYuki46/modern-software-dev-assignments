# Codeforces MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes
Codeforces data as tools for Claude Desktop (or any MCP-compatible client).

Ask Claude things like:
- *"What's my current rating and rank on Codeforces?"*
- *"Find me some DP problems rated 1600–1800."*
- *"What contests are coming up this week?"*
- *"Show my last 10 submissions."*
- *"I keep failing greedy problems — what should I practice?"*

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| [uv](https://docs.astral.sh/uv/) | latest |

Install `uv` (if not already installed):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

---

## Setup

```bash
# 1. Clone / copy the project
cd week3/server

# 2. Create virtual environment and install dependencies
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

uv add "mcp[cli]" httpx
```

---

## Running the Server

### Local (stdio) — for Claude Desktop

```bash
uv run main.py
```

The server speaks JSON-RPC over stdio. You don't interact with it directly —
Claude Desktop does.

### Testing with MCP Inspector

```bash
mcp dev main.py
```

Open the Inspector UI and explore tools interactively before connecting to Claude.

---

## Connecting to Claude Desktop

Add the following block to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codeforces": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/week3/server",
        "run",
        "main.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/week3/server` with the actual path on your machine.
Restart Claude Desktop after saving.

---

## Tool Reference

### `get_user_profile`

Fetch a Codeforces user's public profile.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `handle` | string | ✅ | Codeforces username |

**Example input:**
```json
{ "handle": "tourist" }
```

**Example output:**
```json
{
  "handle": "tourist",
  "rating": 3979,
  "max_rating": 4063,
  "rank": "legendary grandmaster",
  "max_rank": "legendary grandmaster",
  "contribution": 169,
  "friend_of_count": 42350
}
```

---

### `get_submission_history`

Get a user's most recent submissions.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `handle` | string | ✅ | — | Codeforces username |
| `count` | integer | ❌ | 20 | Number of submissions (1–100) |

**Example input:**
```json
{ "handle": "tourist", "count": 5 }
```

**Example output:**
```json
[
  {
    "id": 294823910,
    "problem": "2060A — Twin Permutations",
    "tags": ["constructive algorithms", "math"],
    "rating": 800,
    "verdict": "OK",
    "language": "GNU C++23 (64)",
    "time_ms": 46,
    "memory_kb": 0
  }
]
```

---

### `find_problems`

Search for problems by rating range and/or tags. Returns up to 20 results.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `min_rating` | integer | ❌ | 800 | Minimum difficulty rating |
| `max_rating` | integer | ❌ | 3500 | Maximum difficulty rating |
| `tags` | string | ❌ | `""` | Comma-separated tags, e.g. `"dp,greedy"` |

**Example input:**
```json
{ "min_rating": 1600, "max_rating": 1800, "tags": "dp" }
```

**Example output:**
```json
[
  {
    "id": "1986D",
    "name": "Maximize the Root",
    "rating": 1800,
    "tags": ["dp", "dfs and similar", "trees"],
    "url": "https://codeforces.com/problemset/problem/1986/D"
  }
]
```

---

### `get_upcoming_contests`

List upcoming Codeforces contests (up to 10). Sorted by start time.

No parameters required.

**Example output:**
```json
[
  {
    "id": 2108,
    "name": "Codeforces Round 1000 (Div. 2)",
    "type": "CF",
    "phase": "BEFORE",
    "start_time_seconds": 1741600200,
    "duration_minutes": 135
  }
]
```

---

### `get_practice_recommendation`

Analyse a user's recent submissions and recommend targeted practice problems.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `handle` | string | ✅ | Codeforces username |

**Logic:**
1. Fetches last 200 submissions.
2. Counts which tags have the most WA / TLE / RE verdicts.
3. Estimates comfort rating from recent AC problems.
4. Returns problems at `comfort_rating + 100–300` from the top 3 weak tags.

**Example input:**
```json
{ "handle": "yuki_cf" }
```

**Example output:**
```json
{
  "handle": "yuki_cf",
  "comfort_rating": 1500,
  "target_range": "1600–1800",
  "weak_tags": [
    { "tag": "graphs", "failed_attempts": 7 },
    { "tag": "dp", "failed_attempts": 4 },
    { "tag": "binary search", "failed_attempts": 3 }
  ],
  "recommended_problems": [
    {
      "id": "1742G",
      "name": "Orray",
      "rating": 1600,
      "tags": ["graphs", "greedy"],
      "url": "https://codeforces.com/problemset/problem/1742/G",
      "why": "You had 7 failed attempt(s) on 'graphs' problems"
    }
  ]
}
```

---

## Error Handling

All tools validate their inputs and return descriptive error messages for:
- Empty or missing required parameters
- Out-of-range values (e.g. `count > 100`)
- Unknown Codeforces handles
- Codeforces API timeouts or downtime

---

## Project Structure

```
week3/
└── server/
    ├── main.py      # MCP server — all 5 tools defined here
    └── README.md    # This file
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp[cli]` | Official MCP Python SDK (includes FastMCP) |
| `httpx` | Async HTTP client for Codeforces API requests |
