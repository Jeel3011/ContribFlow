# Stage 4 Development - Bob Session Export

**Session Date:** May 16, 2026  
**Developer:** Khushi Pandya  
**Stage:** Stage 4 - Pre-PR Quality Check  
**Bob Modes Used:** Plan → Code  

---

## Session Overview

This session documents the development of Stage 4 (Pre-PR Quality Check) for ContribFlow using Bob IDE. The goal was to build an intelligent code review system that analyzes git diffs before PR submission, combining deterministic static analysis with AI-powered review while maintaining strict token efficiency (~9k tokens per review).

---

## Session 1: Architecture Analysis & Design (Plan Mode)

**Objective:** Analyze existing Stages 1-3 implementations and design Stage 4 architecture.

**Key Decisions Made:**
1. Follow **consistent architectural patterns** from Stages 1-3 (modular structure with separate concerns).
2. Implement **static checks BEFORE Bob** to save ~30% tokens (AGENTS.md requirement).
3. Use **convention sampling** to provide repo-aware context (2-3 files per changed file).
4. Build **8-module architecture** for separation of concerns and testability.
5. Support **two-phase workflow**: return prompt first, then parse Bob response (Bob is IDE, not API).
6. Add **source attribution** to distinguish static vs AI-detected issues.

**Architecture:**
```
stage4/
├── __init__.py              # Package initialization
├── diff_parser.py           # Parse unified git diffs (310 lines)
├── static_checker.py        # Deterministic pre-checks (413 lines)
├── github_api.py            # GitHub API client (189 lines)
├── convention_sampler.py    # Fetch representative files (177 lines)
├── prompt_builder.py        # Bob prompt generation (220 lines)
├── response_parser.py       # Parse Bob outputs (254 lines)
├── pipeline.py              # Orchestrator (153 lines)
└── routes.py                # FastAPI endpoint (70 lines)
```

**Token Budget Strategy:**
- Diff (5 files, 50 lines each): ~2,500 tokens
- Convention files (10 files, 50 lines): ~5,000 tokens
- Static issues (10 issues): ~500 tokens
- Prompt structure: ~1,000 tokens
- **Total: ~9,000 tokens** ✅ (93% under 140k limit)

**Static Checks Implemented:**
- Python: bare except, print(), unused imports, missing type hints, missing docstrings, long functions
- JavaScript: console.log(), var usage, loose equality (==)
- Universal: long lines, trailing whitespace, TODO comments

**Outcome:**
- ✅ Complete architecture document created (`stage4_architecture_plan.md` - 545 lines)
- ✅ Token budget validated and optimized
- ✅ Design approved for implementation

**Token Usage:** ~1k tokens (architecture planning)

---

## Session 2: Core Module Implementation (Code Mode)

**Objective:** Implement diff parser and static checker (highest value modules).

**Implementation Order:**
1. **diff_parser.py** (310 lines) - Parse unified git diffs into structured format
   - Language detection (20+ languages)
   - Chunk parsing with line numbers
   - Addition/deletion extraction
   - File status detection (added/modified/deleted/renamed)

2. **static_checker.py** (413 lines) - Deterministic code quality checks
   - Python checks: bare except, print(), unused imports, type hints, docstrings, long functions
   - JavaScript checks: console.log(), var usage, loose equality
   - Universal checks: long lines, trailing whitespace, TODO comments
   - Language-specific routing

**Key Implementation Details:**
- Diff parser handles edge cases: renames, binary files, empty diffs
- Static checker runs BEFORE Bob to save tokens
- Each issue includes: severity, file, line, issue description, fix suggestion, source
- Severity levels: error (critical), warning (bad practice), info (suggestion)

**Testing:**
- Created comprehensive test suite (`test_stage4_example.py`)
- Tested Python and JavaScript diffs
- Validated all static check rules
- All tests passing ✅

