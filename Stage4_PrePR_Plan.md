# Stage 4 — Pre-PR Quality Check
### Owner: Member 4 (also owns frontend)

---

## What it does

User pastes a git diff. Your stage fetches 2–3 representative source files from the repo to establish coding conventions, then feeds the diff + convention context to Bob in Code Review mode (or Ask mode). Bob reviews the diff like a senior engineer would: unused imports, obvious bugs, unhandled edge cases, violations of the repo's specific patterns, missing error handling in new code paths. Returns a structured checklist of issues before the user opens the PR and gets flagged by CI.

**Input:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "diff": "--- a/src/http_client.py\n+++ b/src/http_client.py\n@@ ..."
}
```

**Output:**
```json
{
  "repo": "owner/repo",
  "passes_check": false,
  "summary": "3 errors, 2 warnings, 1 info",
  "issues": [
    {
      "severity": "error",
      "file": "src/http_client.py",
      "line": "42",
      "issue": "New retry() function has no type annotations — all other functions in this file use them",
      "fix": "Add return type annotation: def retry(...) -> Response:"
    },
    {
      "severity": "warning",
      "file": "src/http_client.py",
      "line": "67",
      "issue": "Exception caught but not logged — rest of file uses logger.error() on all exceptions",
      "fix": "Add logger.error('Retry failed: %s', e) before re-raising"
    },
    {
      "severity": "info",
      "file": "src/http_client.py",
      "line": "71",
      "issue": "Unused import: 'from typing import Dict' was added but Dict is not used in the diff",
      "fix": "Remove unused import"
    }
  ]
}
```

---

## Architecture

```
POST /api/stage4/review
        │
        ▼
  Diff Parser (your code)
  - Extract file paths mentioned in diff
  - Extract added/removed lines
  - Identify language from file extensions
        │
        ▼
  Convention Sampler (your code)
  - Fetch 2–3 existing source files similar to the changed files
  - These establish the repo's coding conventions
        │
        ▼
  Bob Code Review (Ask or Code mode)
  - Diff + convention files + review prompt
  - Returns structured issue list
        │
        ▼
  Parser + Validator
  - Extract JSON, validate, sort by severity
```

---

## Technical implementation

### 1. Diff parser — extract structure before sending to Bob

Don't send raw diff blindly. Parse it first so you know what you're working with.

```python
import re
from dataclasses import dataclass

@dataclass
class DiffFile:
    path: str
    old_path: str
    added_lines: list[tuple[int, str]]    # (line_number, content)
    removed_lines: list[tuple[int, str]]
    is_new_file: bool
    is_deleted: bool

def parse_diff(diff_text: str) -> list[DiffFile]:
    """Parse a unified diff into structured objects."""
    files = []
    current_file = None
    current_line_new = 0
    
    for line in diff_text.split("\n"):
        # New file header
        if line.startswith("--- "):
            old_path = line[4:].strip()
            old_path = old_path[2:] if old_path.startswith("a/") else old_path
        elif line.startswith("+++ "):
            new_path = line[4:].strip()
            new_path = new_path[2:] if new_path.startswith("b/") else new_path
            current_file = DiffFile(
                path=new_path,
                old_path=old_path if "old_path" in dir() else new_path,
                added_lines=[],
                removed_lines=[],
                is_new_file=(old_path == "/dev/null"),
                is_deleted=(new_path == "/dev/null")
            )
            files.append(current_file)
        
        elif line.startswith("@@ "):
            # Extract new file line number from @@ -old_start,old_count +new_start,new_count @@
            m = re.search(r'\+(\d+)', line)
            if m:
                current_line_new = int(m.group(1)) - 1
        
        elif current_file:
            if line.startswith("+") and not line.startswith("+++"):
                current_line_new += 1
                current_file.added_lines.append((current_line_new, line[1:]))
            elif line.startswith("-") and not line.startswith("---"):
                current_file.removed_lines.append((current_line_new, line[1:]))
            elif not line.startswith("\\"):
                current_line_new += 1
    
    return files


def get_changed_file_paths(diff_files: list[DiffFile]) -> list[str]:
    return [f.path for f in diff_files if not f.is_deleted]


