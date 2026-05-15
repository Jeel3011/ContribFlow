# Stage 3 — Change Impact Analysis
### Owner: Jeel

---

## What it does

User describes a planned change in plain English (or pastes a diff). Your stage builds a dependency map of the relevant files, feeds it and the change description to Bob, and Bob traces the full blast radius — what files change, what downstream code breaks, what tests need updating, what's dynamically loaded and therefore uncertain. Every finding gets a confidence score (0.0–1.0) based on how certain Bob is that it found everything.

This is the demo moment of the entire project. You have real merged PRs to validate against. Build this stage first (in terms of your personal effort), iterate the prompt the most, and own it completely.

**Input:**
```json
{
  "repo_url": "https://github.com/owner/repo",
  "change_description": "Modify the retry logic in the HTTP client to use exponential backoff instead of fixed interval",
  "diff": "optional — paste raw git diff here if available"
}
```

**Output:**
```json
{
  "repo": "owner/repo",
  "change_description": "...",
  "files_affected": ["src/http_client.py", "src/utils/retry.py"],
  "services_at_risk": ["DataSyncService", "WebhookDispatcher"],
  "tests_to_update": ["tests/test_http_client.py", "tests/test_retry.py"],
  "findings": [
    {
      "finding": "http_client.py:retry() is called directly in 8 places across the codebase",
      "confidence": 0.95,
      "type": "direct"
    },
    {
      "finding": "WebhookDispatcher imports http_client at module level — retry behavior change will affect all webhook sends",
      "confidence": 0.85,
      "type": "indirect"
    },
    {
      "finding": "Plugin system loads HTTP handlers at runtime — cannot statically verify all callers",
      "confidence": 0.3,
      "type": "dynamic"
    }
  ],
  "suggested_order": [
    "1. Update retry.py with new backoff logic",
    "2. Update http_client.py to use new retry",
    "3. Update tests/test_retry.py",
    "4. Manually verify WebhookDispatcher behavior"
  ]
}
```

---

## Architecture

```
POST /api/stage3/impact
        │
        ▼
  Dependency Builder (your code — no Bob needed yet)
  - Parse the change description to extract target module/function names
  - Fetch relevant source files from GitHub API
  - Build a static dependency map: who imports what
        │
        ▼
  Context Assembler
  - Select the 6–8 most relevant files (target + direct importers + their tests)
  - Trim to first 80 lines each
  - Build the Bob prompt
        │
        ▼
  Bob Ask mode session
  - Multi-hop reasoning across the dependency map
  - Confidence scoring per finding
        │
        ▼
  Bob Response Parser
  - Extract + validate JSON
  - Return structured result
```

---

## Technical implementation

### 1. Static dependency map builder — run BEFORE Bob

This is the most important thing you build. Bob is smarter when you do the mechanical work first and give it structured input instead of raw files.

The dependency map tells you: for a given Python module, what other modules import it?

```python
import re
from collections import defaultdict

def build_dependency_map(tree: list[dict], file_contents: dict[str, str]) -> dict:
    """
    Build an import graph from source files.
    
    tree: list of FileNode dicts from get_tree()
    file_contents: {path: content} for all source files
    
    Returns: {
        "imports": {"file.py": ["other.py", "utils.py"]},     # what each file imports
        "imported_by": {"utils.py": ["file.py", "main.py"]},  # who imports each file
    }
    """
    imports = defaultdict(list)       # file → files it imports
    imported_by = defaultdict(list)   # file → files that import it
    
    # Build a path lookup: module name → file path
    # e.g. "from src.utils.retry import Retry" → maps to "src/utils/retry.py"
    module_to_path = {}
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if not path.endswith(".py"):
            continue
        # Convert path to module notation
        module = path.replace("/", ".").removesuffix(".py")
        module_to_path[module] = path
        # Also index by last component (handles "from retry import X")
        module_to_path[path.split("/")[-1].removesuffix(".py")] = path
    
    # Parse imports in each file
    for path, content in file_contents.items():
        if not path.endswith(".py"):
            continue
        
        for line in content.split("\n"):
            line = line.strip()
            
            # "from src.utils.retry import Retry"
            m = re.match(r'^from\s+([\w.]+)\s+import', line)
            if m:
                module_name = m.group(1)
                target_path = module_to_path.get(module_name) or module_to_path.get(module_name.split(".")[-1])
                if target_path and target_path != path:
                    imports[path].append(target_path)
                    imported_by[target_path].append(path)
            
            # "import src.utils.retry"
            m = re.match(r'^import\s+([\w.]+)', line)
            if m:
                module_name = m.group(1)
                target_path = module_to_path.get(module_name) or module_to_path.get(module_name.split(".")[-1])
                if target_path and target_path != path:
                    imports[path].append(target_path)
                    imported_by[target_path].append(path)
    
    return {
        "imports": dict(imports),
        "imported_by": dict(imported_by)
    }


def find_affected_files(target_files: list[str], dep_map: dict, depth: int = 2) -> dict:
    """
    Given a list of files being changed, find all files affected up to `depth` hops.
    Returns them categorized by hop distance (direct = 1, indirect = 2).
    """
    affected = {"direct": set(), "indirect": set()}
    imported_by = dep_map["imported_by"]
    
    # Direct: files that import the target files
    for target in target_files:
        for importer in imported_by.get(target, []):
            affected["direct"].add(importer)
    
    # Indirect: files that import the direct importers
    if depth >= 2:
        for direct_file in list(affected["direct"]):
            for importer in imported_by.get(direct_file, []):
                if importer not in affected["direct"]:
                    affected["indirect"].add(importer)
    
    return {
        "direct": sorted(affected["direct"]),
        "indirect": sorted(affected["indirect"])
    }
```