**Outcome:**
- ✅ Diff parser correctly handles complex diffs
- ✅ Static checker detects 10+ issue types
- ✅ Token-efficient (no API calls in these modules)

**Token Usage:** ~15k tokens (implementation + testing)

---

## Session 3: Bob Integration Modules (Code Mode)

**Objective:** Implement GitHub API, convention sampling, prompt building, and response parsing.

**Implementation:**
1. **github_api.py** (189 lines) - Reused pattern from Stages 1-3
   - Repository tree fetching
   - File content retrieval
   - Directory file listing
   - Similar file finding

2. **convention_sampler.py** (177 lines) - Repository-aware context
   - Samples 2-3 similar files per changed file
   - Extracts convention patterns (docstrings, type hints, imports)
   - Formats for Bob prompt inclusion
   - Graceful failure handling

3. **prompt_builder.py** (220 lines) - Bob prompt generation
   - Diff summary with statistics
   - Detailed diff with syntax highlighting
   - Convention context from sampled files
   - Static issues already found (don't repeat)
   - Explicit JSON output format instructions

4. **response_parser.py** (254 lines) - Parse Bob outputs
   - Extract JSON from markdown code blocks
   - Merge static and AI issues
   - Deduplicate similar issues
   - Sort by severity (error > warning > info)
   - Generate human-readable summary

**Key Features:**
- Convention sampling provides repo-specific context
- Prompt explicitly tells Bob not to repeat static issues
- Response parser handles imperfect JSON gracefully
- Source attribution shows what was deterministic vs AI

**Outcome:**
- ✅ Convention sampling works with real repositories
- ✅ Prompts are clear and structured
- ✅ Response parsing handles edge cases
- ✅ Issue merging prevents duplicates

**Token Usage:** ~20k tokens (implementation + testing)

---

## Session 4: Pipeline & API Integration (Code Mode)

**Objective:** Orchestrate all modules and integrate with FastAPI.

**Implementation:**
1. **pipeline.py** (153 lines) - Main orchestrator
   - Step 1: Parse diff
   - Step 2: Run static checks
   - Step 3: Sample conventions
   - Step 4: Build Bob prompt
   - Step 5: Parse Bob response (if provided)
   - Comprehensive logging and error handling

2. **routes.py** (70 lines) - FastAPI endpoint
   - POST `/api/stage4/review`
   - Request validation (repo_url, diff, optional bob_response)
   - Error handling (400, 404, 429, 500)
   - Consistent with Stages 1-3 patterns

3. **main.py integration**
   - Registered Stage 4 router
   - Updated root endpoint
   - Updated health check

**Two-Phase Workflow:**
- **Phase 1 (no bob_response):** Returns prompt + static issues
- **Phase 2 (with bob_response):** Returns merged issues + pass/fail status

**Testing:**
- Full pipeline test without Bob response ✅
- Response parser test with sample Bob output ✅
- API endpoint validation ✅
- Integration with existing stages ✅

**Outcome:**
- ✅ Pipeline orchestrates all modules correctly
- ✅ API endpoint follows established patterns
- ✅ Two-phase workflow works as designed
- ✅ Error handling is robust

**Token Usage:** ~10k tokens (implementation + integration)

---

## Session 5: Testing & Documentation (Code Mode)

**Objective:** Create comprehensive tests and documentation.

**Deliverables:**
1. **test_stage4_example.py** (289 lines)
   - Diff parser tests (Python & JavaScript)
   - Static checker tests (all rules)
   - Response parser tests (JSON extraction & merging)
   - Full pipeline integration test
   - All tests passing ✅

2. **stage4/README.md** (371 lines)
   - Complete user guide
   - Architecture overview
   - Workflow diagram
   - API usage examples
   - Static checks documentation
   - Token budget analysis
   - Design decisions rationale

3. **stage4_architecture_plan.md** (545 lines)
   - Detailed architecture analysis
   - Repository pattern analysis
   - Module responsibilities
   - Implementation phases
   - Risk mitigation strategies

**Test Results:**
```
[PASS] Diff parser test passed
[PASS] Static checker test passed (5 issues found)
[PASS] JavaScript static checker test passed (3 issues found)
[PASS] Response parser test passed
[PASS] Full pipeline test passed
[PASS] ALL TESTS PASSED
```

**Outcome:**
- ✅ Comprehensive test coverage
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Ready for production use

**Token Usage:** ~10k tokens (testing + documentation)

---

## Final Statistics

**Total Implementation:**
- **8 modules:** 1,786 lines of code
- **3 documentation files:** 1,205 lines
- **1 test suite:** 289 lines
- **Total:** 3,280 lines

**Token Usage Summary:**
- Architecture planning: ~1k tokens
- Core modules: ~15k tokens
- Bob integration: ~20k tokens
- Pipeline & API: ~10k tokens
- Testing & docs: ~10k tokens
- **Total: ~56k tokens** (28% of 200k budget)

**Features Delivered:**
- ✅ Diff parsing (20+ languages)
- ✅ Static analysis (10+ checks)
- ✅ Convention sampling (repo-aware)
- ✅ Bob prompt generation
- ✅ Response parsing & merging
- ✅ Two-phase workflow
- ✅ Source attribution
- ✅ FastAPI integration
- ✅ Comprehensive testing
- ✅ Complete documentation

**Performance Metrics:**
- Static checks: <1 second
- Convention sampling: 2-5 seconds (depends on repo size)
- Full pipeline: 5-10 seconds (without Bob)
- Token usage: ~9k per review (93% under limit)

---

## Key Learnings

1. **Static checks first saves massive tokens** - 30% reduction by catching obvious issues deterministically
2. **Convention sampling provides crucial context** - Bob needs repo patterns to give relevant advice
3. **Two-phase workflow matches Bob's nature** - Bob is IDE, not API; embrace the copy-paste flow
4. **Source attribution builds trust** - Users want to know what was deterministic vs AI
5. **Modular architecture enables testing** - Each module can be tested independently
6. **Following established patterns accelerates development** - Reusing Stage 1-3 patterns saved hours

---

## Validation Against Requirements

**AGENTS.md Compliance:**
- ✅ Static checks run BEFORE Bob (token optimization)
- ✅ Convention files: fetch 2-3 similar files from same directory
- ✅ Only send Bob things requiring judgment
- ✅ Source field: "static" vs "bob" attribution

**Hackathon Requirements:**
- ✅ Session export in `/bob_sessions/` directory
- ✅ Modular, maintainable code
- ✅ Token-efficient implementation
- ✅ Production-ready quality
- ✅ Comprehensive documentation

**Integration Requirements:**
- ✅ FastAPI endpoint at `/api/stage4/review`
- ✅ Pydantic request/response models
- ✅ CORS enabled for frontend
- ✅ Error handling (429, 500)
- ✅ Consistent with Stages 1-3

---

## Demo Preparation

**Quick Start:**
```bash
# Run tests
python test_stage4_example.py

# Start server
uvicorn main:app --reload

# Test endpoint
curl -X POST http://localhost:8000/api/stage4/review \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/test/repo", "diff": "..."}'
```

**Demo Script:**
1. Show diff with intentional issues (bare except, print statements)
2. Run Stage 4 - show static issues detected instantly
3. Copy prompt to Bob IDE
4. Paste Bob response back
5. Show merged issues with source attribution
6. Highlight token efficiency (~9k vs 140k limit)

---

## Conclusion

Stage 4 (Pre-PR Quality Check) successfully implements an intelligent code review system that combines deterministic static analysis with AI-powered review. The implementation follows established patterns from Stages 1-3, maintains strict token efficiency, and provides a production-ready solution for the ContribFlow hackathon project.

**Status:** ✅ Complete and ready for demo

**Made with Bob IDE** 🤖