def summarize_diff(diff_files: list[DiffFile]) -> str:
    """Create a compact, Bob-readable summary of the diff."""
    summary = []
    for f in diff_files:
        summary.append(f"FILE: {f.path}")
        summary.append(f"  Added lines ({len(f.added_lines)}):")
        for ln, content in f.added_lines[:50]:  # cap at 50 added lines per file
            summary.append(f"  +{ln}: {content.rstrip()}")
        if len(f.added_lines) > 50:
            summary.append(f"  ... ({len(f.added_lines) - 50} more added lines)")
        summary.append(f"  Removed lines ({len(f.removed_lines)}):")
        for ln, content in f.removed_lines[:20]:
            summary.append(f"  -{ln}: {content.rstrip()}")
    return "\n".join(summary)
```

---

### 2. Convention sampler — pick representative files

The whole point of Stage 4 is catching violations of THIS repo's conventions, not generic lint. To do that, Bob needs to see what the repo's code actually looks like.

```python
def pick_convention_files(
    owner_repo: str,
    changed_paths: list[str],
    all_source_files: list[str]
) -> list[tuple[str, str]]:
    """
    Pick 2–3 source files similar to the changed files.
    "Similar" means: same directory, same file type, similar name pattern.
    Returns list of (path, content) tuples.
    """
    convention_candidates = []
    
    for changed in changed_paths:
        changed_dir = "/".join(changed.split("/")[:-1])
        changed_ext = "." + changed.rsplit(".", 1)[-1] if "." in changed else ""
        
        for candidate in all_source_files:
            if candidate in changed_paths:  # don't use the changed files as convention reference
                continue
            
            candidate_dir = "/".join(candidate.split("/")[:-1])
            candidate_ext = "." + candidate.rsplit(".", 1)[-1] if "." in candidate else ""
            
            # Same directory and extension = best convention reference
            if candidate_dir == changed_dir and candidate_ext == changed_ext:
                convention_candidates.append((2, candidate))  # score 2
            elif candidate_ext == changed_ext:
                convention_candidates.append((1, candidate))  # score 1
    
    # Deduplicate and sort
    seen = set()
    sorted_candidates = []
    for score, path in sorted(convention_candidates, reverse=True):
        if path not in seen:
            seen.add(path)
            sorted_candidates.append(path)
    
    # Fetch content for top 2–3
    result = []
    for path in sorted_candidates[:3]:
        content = get_file_content(owner_repo, path)
        if content:
            # Only take first 60 lines — enough to see conventions
            trimmed = "\n".join(content.split("\n")[:60])
            result.append((path, trimmed))
        if len(result) >= 2:
            break
    
    return result
```

---

### 3. Static pre-checks — run before Bob, saves Bobcoins

Catch the easy stuff yourself. Only send Bob things that need judgment.

```python
def static_precheck(diff_files: list[DiffFile]) -> list[dict]:
    """
    Run deterministic checks on the diff before Bob.
    These are rule-based — no AI needed.
    Returns issues in the same schema as Bob's output.
    """
    issues = []
    
    for f in diff_files:
        added_content = "\n".join(line for _, line in f.added_lines)
        
        # Check for Python-specific patterns in added lines
        if f.path.endswith(".py"):
            
            # Unused imports (added import not used in added code)
            import_pattern = re.compile(r'^import (\w+)|^from [\w.]+ import (\w+(?:,\s*\w+)*)')
            used_names = set(re.findall(r'\b(\w+)\b', added_content))
            
            for ln, line in f.added_lines:
                m = import_pattern.match(line.strip())
                if m:
                    imported = (m.group(1) or m.group(2) or "").split(",")
                    for name in imported:
                        name = name.strip()
                        if name and name not in used_names - {name}:
                            issues.append({
                                "severity": "info",
                                "file": f.path,
                                "line": str(ln),
                                "issue": f"Potentially unused import: '{name}'",
                                "fix": f"Verify '{name}' is used in existing code, or remove it",
                                "source": "static"
                            })
            
            # print() statements in non-test files
            if "test" not in f.path.lower():
                for ln, line in f.added_lines:
                    if re.match(r'\s*print\s*\(', line):
                        issues.append({
                            "severity": "warning",
                            "file": f.path,
                            "line": str(ln),
                            "issue": "print() statement in non-test file — use logger instead",
                            "fix": "Replace with appropriate logger call",
                            "source": "static"
                        })
            
            # Bare except clauses
            for ln, line in f.added_lines:
                if re.match(r'\s*except\s*:', line):
                    issues.append({
                        "severity": "error",
                        "file": f.path,
                        "line": str(ln),
                        "issue": "Bare 'except:' clause catches everything including KeyboardInterrupt",
                        "fix": "Use 'except Exception:' or a more specific exception type",
                        "source": "static"
                    })
    
    return issues
