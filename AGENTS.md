# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Context
ContribFlow is a 4-stage OSS contribution co-pilot for the IBM Bob Hackathon (May 15-17, 2026). This is a **planning and documentation repository**, not a working codebase. The actual implementation will be built during the hackathon.

## Critical Non-Obvious Information

### Bob IDE Constraints (MUST READ)
- **Bob is NOT an API** - It's an IDE tool. The workflow is: FastAPI assembles prompts → copy to Bob IDE → run manually → paste results back
- **Context window**: 200k tokens max, auto-condenses at 140k. Every message sends ENTIRE context - a 50k context costs 50k tokens per message
- **Bobcoins budget**: 40 Bobcoins per account (1 Bobcoin = $0.50). Long sessions deplete fast due to cumulative context costs
- **Context poisoning**: If Bob starts hallucinating, DO NOT try to fix with corrective prompts. Start a new session immediately
- **Mode selection matters**: Ask (cheapest, read-only) → Plan (markdown only) → Code (file edits) → Advanced (MCP tools) → Orchestrator (expensive, delegates)

### Repository Structure (Non-Standard)
- `ContribFlow_Bob_Hackathon_Guide.md` - Complete 48-hour execution plan with time-zone-corrected deadlines
- `ContribFlow_IO_Design.md` - JSON schemas and API contracts (FROZEN - cannot change during hackathon)
- `ContribFlow_UI.jsx` - Complete React UI implementation (831 lines, production-ready)
- `Stage[1-4]_*_Plan.md` - Detailed technical implementation plans for each team member
- `bob_session/` - Where Bob session exports MUST be committed (judges check this)

### Hackathon-Specific Rules
- **Registration closes**: May 15 at 12:00 PM IST (7:00 AM EDT) - NOT 12:30 PM as originally documented
- **Multi-account strategy**: 4 team members × 40 Bobcoins each = 160 total budget. Each member owns one stage
- **Ground truth validation**: Stage 3 MUST validate against tracer-cloud PR #1395 before demo. Compute precision/recall scores
- **Session exports required**: Each stage needs exported Bob session in `/bob-sessions/` or risk disqualification
- **Demo repo**: `opensre/tracer-cloud` is the validation target for all stages

### JSON Schema Contract (IMMUTABLE)
All 4 stages have frozen JSON output schemas defined in `ContribFlow_IO_Design.md`. These cannot change during the hackathon without breaking integration. Key non-obvious fields:
- Stage 3 `confidence` scores are traceability confidence (0.0-1.0), NOT code quality scores
- Stage 3 `type` field: "direct" (0.85-0.95 confidence) / "indirect" (0.4-0.7) / "dynamic" (0.2-0.4)
- Stage 4 `source` field: "static" (regex-based) vs "bob" (AI-based) - shows what was deterministic

### Token Budget Strategy (Critical)
- Never `@mention` full directories - use specific files or line ranges
- New session per focused task - don't mix "explore repo" with "write code"
- If session hits 100k tokens, kill it and summarize in fresh session
- `.bobignore` MUST exclude: node_modules, __pycache__, .git, *.log, venv, dist, build

### Stage-Specific Gotchas
**Stage 1 (Gap Finder)**:
- `score_file_suspiciousness()` runs BEFORE Bob to pre-select top 5 files - saves massive tokens
- Trim commits to 50, issues to 50, file tree to 100 paths max
- Bob prompt explicitly excludes: typos, README badges, test file gaps

**Stage 2 (Idea Dedup)**:
- GitHub `/issues` endpoint returns PRs too - filter with `"pull_request" not in item`
- Semantic matching threshold: only report conflicts with similarity ≥ 0.5
- Closed issues are conflicts ONLY if resolved/merged, not if rejected

**Stage 3 (Change Impact - CORE STAGE)**:
- `build_dependency_map()` runs BEFORE Bob - static analysis is cheaper than AI
- `identify_target_files()` uses keyword matching pre-Bob to narrow scope
- Dynamic imports (importlib, __import__, getattr) automatically get confidence ≤ 0.4
- Validation against PR #1395 is MANDATORY - compute precision/recall before demo

**Stage 4 (Pre-PR Quality)**:
- `static_precheck()` catches bare except, unused imports, print() statements WITHOUT Bob
- Convention files: fetch 2-3 similar files from same directory to establish repo patterns
- Only send Bob things requiring judgment - don't waste tokens on deterministic checks

### GitHub API Patterns
- Rate limit: 5,000 requests/hour with token. One repo analysis uses ~5-25 requests
- Always check `X-RateLimit-Remaining` header and handle 403/429 with exponential backoff
- File content fetch: skip files > 50KB to avoid token bloat
- Pagination: cap at 3 pages (300 items) for issues/PRs to prevent prompt overflow

### Frontend (Streamlit vs React)
- `ContribFlow_UI.jsx` is complete React implementation (831 lines)
- Guide recommends Streamlit for hackathon speed, but React UI is already built
- API base: `http://localhost:8000/api`
- All 4 stages share single repo URL input at top - never ask again

### What NOT to Include (Obvious Information)
- Standard npm/yarn commands
- Framework defaults (React uses JSX, Python uses pip)
- Common patterns (tests in __tests__ folders)
- Information derivable from file extensions or directory names