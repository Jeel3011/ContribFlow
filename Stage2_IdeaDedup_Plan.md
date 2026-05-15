# Stage 2 — Idea Deduplication
### Owner: Member 2 (also owns the shared GitHub API layer)

---

## What it does

User provides a GitHub repo URL and a contribution idea in plain English. Your stage fetches all open AND closed issues plus open PRs. Trims them. Feeds them to Bob in Ask mode. Bob semantically matches the idea against existing work — not keyword search, actual intent matching. Returns a clear signal: safe to proceed, or conflict found with links.

This is the most self-contained stage and the one most likely to work reliably. Build it first. It also validates the shared GitHub API layer that all other stages depend on.

**Input:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "idea": "Add retry logic with exponential backoff to the HTTP client"
}
```

**Output:**
```json
{
  "repo": "owner/repo",
  "idea": "Add retry logic with exponential backoff to the HTTP client",
  "status": "conflict",
  "conflicts": [
    {
      "type": "issue",
      "number": 142,
      "url": "https://github.com/owner/repo/issues/142",
      "title": "Implement exponential backoff in HTTP layer",
      "similarity": 0.9,
      "summary": "This issue directly covers retry logic in the HTTP client. Already assigned to @user."
    }
  ]
}
```

---

## Architecture

```
POST /api/stage2/deduplicate
        │
        ▼
  GitHub API Layer (you build this — shared by all stages)
  - GET /repos/{owner}/{repo}/issues?state=all       → issues (no PRs)
  - GET /repos/{owner}/{repo}/pulls?state=open        → open PRs
  - GET /repos/{owner}/{repo}/pulls?state=closed      → closed/merged PRs
        │
        ▼
  Data Trimmer
  - Issues: number, title, body (300 chars), state, assignees
  - PRs: number, title, body (300 chars), state, merged
  - Combine into one "existing_work" list
        │
        ▼
  Bob Prompt Builder
  - Injects idea + existing_work list
  - Sends to Bob Ask mode
        │
        ▼
  Bob Response Parser
  - Extracts JSON, validates schema
  - Returns clean result
```

---

## Technical implementation

### 1. Shared GitHub API layer — you own this

Every other stage imports from this. Build it clean. This is your biggest responsibility.

```python
# github_client.py
import requests, os, base64, time
from typing import Optional

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def _get(url: str, params: dict = None) -> dict | list:
    """Single GET with rate limit awareness and retry."""
    for attempt in range(3):
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        
        if r.status_code == 403 or r.status_code == 429:
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            wait = max(reset - time.time(), 1)
            if wait > 30:
                raise Exception(f"GitHub rate limit hit. Resets in {int(wait)}s")
            time.sleep(wait + 1)
            continue
        
        r.raise_for_status()
        return r.json()
    
    raise Exception(f"GitHub API failed after 3 attempts: {url}")


def _paginate(url: str, params: dict = None, max_pages: int = 5) -> list:
    """Paginate through GitHub API results up to max_pages."""
    params = params or {}
    params["per_page"] = 100
    results = []
    
    for page in range(1, max_pages + 1):
        params["page"] = page
        data = _get(url, params)
        if not data:
            break
        results.extend(data)
        if len(data) < 100:  # last page
            break
    
    return results


def get_repo_meta(owner_repo: str) -> dict:
    owner, repo = owner_repo.split("/")
    return _get(f"{BASE}/repos/{owner}/{repo}")


def get_tree(owner_repo: str) -> list[dict]:
    owner, repo = owner_repo.split("/")
    meta = get_repo_meta(owner_repo)
    branch = meta["default_branch"]
    data = _get(
        f"{BASE}/repos/{owner}/{repo}/git/trees/{branch}",
        {"recursive": "1"}
    )
    return data.get("tree", [])


def get_commits(owner_repo: str, limit: int = 50) -> list[dict]:
    owner, repo = owner_repo.split("/")
    return _paginate(
        f"{BASE}/repos/{owner}/{repo}/commits",
        max_pages=1  # 1 page = 100 commits, take first `limit`
    )[:limit]


def get_issues(owner_repo: str, state: str = "open") -> list[dict]:
    """Returns issues only — GitHub /issues endpoint returns PRs too, we filter them."""
    owner, repo = owner_repo.split("/")
    all_items = _paginate(
        f"{BASE}/repos/{owner}/{repo}/issues",
        {"state": state},
        max_pages=3  # up to 300 issues
    )
    return [i for i in all_items if "pull_request" not in i]


def get_pull_requests(owner_repo: str, state: str = "open") -> list[dict]:
    owner, repo = owner_repo.split("/")
    return _paginate(
        f"{BASE}/repos/{owner}/{repo}/pulls",
        {"state": state},
        max_pages=3
    )


