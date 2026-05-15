# ContribFlow — Input / Output Design
### All 4 stages. What we ask, what we return, and why.

---

## The user's journey (context for all I/O decisions)

The user is a developer who found a repo they want to contribute to. They are NOT a maintainer. They have:
- The repo URL
- A vague idea of what they want to do
- Possibly a half-written change description
- Maybe a diff if they've started coding

They don't have: deep knowledge of the codebase, visibility into what's already been proposed, certainty about what their change will affect.

Every input we ask for must be something this person actually has in front of them. Every output must be a decision they can act on immediately.

**The one repo URL rule:** We ask for the GitHub repo URL once, at the top of the page. All 4 stages share it. We never ask for it again.

---

## Stage 1 — Gap Finder

### What the user has at this point
They found a repo they like. They haven't decided what to contribute yet. They want ideas.

### Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `repo_url` | string | yes | Already filled from global input |
| `focus_area` | enum (optional) | no | Filter: "any" / "error handling" / "test coverage" / "missing features" / "deprecated deps" — defaults to "any" |

That's it. Two fields. The second is optional. If we ask for more, we're making the user do analysis before we do — which defeats the point.

**What we do NOT ask:**
- Branch name (we use default branch)
- Programming language (we detect it from the tree)
- "What kind of contribution are you looking for?" — this is Stage 1's job, not the user's

### Output

```json
{
  "repo": "opensre/tracer-cloud",
  "analysis_timestamp": "2026-05-16T10:30:00Z",
  "language_detected": "Python",
  "files_analyzed": 24,
  "gaps": [
    {
      "id": "gap_001",
      "title": "HTTP client has no retry logic on 5xx responses",
      "file": "src/http/client.py",
      "line_range": "45-92",
      "impact": "high",
      "category": "error-handling",
      "evidence": "client.py:67 — bare except clause catches all exceptions including KeyboardInterrupt",
      "reasoning": "This module is imported by 11 other files. Any unhandled network failure here propagates silently across the entire request pipeline.",
      "estimated_effort": "medium",
      "good_first_issue": false
    }
  ],
  "summary": {
    "high_count": 2,
    "medium_count": 5,
    "low_count": 3,
    "top_category": "error-handling"
  }
}
```

**What each field is for:**
- `evidence` — the exact code reference that proves the gap exists. Not "this module lacks error handling." "client.py:67 — bare except clause." This is what makes the output trustworthy.
- `reasoning` — why it matters. How many files it affects. What breaks if ignored.
- `estimated_effort` — low/medium/high. Helps the contributor pick something realistic.
- `good_first_issue` — bool. Explicitly useful for new contributors. We infer this: low effort + isolated + well-understood = true.
- `line_range` — so the user can jump directly to the relevant code. Not just a filename.

**What we do NOT output:**
- Generic advice ("add more docstrings to this module") — we cut these in prompt construction
- More than 10 gaps — beyond that it's noise. We rank and cap.
- Confidence scores — Stage 1 doesn't need them. Confidence belongs in Stage 3 where traceability matters.

**UI display:** Gaps rendered as cards, sorted by impact (high → medium → low). Each card shows: title, file+line, impact badge, category tag, reasoning. Clicking a card shows the full `evidence` field. Export to markdown button at the bottom.

---

## Stage 2 — Idea Deduplication

### What the user has at this point
They have a contribution idea (from Stage 1 or their own head). They want to know if it's already been proposed or built.

### Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `repo_url` | string | yes | Already filled from global input |
| `idea` | string | yes | Plain English. "Add retry logic with exponential backoff to the HTTP client." 1–3 sentences max. |

**What we do NOT ask:**
- Which issue categories to search — we search all of them
- A title vs a description — we take free text and let Bob parse intent
- Whether to search open vs closed — we search both, always

**Hint text for the `idea` field:** "Describe what you want to build in 1–3 sentences. Don't worry about technical precision — describe the goal."

### Output

