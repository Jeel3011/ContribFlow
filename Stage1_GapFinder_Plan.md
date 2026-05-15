# Stage 1 — Gap Finder
### Owner: Member 3

---

## What it does

User provides a GitHub repo URL. Your stage fetches the repo file tree, last 50 commits, and open issues. You trim that data, feed it to Bob in Ask mode, and Bob returns a ranked JSON list of **real** contribution gaps — missing error handling, zero test coverage on critical paths, deprecated dependencies, unhandled TODOs in core modules. Not typos. Not README badges.

**Input to your FastAPI endpoint:**
```json
{ "repo_url": "https://github.com/owner/repo" }
```

**Output:**
```json
{
  "repo": "owner/repo",
  "gaps": [
    {
      "title": "Short one-line description",
      "file": "path/to/file.py",
      "impact": "high",
      "category": "error-handling",
      "reasoning": "2-3 sentences grounded in actual code. Not generic."
    }
  ]
}
```

---

## Architecture

```
POST /api/stage1/analyze
        │
        ▼
  GitHub API Layer (shared, built by Member 2)
  - GET /repos/{owner}/{repo}/git/trees/HEAD?recursive=1   → file tree
  - GET /repos/{owner}/{repo}/commits?per_page=50          → last 50 commits
  - GET /repos/{owner}/{repo}/issues?state=open&per_page=100 → open issues
        │
        ▼
  Data Trimmer (your code)
  - Filter tree: only .py, .js, .ts, .go files (no tests, no vendor)
  - Commits: keep only sha (short), message, date
  - Issues: keep only number, title, first 200 chars of body
  - Fetch file content for top 5 "suspicious" files (by heuristic)
        │
        ▼
  Bob Prompt Builder
  - Assembles trimmed data into the prompt
  - Sends to Bob via Ask mode session
        │
        ▼
  Bob Response Parser
  - Extracts JSON from Bob's response
  - Validates against schema
  - Returns to FastAPI
```

---

## Technical implementation

### 1. Shared GitHub fetcher (coordinate with Member 2)

This is used by all 4 stages. Member 2 owns it. You consume it. The interface:

```python
# github_client.py — Member 2 builds this, you import it
from github_client import GitHubClient

client = GitHubClient(token=os.environ["GITHUB_TOKEN"])

tree    = client.get_tree("opensre/tracer-cloud")      # list of FileNode
commits = client.get_commits("opensre/tracer-cloud", limit=50)
issues  = client.get_issues("opensre/tracer-cloud", state="open")
```

If Member 2 is not done yet, write a local stub:

```python
import requests, os

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28"
}

def get_tree(owner_repo: str) -> list[dict]:
    owner, repo = owner_repo.split("/")
    # Get default branch first
    r = requests.get(f"https://api.github.com/repos/{owner}/{repo}", headers=HEADERS)
    r.raise_for_status()
    branch = r.json()["default_branch"]
    
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}",
        headers=HEADERS,
        params={"recursive": "1"}
    )
    r.raise_for_status()
    return r.json().get("tree", [])

def get_commits(owner_repo: str, limit: int = 50) -> list[dict]:
    owner, repo = owner_repo.split("/")
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/commits",
        headers=HEADERS,
        params={"per_page": limit}
    )
    r.raise_for_status()
    return r.json()

def get_issues(owner_repo: str, state: str = "open") -> list[dict]:
    owner, repo = owner_repo.split("/")
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/issues",
        headers=HEADERS,
        params={"state": state, "per_page": 100}
    )
    r.raise_for_status()
    # GitHub issues endpoint returns PRs too — filter them out
    return [i for i in r.json() if "pull_request" not in i]

def get_file_content(owner_repo: str, path: str) -> str:
    """Fetch raw file content. Returns empty string if too large or error."""
    owner, repo = owner_repo.split("/")
    r = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
        headers=HEADERS
    )
    if r.status_code != 200:
        return ""
    data = r.json()
    if data.get("size", 0) > 50000:  # skip files > 50KB — too token-heavy
        return ""
    import base64
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
```

**Rate limit reality:** With a token you have 5,000 requests/hour. For one repo analysis you'll use ~5 requests. You're fine. But add a check anyway:

```python
def check_rate_limit() -> dict:
    r = requests.get("https://api.github.com/rate_limit", headers=HEADERS)
    return r.json()["rate"]  # {"limit": 5000, "remaining": 4995, "reset": 1234567890}
```