---

### 2. Identify target files from change description — also pre-Bob

Given a natural language change description, extract which files are likely being touched. This is a cheap heuristic pass before involving Bob.

```python
def identify_target_files(change_description: str, source_files: list[str]) -> list[str]:
    """
    Map a natural language change description to likely target files.
    Uses keyword matching against file paths — no LLM needed.
    """
    desc_lower = change_description.lower()
    
    # Extract meaningful words from description (skip stop words)
    STOP = {"the", "a", "an", "in", "to", "for", "of", "and", "or", "with",
            "add", "modify", "update", "change", "fix", "improve", "refactor",
            "implement", "create", "use", "make", "instead"}
    
    keywords = [w for w in re.findall(r'\b[a-z_]+\b', desc_lower) if w not in STOP and len(w) > 3]
    
    scored = []
    for path in source_files:
        path_lower = path.lower()
        score = sum(1 for kw in keywords if kw in path_lower)
        if score > 0:
            scored.append((score, path))
    
    scored.sort(reverse=True)
    return [path for _, path in scored[:5]]  # top 5 likely targets
```

---

### 3. Dynamic import detection — find low-confidence cases

These are the ones that get confidence 0.3 — Bob can't know for certain they're affected.

```python
def find_dynamic_imports(file_contents: dict[str, str]) -> list[dict]:
    """
    Find places where imports happen at runtime — these get low confidence scores.
    """
    dynamic = []
    
    DYNAMIC_PATTERNS = [
        (r'importlib\.import_module\(', "importlib.import_module()"),
        (r'__import__\(',              "__import__()"),
        (r'getattr\(.*,\s*[\'"]',      "getattr() used to access attributes by name"),
        (r'globals\(\)\[',             "globals() dict access"),
        (r'plugin.*load',              "possible plugin loading pattern"),
        (r'entry_point',               "setuptools entry point"),
    ]
    
    for path, content in file_contents.items():
        for pattern, label in DYNAMIC_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                # Find the line
                for i, line in enumerate(content.split("\n"), 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        dynamic.append({
                            "file": path,
                            "line": i,
                            "pattern": label,
                            "code": line.strip()[:100]
                        })
    
    return dynamic
```

---

### 4. Context assembler — what you load before calling Bob

Never send all file contents to Bob. Send exactly what it needs.

```python
def assemble_stage3_context(
    target_files: list[str],
    affected: dict,
    file_contents: dict[str, str],
    dep_map: dict,
    max_files: int = 7
) -> dict:
    """
    Select the most relevant files for Bob to analyze.
    Priority: target files first, then direct importers, then indirect.
    Trim each file to first 80 lines.
    """
    priority_files = (
        target_files +
        affected.get("direct", [])[:3] +
        affected.get("indirect", [])[:2]
    )[:max_files]
    
    trimmed_files = {}
    for path in priority_files:
        content = file_contents.get(path, "")
        if not content:
            continue
        lines = content.split("\n")[:80]
        trimmed_files[path] = "\n".join(lines)
    
    # Build a compact dep map summary for Bob (not the full dict)
    dep_summary = []
    for path in priority_files:
        importers = dep_map["imported_by"].get(path, [])
        if importers:
            dep_summary.append(f"{path} ← imported by: {', '.join(importers[:5])}")
    
    return {
        "files": trimmed_files,
        "dep_summary": dep_summary
    }
```

---

### 5. Bob prompt