```

---

### 4. Bob prompt — convention-aware review

```python
def build_stage4_prompt(
    repo: str,
    diff_summary: str,
    convention_files: list[tuple[str, str]],
    static_issues: list[dict]
) -> str:
    
    convention_block = ""
    for path, content in convention_files:
        convention_block += f"\n--- EXISTING FILE (for convention reference): {path} ---\n{content}\n"
    
    static_block = ""
    if static_issues:
        static_block = "\n## Issues already found by static analysis (do NOT repeat these)\n"
        for i in static_issues:
            static_block += f"- [{i['severity'].upper()}] {i['file']}:{i['line']} — {i['issue']}\n"
    
    return f"""You are reviewing a git diff as a senior engineer on the {repo} repository.
You care about code quality, consistency with the existing codebase, and catching things that CI will reject.

## Existing code (establishes this repo's conventions)
{convention_block}

## Diff to review
{diff_summary}
{static_block}

---

Your task: review the diff for issues a senior engineer or CI would catch.

Focus on:
1. Convention violations — does new code follow the patterns shown in existing files?
   (type annotations, error handling style, logging style, naming, docstrings)
2. Logic bugs — obvious errors in the added code
3. Missing error handling — new code paths that can fail but don't handle exceptions
4. Edge cases not handled — e.g. empty input, None values, zero division
5. Inconsistencies — new code doing something differently from how the rest of the file does it

Do NOT report:
- Issues already listed in the "static analysis" section above
- Style preferences that aren't specifically violated (don't invent rules)
- Generic advice like "add more tests" without a specific test case in mind
- Anything you cannot ground in the actual diff content

Severity levels:
- error: will likely cause CI failure or runtime bug
- warning: code smell, inconsistency, potential issue
- info: minor improvement, cleanup

Return ONLY valid JSON. No preamble, no markdown fences.

{{
  "repo": "{repo}",
  "passes_check": true,
  "summary": "N errors, N warnings, N info",
  "issues": [
    {{
      "severity": "error|warning|info",
      "file": "",
      "line": "",
      "issue": "Specific description referencing actual code from the diff",
      "fix": "Concrete fix in one sentence"
    }}
  ]
}}

If there are no issues, return passes_check: true and empty issues array."""
```

---

### 5. Bob response parser

```python
import json, re

def parse_stage4_response(raw: str, repo: str, static_issues: list[dict]) -> dict:
    """Parse Bob's review response and merge with static pre-check results."""
    
    # Strip fences
    cleaned = re.sub(r"```(?:json)?\s*", "", raw)
    cleaned = re.sub(r"```\s*", "", cleaned).strip()
    
    match = re.search(r'\{[\s\S]*\}', cleaned)
    if not match:
        # Bob might have said "No issues found" in plain text
        if any(p in raw.lower() for p in ["no issues", "looks good", "no problems", "lgtm"]):
            bob_issues = []
        else:
            bob_issues = []  # fail safe — don't crash
    else:
        try:
            data = json.loads(match.group())
            bob_issues = data.get("issues", [])
        except json.JSONDecodeError:
            bob_issues = []
    
    # Merge static + Bob issues
    all_issues = static_issues + [
        {**i, "source": "bob"} for i in bob_issues
    ]
    
    # Sort by severity: error first, then warning, then info
    severity_order = {"error": 0, "warning": 1, "info": 2}
    all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 2))
    
    error_count   = sum(1 for i in all_issues if i.get("severity") == "error")
    warning_count = sum(1 for i in all_issues if i.get("severity") == "warning")
    info_count    = sum(1 for i in all_issues if i.get("severity") == "info")
    
    return {
        "repo": repo,
        "passes_check": error_count == 0,
        "summary": f"{error_count} errors, {warning_count} warnings, {info_count} info",
        "issues": all_issues
    }
```

---

### 6. FastAPI endpoint

```python
# routes/stage4.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class Stage4Request(BaseModel):
    repo_url: str
    diff: str