```json
{
  "repo": "opensre/tracer-cloud",
  "idea": "Add retry logic with exponential backoff to the HTTP client",
  "status": "conflict",
  "checked_against": {
    "open_issues": 47,
    "closed_issues": 102,
    "open_prs": 8,
    "closed_prs": 34
  },
  "conflicts": [
    {
      "type": "issue",
      "number": 142,
      "url": "https://github.com/opensre/tracer-cloud/issues/142",
      "title": "Implement exponential backoff in HTTP layer",
      "state": "open",
      "assigned": true,
      "assignee": "dev-user",
      "similarity": 0.91,
      "summary": "This issue directly covers retry logic in the HTTP client using exponential backoff. Currently assigned and has a milestone. Your idea is covered here.",
      "recommendation": "comment"
    }
  ],
  "recommendation": "conflict_found",
  "recommendation_text": "This idea is already being worked on. Consider commenting on Issue #142 to collaborate rather than opening a duplicate."
}
```

**What each field is for:**
- `checked_against` — shows the user we actually checked. "Bob checked 191 items" builds trust.
- `similarity` — 0.0–1.0. We only show conflicts ≥ 0.5.
- `assigned` + `assignee` — if it's already being worked on, the user should know before they spend time on it.
- `recommendation` — one of: `"proceed"` (clear), `"conflict_found"` (duplicate), `"partial_overlap"` (adjacent but not identical).
- `recommendation_text` — plain English action: "Safe to proceed. No existing issues cover this." or "Consider commenting on Issue #142."

**What we do NOT output:**
- A list of all 191 items we checked — that's noise
- Similarity scores for non-conflicts — we filter these out entirely
- Anything with similarity < 0.5

**UI display:** Large clear/conflict indicator at top (green ✓ / amber ⚠ / red ✗). If clear: "Safe to proceed" with the count of items checked. If conflict: list of conflict cards, each with: issue/PR number + link, title, similarity bar, summary, recommendation action. If partial: show conflicts with a note that the core intent is different.

---

## Stage 3 — Change Impact Analysis (core)

### What the user has at this point
They've decided what to build. They may have written some code or just have a clear description. They want to know what they're going to break before they break it.

### Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `repo_url` | string | yes | Already filled from global input |
| `change_description` | string | yes | Plain English. "Modify the retry function in http_client.py to use exponential backoff instead of fixed interval." 1–5 sentences. |
| `diff` | string | optional | Paste a `git diff` if they've already started coding. If provided, Bob uses this as primary source of truth. If not, Bob reasons from the description alone. |
| `target_files` | string[] | optional | If the user knows which files they're changing. If empty, we auto-detect from the change description. |

**Three usage modes depending on what the user provides:**
- `change_description` only → Bob reasons from description + dep map
- `change_description` + `diff` → Bob uses diff as ground truth, description as context
- All three → most accurate result

We don't force the user to know which files they're changing. `target_files` is optional precisely because the user might not know — and figuring that out is partly what this stage does.

**Hint text for `change_description`:** "Describe your change in plain English. What function or module are you modifying? What is the new behavior? You don't need to be precise about file paths."

### Output

```json
{
  "repo": "opensre/tracer-cloud",
  "change_description": "Modify retry logic in http_client.py to use exponential backoff",
  "analysis_mode": "description_only",
  "target_files_identified": ["src/http/client.py", "src/utils/retry.py"],
  "files_affected": [
    "src/http/client.py",
    "src/utils/retry.py"
  ],
  "services_at_risk": [
    "DataSyncService",
    "WebhookDispatcher"
  ],
  "tests_to_update": [
    "tests/test_http_client.py",
    "tests/test_retry.py"
  ],
  "findings": [
    {
      "id": "f001",
      "finding": "retry() in client.py is called directly from 8 files across the codebase",
      "confidence": 0.95,
      "type": "direct",
      "evidence_files": ["src/sync/data_sync.py", "src/webhooks/dispatcher.py", "src/api/gateway.py"]
    },
    {
      "id": "f002",
      "finding": "WebhookDispatcher imports http_client at module level — any behavior change affects all webhook sends immediately",
      "confidence": 0.82,
      "type": "indirect",
      "evidence_files": ["src/webhooks/dispatcher.py"]
    },
    {
      "id": "f003",
      "finding": "Plugin system loads HTTP handlers via importlib at runtime — cannot statically verify all callers",
      "confidence": 0.28,
      "type": "dynamic",
      "evidence_files": ["src/plugins/loader.py"]
    }
  ],
  "suggested_order": [
    "Update src/utils/retry.py with exponential backoff logic",
    "Update src/http/client.py to use the new retry utility",
    "Run tests/test_retry.py — these will fail and need updating",
    "Manually test WebhookDispatcher — it imports http_client at module level",
    "Check plugin system behavior — dynamic loading means static analysis is incomplete here"
  ],
  "risk_summary": {
    "high_confidence_findings": 2,
    "low_confidence_findings": 1,
    "total_files_affected": 2,
    "services_at_risk_count": 2,
    "has_dynamic_risks": true
  },
  "confidence_explanation": "Confidence reflects how certain this analysis is that a finding is correct — not code quality. Direct function calls score 0.85–0.95. Dynamic/runtime loading scores 0.2–0.35 because static analysis cannot verify these paths."
}
```