```python
def build_stage3_prompt(
    repo: str,
    change_description: str,
    diff: str,
    context: dict,
    dynamic_imports: list[dict]
) -> str:
    
    files_block = ""
    for path, content in context["files"].items():
        files_block += f"\n--- {path} ---\n{content}\n"
    
    dep_block = "\n".join(context["dep_summary"])
    
    diff_block = ""
    if diff and diff.strip():
        diff_block = f"\n## Git diff (if available)\n```diff\n{diff[:3000]}\n```"
    
    dynamic_block = ""
    if dynamic_imports:
        dynamic_block = "\n## Dynamic imports found (low confidence zones)\n"
        for d in dynamic_imports[:10]:
            dynamic_block += f"- {d['file']}:{d['line']} — {d['pattern']}: `{d['code']}`\n"
    
    return f"""You are performing change impact analysis for the repository: {repo}

## Proposed change
{change_description}
{diff_block}

## Dependency relationships
{dep_block}

## Relevant source files
{files_block}
{dynamic_block}

---

Your task: trace the full blast radius of this change.

For each finding, assign a confidence score (0.0–1.0) based on HOW CERTAIN you are:
- Direct function call found in specific file: 0.85–0.95
- File imports changed module but usage pattern unclear: 0.5–0.7
- Indirect dependency (2 hops): 0.4–0.6
- Dynamic import or runtime loading pattern found: 0.2–0.4
- Inference without code evidence: 0.1–0.3

Confidence is NOT about code quality. It is about "how sure is this analysis that this file is actually affected."

Provide:
1. files_affected: list of file paths that will need changes
2. services_at_risk: list of service/class names whose behavior will change (not file paths — logical units)
3. tests_to_update: list of test file paths that must be updated or will break
4. findings: each finding with confidence + type (direct|indirect|dynamic)
5. suggested_order: ordered list of changes to make (what to do first to avoid breaking things)

Return ONLY valid JSON. No preamble, no markdown fences.

{{
  "repo": "{repo}",
  "change_description": "{change_description[:100]}...",
  "files_affected": [],
  "services_at_risk": [],
  "tests_to_update": [],
  "findings": [
    {{"finding": "", "confidence": 0.0, "type": "direct|indirect|dynamic"}}
  ],
  "suggested_order": []
}}"""
```

---

### 6. Validating against PR #1395 — your killer demo

This is not optional. Do this before the hackathon starts.

**Step 1:** Go to `opensre/tracer-cloud` PR #1395 on GitHub right now. Record:
- Every file it touched (from the "Files changed" tab)
- Every test it updated
- Any reviewer comment about scope or impact

**Step 2:** Write that down as your **ground truth file**:

```python
# ground_truth_pr1395.py
GROUND_TRUTH = {
    "files_changed": [
        "path/to/actual/file.py",
        # ... fill these in from the actual PR
    ],
    "tests_updated": [
        "tests/test_something.py",
        # ...
    ],
    "reviewer_comments_about_scope": [
        "This changes behavior in X which also affects Y",
        # ...
    ]
}
```

**Step 3:** Run your Stage 3 pipeline against the PR's change description. Compute a match score:

```python
def compute_accuracy(bob_output: dict, ground_truth: dict) -> dict:
    predicted = set(bob_output["files_affected"])
    actual = set(ground_truth["files_changed"])
    
    true_positives = predicted & actual
    false_positives = predicted - actual
    false_negatives = actual - predicted
    
    precision = len(true_positives) / len(predicted) if predicted else 0
    recall    = len(true_positives) / len(actual) if actual else 0
    
    return {
        "precision": round(precision, 2),
        "recall": round(recall, 2),
        "missed": sorted(false_negatives),
        "extra": sorted(false_positives)
    }
```

**Step 4:** If recall is below 0.6 (Bob missed more than 40% of real files), your dep map is incomplete. Common reasons:
- You only fetched 30 files but the repo has 200 — fetch more candidates
- The target file identification step missed the actual target — broaden keyword matching
- Your content trim at 80 lines cut the import section — keep first 30 lines (imports) + lines 40–80 (logic)

**This accuracy number is your demo proof point.** "Bob predicted X out of Y files that this PR actually touched." Make it real.

---

### 7. Bob sessions to run

**Session 1 — Dependency map validation (Ask mode) | ~3 Bobcoins**

Run BEFORE hackathon with tracer-cloud loaded. Purpose: verify your static dep map is roughly correct.

```
@/tracer-cloud/[main source directory]
List the top 5 files that are imported by the most other files in this codebase.
For each, list the files that import it.
Format as JSON: {"file": "path", "imported_by": ["path1", "path2"]}
```

Compare this output to your `build_dependency_map()` output for the same repo. If they diverge significantly, your parser is missing import patterns. Fix it before Day 1.

---

**Session 2 — Prompt accuracy iteration (Ask mode) | ~4 Bobcoins**