@router.post("/stage4/review")
async def review_diff(req: Stage4Request):
    owner_repo = _parse_url(req.repo_url)
    
    # Parse diff
    diff_files = parse_diff(req.diff)
    if not diff_files:
        raise HTTPException(400, "Could not parse diff. Check format.")
    
    changed_paths = get_changed_file_paths(diff_files)
    diff_summary = summarize_diff(diff_files)
    
    # Run static checks first (free — no Bob needed)
    static_issues = static_precheck(diff_files)
    
    # Fetch convention files
    try:
        tree = get_tree(owner_repo)
        SOURCE_EXTS = {".py", ".js", ".ts", ".go"}
        SKIP_DIRS = {"test", "tests", "node_modules", "vendor", "dist"}
        source_files = [
            item["path"] for item in tree
            if item.get("type") == "blob"
            and any(item["path"].endswith(e) for e in SOURCE_EXTS)
            and not any(d in item["path"].split("/") for d in SKIP_DIRS)
        ]
        convention_files = pick_convention_files(owner_repo, changed_paths, source_files)
    except Exception as e:
        convention_files = []  # degrade gracefully — Bob can still review without convention files
    
    # Build prompt
    prompt = build_stage4_prompt(owner_repo, diff_summary, convention_files, static_issues)
    
    return {
        "owner_repo": owner_repo,
        "changed_files": changed_paths,
        "static_issues_found": len(static_issues),
        "convention_files_loaded": [p for p, _ in convention_files],
        "prompt_for_bob": prompt,
        "static_issues": static_issues,
        "token_estimate": len(prompt)
    }
```

---

### 7. Bob sessions to run

**Session 1 — Convention detection test (Ask mode) | ~2 Bobcoins**

Purpose: verify Bob correctly infers conventions from the sample files.

```
Here are two files from the tracer-cloud repository:
[paste content of 2 representative source files, first 40 lines each]

Based on these files, what are the top 5 coding conventions this repo follows?
(type annotations, error handling style, logging, docstrings, naming)
Be specific — reference actual patterns you see in the code.
```

Save the output. If Bob identifies conventions you can also check for statically, add them to `static_precheck()`.

---

**Session 2 — Review accuracy test (Ask mode) | ~3 Bobcoins**

Use PR #1395's diff as input. Run the full Stage 4 prompt. Check: does Bob catch the things that reviewers actually flagged in the PR comments?

```
[Full assembled prompt from build_stage4_prompt() with PR #1395 diff]
```

If Bob is too noisy (reporting trivial things): add to the prompt — "Only report issues that a reviewer would actually block the PR for. Skip style preferences."

If Bob misses real issues: add — "Pay special attention to exception handling patterns. Check that every new try/except follows the same pattern as existing ones in the convention files."

---

**Session 3 — Demo run for export (Ask mode) | ~3 Bobcoins**

Final clean run using PR #1395 diff. This is your export session.

Screenshot the full session. Export. Commit to `/bob-sessions/`.

---

### 8. Frontend — your other responsibility

Use Streamlit. Do not start React from scratch in a hackathon. You will run out of time.

The whole ContribFlow UI is one Streamlit app:

```python
# app.py
import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="ContribFlow", layout="wide")
st.title("ContribFlow — OSS Contribution Co-pilot")

repo_url = st.text_input("GitHub Repository URL", placeholder="https://github.com/owner/repo")

tab1, tab2, tab3, tab4 = st.tabs(["🔍 Gap Finder", "🔁 Dedup", "💥 Impact", "✅ Pre-PR"])

# Stage 1
with tab1:
    if st.button("Find Gaps") and repo_url:
        with st.spinner("Bob is analyzing the repo..."):
            r = requests.post(f"{API_BASE}/stage1/analyze", json={"repo_url": repo_url})
        if r.ok:
            data = r.json()
            gaps = data.get("gaps", [])
            st.success(f"Found {len(gaps)} gaps")
            for gap in sorted(gaps, key=lambda g: {"high":0,"medium":1,"low":2}.get(g["impact"],2)):
                color = {"high":"🔴","medium":"🟡","low":"🟢"}.get(gap["impact"],"⚪")
                with st.expander(f"{color} {gap['title']} — `{gap['file']}`"):
                    st.write(gap["reasoning"])
                    st.caption(f"Category: {gap['category']} | Impact: {gap['impact']}")
        else:
            st.error(f"API error: {r.text}")

# Stage 2
with tab2:
    idea = st.text_area("Your contribution idea", height=80)
    if st.button("Check for Duplicates") and repo_url and idea:
        with st.spinner("Bob is checking for duplicates..."):
            r = requests.post(f"{API_BASE}/stage2/deduplicate", json={"repo_url": repo_url, "idea": idea})
        if r.ok:
            data = r.json()
            if data["status"] == "clear":
                st.success("✅ No conflicts found. Safe to proceed.")
            else:
                st.error(f"⚠️ {len(data['conflicts'])} conflict(s) found")
                for c in data["conflicts"]:
                    st.markdown(f"**[{c['type'].upper()} #{c['number']}]({c['url']})** — {c['title']}")
                    st.caption(f"Similarity: {c['similarity']:.0%} — {c['summary']}")