---

### 2. Data trimmer — the most important function you write

This is where you control what Bob sees. Too much data = context bloat = bad reasoning + wasted Bobcoins. Too little = Bob hallucinates. Get this right.

```python
def trim_for_stage1(tree: list, commits: list, issues: list) -> dict:
    
    # --- File tree: only source files, no tests, no vendor, no generated ---
    SOURCE_EXTS = {".py", ".js", ".ts", ".go", ".java", ".rb", ".rs"}
    SKIP_DIRS = {"test", "tests", "__pycache__", "node_modules", "vendor", 
                 "dist", "build", ".git", "migrations", "static", "assets"}
    
    source_files = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        parts = set(path.split("/"))
        if parts & SKIP_DIRS:
            continue
        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
        if ext in SOURCE_EXTS:
            source_files.append(path)
    
    # --- Commits: just sha (7 chars) + message title + date ---
    trimmed_commits = []
    for c in commits[:50]:
        trimmed_commits.append({
            "sha": c["sha"][:7],
            "message": c["commit"]["message"].split("\n")[0][:100],
            "date": c["commit"]["author"]["date"][:10]
        })
    
    # --- Issues: number + title + first 200 chars of body ---
    trimmed_issues = []
    for i in issues[:50]:  # cap at 50 — more than this is noise
        trimmed_issues.append({
            "number": i["number"],
            "title": i["title"],
            "body": (i.get("body") or "")[:200]
        })
    
    return {
        "source_files": source_files,    # flat list of paths
        "recent_commits": trimmed_commits,
        "open_issues": trimmed_issues
    }
```

---

### 3. Suspicious file heuristic — pick 5 files for Bob to read deeply

Bob can't read every file in a real repo. You need to pre-select the 5 most likely to have gaps. Do this with cheap heuristics before involving Bob at all:

```python
import re

def score_file_suspiciousness(content: str, path: str) -> int:
    """
    Higher score = more likely to have meaningful gaps.
    Does NOT require Bob. Pure text analysis.
    """
    score = 0
    
    # Has TODO/FIXME/HACK/XXX comments
    score += len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX)', content, re.IGNORECASE)) * 3
    
    # Functions defined but no try/except anywhere in file
    func_count = len(re.findall(r'^\s*def ', content, re.MULTILINE))
    try_count = len(re.findall(r'^\s*try:', content, re.MULTILINE))
    if func_count > 3 and try_count == 0:
        score += 10  # functions with zero error handling
    
    # Has raise NotImplementedError or pass in function bodies
    score += len(re.findall(r'raise NotImplementedError', content)) * 5
    
    # Imports deprecated libraries
    DEPRECATED = ["imp", "asynchat", "asyncore", "cgi", "cgitb", "crypt"]
    for dep in DEPRECATED:
        if f"import {dep}" in content or f"from {dep}" in content:
            score += 8
    
    # File name suggests it's core/critical
    CORE_SIGNALS = ["core", "main", "base", "engine", "handler", "manager", "service"]
    if any(s in path.lower() for s in CORE_SIGNALS):
        score += 5
    
    return score


def pick_top_files(owner_repo: str, source_files: list[str], top_n: int = 5) -> list[tuple[str, str]]:
    """
    Fetch content for files, score them, return top N as (path, content) tuples.
    This costs top_n GitHub API calls — worth it to give Bob focused input.
    """
    scored = []
    # Sample up to 30 files to score — don't fetch all 200
    candidates = source_files[:30]
    
    for path in candidates:
        content = get_file_content(owner_repo, path)
        if not content:
            continue
        score = score_file_suspiciousness(content, path)
        scored.append((score, path, content))
    
    scored.sort(reverse=True)
    return [(path, content) for _, path, content in scored[:top_n]]
```

---

### 4. Bob prompt — what you send

This is the final prompt template. Assemble it in Python, then run it in Bob manually (Ask mode) during the hackathon. Copy-paste the output and parse it.