**What each field is for:**
- `analysis_mode` — tells the user whether Bob used a diff (most accurate), description only, or both. Sets honest expectations.
- `target_files_identified` — shows what Bob thought the target was. User can validate this.
- `evidence_files` per finding — not just "this file is affected." Here is specifically which file is the evidence. Makes findings verifiable.
- `confidence_explanation` — one-time explanation of what confidence means. It's a non-obvious metric. We explain it once in the output, not buried in docs.
- `suggested_order` — the most actionable field. Not just what's affected — in what order to handle it safely.
- `risk_summary` — compact summary for the UI metrics row.
- `has_dynamic_risks` — boolean flag so the UI can show a specific warning about the plugin system / runtime loading issue.

**What we do NOT output:**
- A confidence score on every file — only on individual findings. Files are just "affected" or not.
- Findings with confidence < 0.2 — below this threshold Bob is speculating, not reasoning.
- A percentage accuracy claim in the output — that's for the demo narration, not a live feature.

**UI display (this is the centrepiece — it needs the most visual attention):**
- Top row: 4 metric chips — files affected / services at risk / tests to update / dynamic risks yes/no
- Main panel: findings list, each showing: finding text + confidence bar + type badge (direct/indirect/dynamic) + evidence files as clickable chips
- Confidence bar: filled left-to-right, color by type — teal for direct, amber for indirect, red for dynamic
- Right panel: suggested order as a numbered checklist
- Bottom: `analysis_mode` badge + `confidence_explanation` in small muted text

---

## Stage 4 — Pre-PR Quality Check

### What the user has at this point
They've written the code. They have a diff. They're about to open a PR and want to catch anything before CI does.

### Input

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `repo_url` | string | yes | Already filled — we use this to fetch convention files |
| `diff` | string | yes | Raw output of `git diff HEAD` or `git diff main`. We parse this ourselves. |

That's it. We don't ask the user to describe what they changed — the diff tells us. We don't ask them what conventions to check — we infer them from the repo.

**Hint text for `diff` field:** "Paste the output of `git diff HEAD` or `git diff main`. You can get this by running that command in your terminal."

**What we do NOT ask:**
- What language the diff is in (we detect from file extensions)
- Which conventions to check (we infer from convention files)
- What CI tools the repo uses (out of scope — we check for common patterns, not CI config)

### Output

```json
{
  "repo": "opensre/tracer-cloud",
  "passes_check": false,
  "summary": "2 errors, 1 warning, 2 info",
  "convention_files_used": ["src/http/client.py", "src/utils/base.py"],
  "issues": [
    {
      "id": "i001",
      "severity": "error",
      "file": "src/http/client.py",
      "line": "67",
      "issue": "Bare except: clause — catches KeyboardInterrupt and SystemExit. Rest of this file uses except Exception specifically.",
      "fix": "Change to: except Exception as e:",
      "source": "bob",
      "category": "convention-violation"
    },
    {
      "id": "i002",
      "severity": "error",
      "file": "src/http/client.py",
      "line": "72",
      "issue": "New retry() function has no type annotations. Every other function in this file is fully annotated.",
      "fix": "Add: def retry(url: str, max_attempts: int = 3, backoff: float = 1.5) -> Response:",
      "source": "bob",
      "category": "convention-violation"
    },
    {
      "id": "i003",
      "severity": "warning",
      "file": "src/http/client.py",
      "line": "80",
      "issue": "Exception caught but not logged. Every other except block in this file calls logger.error() before re-raising.",
      "fix": "Add: logger.error('Retry failed after %d attempts: %s', max_attempts, e)",
      "source": "bob",
      "category": "pattern-inconsistency"
    },
    {
      "id": "i004",
      "severity": "info",
      "file": "src/http/client.py",
      "line": "45",
      "issue": "Unused import: 'from typing import Dict' added but Dict not referenced in the diff.",
      "fix": "Remove unused import.",
      "source": "static",
      "category": "cleanup"
    },
    {
      "id": "i005",
      "severity": "info",
      "file": "tests/test_http_client.py",
      "line": "120",
      "issue": "New retry behavior is tested for the happy path only. No test for max_attempts exhaustion.",
      "fix": "Add test case: def test_retry_exhaustion_raises(): ...",
      "source": "bob",
      "category": "missing-test"
    }
  ],
  "convention_notes": [
    "This repo uses type annotations on all public functions",
    "All except blocks use logger.error() before re-raising",
    "Tests follow pytest, not unittest"
  ]
}
```