# Stage 3
with tab3:
    change_desc = st.text_area("Describe your change", height=80)
    diff_input = st.text_area("Paste git diff (optional)", height=120)
    if st.button("Analyze Impact") and repo_url and change_desc:
        with st.spinner("Bob is tracing the blast radius..."):
            r = requests.post(f"{API_BASE}/stage3/impact", json={
                "repo_url": repo_url,
                "change_description": change_desc,
                "diff": diff_input or None
            })
        if r.ok:
            data = r.json()
            col1, col2, col3 = st.columns(3)
            col1.metric("Files Affected", len(data.get("files_affected", [])))
            col2.metric("Services at Risk", len(data.get("services_at_risk", [])))
            col3.metric("Tests to Update", len(data.get("tests_to_update", [])))
            
            st.subheader("Findings")
            for f in sorted(data.get("findings", []), key=lambda x: -x["confidence"]):
                conf = f["confidence"]
                bar = "█" * int(conf * 10) + "░" * (10 - int(conf * 10))
                type_icon = {"direct":"🔴","indirect":"🟡","dynamic":"⚪"}.get(f["type"],"⚪")
                st.markdown(f"{type_icon} `[{bar}] {conf:.0%}` {f['finding']}")
            
            st.subheader("Suggested Order of Changes")
            for step in data.get("suggested_order", []):
                st.markdown(f"- {step}")

# Stage 4
with tab4:
    diff_pr = st.text_area("Paste your git diff", height=200)
    if st.button("Review Before PR") and repo_url and diff_pr:
        with st.spinner("Bob is reviewing your diff..."):
            r = requests.post(f"{API_BASE}/stage4/review", json={"repo_url": repo_url, "diff": diff_pr})
        if r.ok:
            data = r.json()
            if data["passes_check"]:
                st.success(f"✅ Passes check — {data['summary']}")
            else:
                st.error(f"❌ Issues found — {data['summary']}")
            
            for issue in data.get("issues", []):
                icon = {"error":"🔴","warning":"🟡","info":"🔵"}.get(issue["severity"],"⚪")
                with st.expander(f"{icon} [{issue['severity'].upper()}] {issue['file']}:{issue['line']} — {issue['issue'][:60]}"):
                    st.write(f"**Issue:** {issue['issue']}")
                    st.write(f"**Fix:** {issue['fix']}")
                    st.caption(f"Source: {issue.get('source','bob')}")
```

Build this in the first 3 hours of Day 2. Not earlier — you don't have the endpoints to test against.

---

### 9. What "done" looks like

- [ ] `parse_diff()` correctly parses a unified diff from PR #1395
- [ ] `static_precheck()` catches at least 2 real issues in PR #1395's diff
- [ ] `pick_convention_files()` fetches relevant convention files from tracer-cloud
- [ ] Bob prompt returns valid JSON with specific, grounded issues
- [ ] `parse_stage4_response()` merges static + Bob issues correctly
- [ ] FastAPI endpoint returns full result
- [ ] Streamlit UI shows all 4 stages, tab-based, working end-to-end
- [ ] Bob session exported to `/bob-sessions/`

---

### 10. What can go wrong and what to do

| Problem | Fix |
|---------|-----|
| Bob is too generic ("add more comments") | Add to prompt: "Only flag issues grounded in the actual diff lines shown above. Do not give generic advice." |
| Bob reports things not in the diff | Add: "Only review the ADDED lines (lines starting with +). Do not comment on existing code unless the new code interacts with it incorrectly." |
| `parse_diff()` fails on certain diff formats | Use the raw diff as a fallback — send it directly as a string if parsing fails. |
| No convention files found (empty repo / unusual layout) | Fall back gracefully: run prompt without convention block. Bob's general knowledge fills in. Note in output: "Convention context not available." |
| Streamlit is slow or crashes under multiple users | It's a hackathon demo — one user at a time is fine. Don't over-engineer this. |
| Static checker floods output with false positives | Raise the bar: only report bare `except:` as error. Move import check from "info" to a separate "suggestions" field that isn't counted in `passes_check`. |