This is your most important prep session. Run the full Stage 3 prompt against PR #1395's change description. Use your `compute_accuracy()` function to score it. Iterate once if needed.

```
[Full assembled prompt from build_stage3_prompt() for PR #1395]
```

If Bob's recall is below 0.6: add to the prompt — "Pay special attention to files that import the changed module, even indirectly. Check 2 hops out from the primary change."

If Bob's precision is below 0.5 (too many false positives): add — "Only include a file in files_affected if you have specific code evidence that it calls or depends on the changed function. Do not speculate."

---

**Session 3 — Demo run for export (Ask mode) | ~4 Bobcoins**

This is your export session. Use the final tuned prompt on tracer-cloud PR #1395. This is the session you screenshot and submit.

Screenshot: the full prompt input, Bob's reasoning, and the JSON output. Show the token counter. Export the session. Commit to `/bob-sessions/`.

---

### 8. FastAPI endpoint

```python
# routes/stage3.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class Stage3Request(BaseModel):
    repo_url: str
    change_description: str
    diff: Optional[str] = None

@router.post("/stage3/impact")
async def analyze_impact(req: Stage3Request):
    owner_repo = _parse_url(req.repo_url)
    
    # Fetch data
    try:
        tree = get_tree(owner_repo)
    except Exception as e:
        raise HTTPException(502, f"GitHub API error: {e}")
    
    # Filter to source files only
    SOURCE_EXTS = {".py", ".js", ".ts", ".go", ".java"}
    SKIP_DIRS = {"test", "tests", "node_modules", "vendor", "dist", "build"}
    source_files = [
        item["path"] for item in tree
        if item.get("type") == "blob"
        and any(item["path"].endswith(ext) for ext in SOURCE_EXTS)
        and not any(d in item["path"].split("/") for d in SKIP_DIRS)
    ]
    
    # Identify target files from change description
    target_files = identify_target_files(req.change_description, source_files)
    
    # Fetch content for target files + nearby files
    candidate_paths = list(set(target_files + source_files[:20]))  # target + first 20 source
    file_contents = {}
    for path in candidate_paths[:25]:  # cap at 25 API calls
        content = get_file_content(owner_repo, path)
        if content:
            file_contents[path] = content
    
    # Build dependency map
    dep_map = build_dependency_map(tree, file_contents)
    affected = find_affected_files(target_files, dep_map)
    dynamic_imports = find_dynamic_imports(file_contents)
    
    # Assemble context for Bob
    context = assemble_stage3_context(target_files, affected, file_contents, dep_map)
    
    # Build prompt
    prompt = build_stage3_prompt(
        owner_repo,
        req.change_description,
        req.diff or "",
        context,
        dynamic_imports
    )
    
    return {
        "owner_repo": owner_repo,
        "target_files_identified": target_files,
        "static_affected": affected,
        "dynamic_import_risks": dynamic_imports[:5],
        "prompt_for_bob": prompt,
        "token_estimate": len(prompt)
    }
```

---

### 9. What "done" looks like

- [ ] `build_dependency_map()` correctly maps imports for tracer-cloud
- [ ] `identify_target_files()` correctly identifies target files for PR #1395's change description
- [ ] `find_affected_files()` at depth=2 catches the actual files PR #1395 touched
- [ ] `find_dynamic_imports()` flags any dynamic loading patterns in tracer-cloud
- [ ] Bob prompt assembled and tested — recall ≥ 0.65 against PR #1395 ground truth
- [ ] `parse_stage3_response()` handles all Bob output variations without crashing
- [ ] FastAPI endpoint returns full structured result
- [ ] Demo run session exported to `/bob-sessions/`
- [ ] Ground truth comparison computed and ready for demo narration

---

### 10. What can go wrong and what to do

| Problem | Fix |
|---------|-----|
| Bob misses files that PR #1395 actually touched | Your dep map didn't catch the import chain. Check: is the target file correctly identified? Are the importers being fetched and included in context? |
| `identify_target_files()` picks wrong files | Your keyword extraction from the change description is too naive. Fall back: let Bob identify the target files in a separate Ask session, then use those as input to the dep map. |
| Dep map is empty (no imports found) | Your import regex isn't matching the repo's import style. Add: `from . import module` (relative imports) and `import module as alias` patterns. |
| Dynamic import list is too long (clutters output) | Cap at 5 in the prompt. Show the rest in a collapsible section in the frontend. |
| Bob returns very high confidence on indirect/dynamic files | Add explicit instruction: "Dynamic imports must have confidence ≤ 0.4. Indirect (2-hop) dependencies must have confidence ≤ 0.65." |
| Prompt exceeds 15k chars | Reduce file content from 80 lines to 50 lines. Cut indirect files from context. Keep target + direct importers only. |