def get_file_content(owner_repo: str, path: str, max_bytes: int = 50000) -> str:
    """Fetch decoded file content. Returns empty string if too large or missing."""
    owner, repo = owner_repo.split("/")
    try:
        data = _get(f"{BASE}/repos/{owner}/{repo}/contents/{path}")
    except Exception:
        return ""
    
    if isinstance(data, list):  # it's a directory
        return ""
    if data.get("size", 0) > max_bytes:
        return ""
    if data.get("encoding") != "base64":
        return ""
    
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def check_rate_limit() -> dict:
    data = _get(f"{BASE}/rate_limit")
    return data["rate"]  # {"limit": 5000, "remaining": X, "reset": timestamp}
```

**Expose this as FastAPI routes too** (the other stages call your endpoints directly OR import this module — agree with the team which pattern you use before hackathon day):

```python
# routes/github.py
from fastapi import APIRouter, HTTPException
from github_client import get_tree, get_commits, get_issues, get_pull_requests

router = APIRouter(prefix="/repo")

@router.get("/tree")
def repo_tree(url: str):
    owner_repo = _parse_url(url)
    try:
        return get_tree(owner_repo)
    except Exception as e:
        raise HTTPException(502, str(e))

@router.get("/commits")
def repo_commits(url: str, limit: int = 50):
    owner_repo = _parse_url(url)
    return get_commits(owner_repo, limit)

@router.get("/issues")
def repo_issues(url: str, state: str = "open"):
    owner_repo = _parse_url(url)
    return get_issues(owner_repo, state)

@router.get("/prs")
def repo_prs(url: str, state: str = "open"):
    owner_repo = _parse_url(url)
    return get_pull_requests(owner_repo, state)

def _parse_url(url: str) -> str:
    parts = url.rstrip("/").split("/")
    return f"{parts[-2]}/{parts[-1]}"
```

---

### 2. Data trimmer for Stage 2

Stage 2 needs issues AND PRs because someone might already be working on your idea in a PR without an issue.

```python
def trim_for_stage2(issues: list, open_prs: list, closed_prs: list) -> list[dict]:
    """
    Combine issues and PRs into one "existing_work" list for Bob.
    Trim aggressively — Bob needs the title and gist, not the full thread.
    """
    existing = []
    
    for i in issues:
        existing.append({
            "type": "issue",
            "number": i["number"],
            "url": i["html_url"],
            "title": i["title"],
            "body": (i.get("body") or "")[:300].replace("\n", " "),
            "state": i["state"],
            "assignees": [a["login"] for a in i.get("assignees", [])]
        })
    
    for pr in open_prs + closed_prs:
        existing.append({
            "type": "pr",
            "number": pr["number"],
            "url": pr["html_url"],
            "title": pr["title"],
            "body": (pr.get("body") or "")[:300].replace("\n", " "),
            "state": pr["state"],
            "merged": pr.get("merged_at") is not None
        })
    
    # Cap total at 200 items — beyond this is noise and token waste
    return existing[:200]
```

**Token math:** 200 items × ~80 chars each ≈ 16,000 chars ≈ ~4,000 tokens. Safe. A large repo like tracer-cloud probably has ~50 issues and ~20 PRs total, so you'll be well under 200.

---

### 3. Bob prompt — semantic deduplication

This is where Stage 2 wins. Not keyword matching — Bob understands intent.

```python
def build_stage2_prompt(repo: str, idea: str, existing_work: list[dict]) -> str:
    
    work_block = "\n".join(
        f"[{w['type'].upper()} #{w['number']}] {w['title']} | {w['body']}"
        for w in existing_work
    )
    
    return f"""You are checking whether a contribution idea has already been proposed or is being worked on in the repository: {repo}

CONTRIBUTION IDEA:
"{idea}"

EXISTING ISSUES AND PULL REQUESTS:
{work_block}

---

Your task: semantically compare the contribution idea against every issue and PR listed above.

Semantic matching rules:
- "Add retry logic to the HTTP client" MATCHES "Implement exponential backoff in HTTP layer" — same intent, different words
- "Fix authentication bug" does NOT match "Add retry logic" — different problems  
- "Improve test coverage" does NOT match a specific test fix issue — too vague to be a real conflict
- A CLOSED issue is a conflict only if it was resolved/merged. A closed issue that was rejected is NOT a conflict.
- A merged PR is a conflict. An open PR is a strong conflict (someone is already doing it).

For each conflict you find, provide:
- type: "issue" or "pr"
- number: the issue/PR number
- url: the full URL
- title: the existing item's title
- similarity: 0.0 to 1.0 (1.0 = identical intent, 0.5 = overlapping but different scope)
- summary: one sentence explaining WHY this is a conflict. Be specific.

If similarity < 0.4, it is NOT a conflict — do not include it.

Return ONLY valid JSON. No preamble, no explanation, no markdown fences.

If there are NO conflicts:
{{"repo": "{repo}", "idea": "{idea}", "status": "clear", "conflicts": []}}

If there ARE conflicts:
{{"repo": "{repo}", "idea": "{idea}", "status": "conflict", "conflicts": [
  {{"type": "", "number": 0, "url": "", "title": "", "similarity": 0.0, "summary": ""}}
]}}"""
```

---

### 4. Bob response parser

```python
import json, re