**What each field is for:**
- `passes_check` — single boolean. The user's first question is "can I submit this?" Answer it immediately.
- `convention_files_used` — shows which files Bob used to learn the repo's style. Builds trust.
- `source` — "static" (caught by regex) or "bob" (caught by reasoning). Transparent about what AI did vs what's deterministic.
- `category` — groups issues: convention-violation / pattern-inconsistency / cleanup / missing-test / logic-bug.
- `convention_notes` — 2–3 sentences about what conventions Bob inferred from the repo. Lets the user validate that Bob read the right files.
- `fix` — concrete, one-line. Not "consider adding type annotations." "Add: def retry(url: str, ...) -> Response:"

**What we do NOT output:**
- Generic linting advice not grounded in the diff
- Issues from existing code that the diff didn't touch
- More than 10 issues — beyond that it becomes a code review, not a pre-flight check
- `passes_check: true` if there are any errors (only warnings/info don't block passing)

**UI display:** Large green/red pass/fail badge at top. Issue count by severity. Issues as cards, sorted error → warning → info. Each card: severity icon + file:line + issue description + fix (in code font). `convention_notes` at bottom in muted text.

---

## Global inputs that persist across all stages

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Repo URL                              [Analyze]  │
│  https://github.com/opensre/tracer-cloud                 │
└─────────────────────────────────────────────────────────┘

  [Gap Finder]  [Idea Dedup]  [Impact Analysis ●]  [Pre-PR]
```

The repo URL is typed once. All stages share it. The currently active stage is highlighted. The user can navigate between stages freely without re-entering the repo.

**URL validation:** On blur from the repo URL field, we validate it's a real GitHub URL in `owner/repo` format. If invalid, we show an inline error. If valid, we do nothing else — we don't prefetch anything until the user clicks Analyze in a specific stage.

---

## Error states — what we show instead of crashing

| Scenario | What we show |
|----------|-------------|
| GitHub API rate limit | "GitHub rate limit hit. Try again in X minutes." with the reset time. |
| Repo is private | "This repository is private or doesn't exist. Make sure the URL is correct and the repo is public." |
| Repo has no Python/JS/TS/Go files | "No supported source files found in this repo. Currently supports Python, JavaScript, TypeScript, and Go." |
| Bob returns invalid JSON | "Analysis returned an unexpected format. Try again — if this persists, the repo structure may be unusual." (Don't expose raw Bob output to the user.) |
| Diff is malformed | "Couldn't parse this diff. Make sure you're pasting the raw output of `git diff`." |
| Stage 3: no files identified from description | "Couldn't identify which files your change description refers to. Try being more specific about the module or function name, or provide a diff." |

---

## What we never ask

These are things that seem reasonable to ask but will confuse or slow down the user:

- **Branch name** — we use the default branch. If they need a specific branch, that's a v2 feature.
- **Programming language** — we detect it.
- **"How experienced are you?"** — irrelevant, patronizing.
- **GitHub token** — we don't ask the user to authenticate. We use server-side token. If rate limited, we tell them and show the reset time.
- **"What kind of output do you want?"** — we decide the format. The user wants an answer, not a format picker.