```python
def build_stage1_prompt(repo: str, trimmed_data: dict, top_files: list[tuple]) -> str:
    
    file_list = "\n".join(trimmed_data["source_files"][:100])  # cap at 100 paths
    
    commits_block = "\n".join(
        f"[{c['date']}] {c['sha']} {c['message']}"
        for c in trimmed_data["recent_commits"]
    )
    
    issues_block = "\n".join(
        f"#{i['number']}: {i['title']} — {i['body']}"
        for i in trimmed_data["open_issues"]
    )
    
    files_block = ""
    for path, content in top_files:
        # Truncate file content — first 100 lines is enough for gap detection
        lines = content.split("\n")[:100]
        files_block += f"\n--- FILE: {path} ---\n" + "\n".join(lines) + "\n"
    
    return f"""You are analyzing the open source repository: {repo}

## Repository file structure (source files only)
{file_list}

## Recent commits (last 50)
{commits_block}

## Open issues
{issues_block}

## Key source files (content)
{files_block}

---

Your task: identify REAL, meaningful contribution gaps in this repository.

What counts as real:
- A module with no try/except blocks that is called from many other files
- A public function with no test coverage that is part of the critical path
- A TODO/FIXME comment in a core file that describes missing functionality
- An import of a deprecated Python standard library module
- A class or module with no docstring that is exported and used externally

What does NOT count:
- Typos in comments or documentation
- Missing README sections or badge additions
- Minor formatting inconsistencies
- Test files themselves being incomplete

For each gap you find, provide:
- title: one-line description of the specific gap
- file: the file path where it exists
- impact: "high" if it's in a critical path or called from 5+ places, "medium" if isolated, "low" if cosmetic
- category: one of error-handling, test-coverage, documentation, missing-feature, deprecated-dependency
- reasoning: 2-3 sentences. Reference the actual code evidence. Not generic statements.

Return ONLY valid JSON. No preamble, no explanation, no markdown code fences.

{{
  "repo": "{repo}",
  "gaps": [
    {{
      "title": "",
      "file": "",
      "impact": "high|medium|low",
      "category": "error-handling|test-coverage|documentation|missing-feature|deprecated-dependency",
      "reasoning": ""
    }}
  ]
}}"""
```

---

### 5. Bob response parser — handle the mess

Bob will not always return clean JSON. It might wrap it in markdown fences, add a preamble sentence, or occasionally return malformed JSON. Handle all of it:

```python
import json, re

def parse_bob_response(raw: str) -> dict:
    """
    Extract and validate JSON from Bob's raw response.
    Bob sometimes wraps in ```json ... ```, sometimes adds a sentence before.
    """
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    
    # Try to find JSON object even if there's text before/after
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if not match:
        raise ValueError(f"No JSON object found in Bob response. Raw:\n{raw[:500]}")
    
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON from Bob: {e}\nExtracted:\n{match.group()[:500]}")
    
    # Validate structure
    if "gaps" not in data:
        raise ValueError(f"Bob returned JSON but missing 'gaps' key: {data}")
    
    # Normalize each gap — fill missing fields with safe defaults
    valid_impacts = {"high", "medium", "low"}
    valid_categories = {"error-handling", "test-coverage", "documentation", 
                        "missing-feature", "deprecated-dependency"}
    
    for gap in data["gaps"]:
        if gap.get("impact") not in valid_impacts:
            gap["impact"] = "medium"
        if gap.get("category") not in valid_categories:
            gap["category"] = "missing-feature"
        gap.setdefault("title", "Untitled gap")
        gap.setdefault("file", "unknown")
        gap.setdefault("reasoning", "")
    
    return data
```

---

### 6. FastAPI endpoint — wire it all together

```python
# routes/stage1.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os

router = APIRouter()

class Stage1Request(BaseModel):
    repo_url: str  # e.g. "https://github.com/opensre/tracer-cloud"

class Stage1Response(BaseModel):
    repo: str
    gaps: list[dict]
    bob_raw: str      # preserve raw Bob output for session export evidence
    token_estimate: int  # rough char count of what you sent Bob

@router.post("/stage1/analyze")
async def analyze_gaps(req: Stage1Request) -> Stage1Response:
    # Parse repo from URL
    parts = req.repo_url.rstrip("/").split("/")
    owner_repo = f"{parts[-2]}/{parts[-1]}"
    
    # Fetch data
    try:
        tree    = get_tree(owner_repo)
        commits = get_commits(owner_repo, limit=50)
        issues  = get_issues(owner_repo, state="open")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e}")
    
    # Trim
    trimmed = trim_for_stage1(tree, commits, issues)
    
    # Pick top 5 suspicious files
    top_files = pick_top_files(owner_repo, trimmed["source_files"], top_n=5)
    
    # Build prompt
    prompt = build_stage1_prompt(owner_repo, trimmed, top_files)
    
    # --- MANUAL STEP during hackathon demo ---
    # Copy `prompt` to Bob IDE, run in Ask mode, paste response back.
    # For the automated version, you store the Bob response and parse it:
    
    # bob_raw = run_bob_session(prompt)  # see note below
    # result = parse_bob_response(bob_raw)
    
    # For now return the prompt so you can run it manually:
    return {
        "repo": owner_repo,
        "gaps": [],
        "bob_raw": "",
        "token_estimate": len(prompt),
        "prompt_for_bob": prompt  # remove this field before submission polish
    }
```