def parse_stage2_response(raw: str, repo: str, idea: str) -> dict:
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned).strip()
    
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if not match:
        # Bob might return "No conflicts found" as plain text — handle it
        if any(phrase in raw.lower() for phrase in ["no conflict", "no overlap", "safe to proceed", "clear"]):
            return {"repo": repo, "idea": idea, "status": "clear", "conflicts": []}
        raise ValueError(f"No parseable response from Bob: {raw[:300]}")
    
    data = json.loads(match.group())
    
    # Normalize
    data.setdefault("status", "clear" if not data.get("conflicts") else "conflict")
    data.setdefault("conflicts", [])
    data["repo"] = repo
    data["idea"] = idea
    
    # Filter out low-similarity results Bob might have included anyway
    data["conflicts"] = [c for c in data["conflicts"] if c.get("similarity", 0) >= 0.4]
    
    if data["conflicts"]:
        data["status"] = "conflict"
    
    return data
```

---

### 5. FastAPI endpoint

```python
# routes/stage2.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class Stage2Request(BaseModel):
    repo_url: str
    idea: str

@router.post("/stage2/deduplicate")
async def deduplicate_idea(req: Stage2Request):
    owner_repo = _parse_url(req.repo_url)
    
    # Fetch from GitHub
    try:
        issues      = get_issues(owner_repo, state="all")     # open + closed
        open_prs    = get_pull_requests(owner_repo, state="open")
        closed_prs  = get_pull_requests(owner_repo, state="closed")
    except Exception as e:
        raise HTTPException(502, f"GitHub API error: {e}")
    
    existing = trim_for_stage2(issues, open_prs, closed_prs)
    prompt   = build_stage2_prompt(owner_repo, req.idea, existing)
    
    # Return prompt for manual Bob execution (see note in Stage 1)
    return {
        "owner_repo": owner_repo,
        "idea": req.idea,
        "existing_work_count": len(existing),
        "prompt_for_bob": prompt,
        "token_estimate": len(prompt)
    }
```

---

### 6. Bob sessions to run (in order)

**Session 1 — Baseline test (Ask mode) | ~2 Bobcoins**

Before hackathon starts. Feed tracer-cloud + a fake idea you know conflicts with an existing issue.

```
[Paste your built prompt here for tracer-cloud with idea: "Add retry logic to HTTP requests"]
```

Check if Bob finds the real issue/PR that matches. If it doesn't, your existing_work trimming is cutting too aggressively — increase body trim from 300 to 500 chars.

---

**Session 2 — False positive test (Ask mode) | ~1 Bobcoin**

Same repo, use an idea that you know has NO existing issues:

```
[Paste prompt with idea: "Add a CLI flag to disable colored terminal output"]
```

Verify Bob returns `"status": "clear"`. If it returns false conflicts, your similarity threshold instruction is too loose — add to the prompt: "Only report conflicts where the CORE PURPOSE of the idea is already covered."

---

**Session 3 — Demo run (Ask mode) | ~3 Bobcoins**

This is your export session. Use a real historically interesting case:

Idea: `"Add semantic deduplication check before creating new issues"`

Run it against tracer-cloud. Screenshot everything. Export. Commit to `/bob-sessions/`.

---

### 7. What "done" looks like

- [ ] All 4 shared `github_client.py` functions working and tested against tracer-cloud
- [ ] Other stages confirmed they can import or call your endpoints
- [ ] `trim_for_stage2()` produces payload under 20,000 chars for a 200-item repo
- [ ] Bob returns valid JSON for both `clear` and `conflict` cases
- [ ] `parse_stage2_response()` handles Bob's plain-text fallbacks
- [ ] FastAPI endpoint returns full result with `bob_raw` stored
- [ ] Frontend shows green "Safe to proceed" or red "Conflict found" with linked issues
- [ ] Bob session exported to `/bob-sessions/`

---

### 8. What can go wrong and what to do

| Problem | Fix |
|---------|-----|
| Bob reports a conflict with similarity 0.2 (false positive) | Tighten the prompt: add "Only report if similarity >= 0.5 and the core contribution purpose is already addressed." |
| Bob misses an obvious conflict | The matching issue's body was trimmed too short and the key info was cut off. Increase body trim from 300 to 600 chars. |
| Large repo (1000+ issues) makes prompt too long | Cap at 200 in `trim_for_stage2`. If still too large, take the 100 most recent + 100 most commented (sort by `comments` field). |
| GitHub returns issues AND PRs mixed from /issues endpoint | Already handled — `get_issues()` filters out anything with `"pull_request"` key. |
| `state=all` for closed PRs returns hundreds of stale old PRs | Limit closed PRs to last 6 months: add `since` param with date 6 months ago. |
| Bob response is valid JSON but `status` field is missing | `parse_stage2_response()` infers it from whether `conflicts` is empty. |