**Note on "run_bob_session":** Bob is an IDE, not an API. There is no programmatic way to call it. During the hackathon, the flow is: your FastAPI endpoint assembles the prompt → you copy it to Bob → you run it → you paste the output back into your frontend. That is a valid demo. The judges care that Bob did the reasoning, not that it was automated end-to-end.

---

### 7. Bob sessions to run (in order)

**Session 1 — Repo exploration (Ask mode) | ~3 Bobcoins**

Purpose: understand tracer-cloud before writing anything. Run this before the hackathon starts.

```
Message 1 (to Bob, Ask mode):
@/tracer-cloud/[main source directory]
List all Python files in this directory with:
- Number of functions defined
- Whether any try/except blocks exist
- Whether a corresponding test file exists in /tests/
Format as a plain table. No explanations.
```

```
Message 2 (same session):
Based on what you just read, which 3 files are the most likely to have
meaningful contribution gaps — missing error handling, zero tests, or deprecated patterns?
Just the file paths and one sentence each. Nothing else.
```

Save both outputs. Kill the session after this.

---

**Session 2 — Prompt refinement (Plan mode) | ~2 Bobcoins**

Purpose: improve your prompt template against tracer-cloud ground truth.

```
Message 1:
I'm building a tool that finds real OSS contribution gaps.
Here is my current prompt template: [paste your prompt]
Here is what Bob returned for tracer-cloud: [paste Session 1 output]

What's missing from this analysis that a real contributor would care about?
What would make the reasoning more specific and grounded?
Suggest 3 concrete improvements to the prompt. Keep it concise.
```

Apply the suggestions. Freeze the prompt. Don't keep iterating — you will run out of Bobcoins.

---

**Session 3 — Demo run (Ask mode) | ~4 Bobcoins**

This is the session you export for the judges. Run it on tracer-cloud with your final prompt. This is your evidence session.

```
[Paste your final assembled prompt from build_stage1_prompt()]
```

Screenshot the full session. Export it. Commit to /bob-sessions/.

---

### 8. What "done" looks like

- [ ] `GET /repo/tree`, `/repo/commits`, `/repo/issues` endpoints from Member 2 working
- [ ] `trim_for_stage1()` produces trimmed payload under 8,000 chars
- [ ] `pick_top_files()` returns 5 files with suspiciousness scores
- [ ] `build_stage1_prompt()` produces a clean, assembled prompt
- [ ] Manually running the prompt in Bob returns valid JSON with 3+ gaps
- [ ] `parse_bob_response()` handles fenced and unfenced JSON without crashing
- [ ] FastAPI endpoint returns the full result including `bob_raw`
- [ ] Frontend displays gaps as cards sorted by impact (high first)
- [ ] Bob session exported and committed to `/bob-sessions/`

---

### 9. What can go wrong and what to do

| Problem | Fix |
|---------|-----|
| Bob returns generic gaps ("add docstrings everywhere") | Your context files are too shallow. Replace with deeper files using `get_file_content()` on specific paths, not the overview. |
| Bob returns malformed JSON | `parse_bob_response()` handles it. If it fails, ask Bob in a new message: "Return only the JSON, no other text." Then paste that. |
| Repo has 0 Python files | Your trimmer finds nothing. Add a check: if `source_files` is empty, return early with `{"gaps": [], "error": "No source files found"}`. |
| GitHub API returns 403 | Token missing or expired. Check `GITHUB_TOKEN` env var. Check `check_rate_limit()`. |
| Prompt is over 15,000 chars | You're including too many files or too many commits. Cap `source_files` to 80 in prompt, `commits` to 20, `issues` to 30. |
| Bob session hits 140k tokens (auto-condenses) | You sent too much context. Start fresh, use only the top 3 files instead of 5. |
