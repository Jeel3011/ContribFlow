# ContribFlow — IBM Bob Hackathon Complete Operational Guide
### Team: ChainToGather | Jeel Thummar + Team | May 15–17, 2026

---

## CONFIRMED FACTS (verified)

| Item | Detail |
|------|--------|
| Hackathon dates | May 15–17, 2026 (48 hours) |
| Registration closes | May 15 at **7:00 AM ET = 12:00 PM IST** (ET in May = EDT = UTC-4) |
| Kickoff stream | May 15 at **8:00 AM PDT = 8:30 PM IST** → twitch.tv/lablabai |
| Submission deadline | May 17 at **8:00 AM PDT = 8:30 PM IST** |
| Prize pool | $10,000 ($5K / $3K / $2K) |
| Bob context window | **200,000 tokens max** — auto-condenses at 140,000 |
| Bobcoins (free trial) | **40 Bobcoins** per account. 1 Bobcoin = $0.50. Every token in AND out counts. |
| Hackathon likely provides | Extra Bob credits at kickoff — confirm immediately. |

> ⚠️ **Time zone correction**: The "7:00 AM ET = 12:30 PM IST" in the original guide is WRONG. May uses EDT (UTC-4), not EST (UTC-5). 7:00 AM EDT = **12:00 PM IST**, not 12:30.

---

## BOB FUNDAMENTALS — READ BEFORE TOUCHING THE KEYBOARD

This is the most important section. Bob is not Cursor. It's not Windsurf. It behaves differently in ways that will burn your Bobcoins and break your sessions if you don't understand them.

### How Bob works

Bob has 5 modes. You need to use the right one for each task or you'll waste tokens:

| Mode | When to use it | Token cost |
|------|---------------|------------|
| **Ask** | Understand repo structure, ask questions, explore — no file edits | Lower (read + browser only) |
| **Plan** | Design the approach before writing code — outputs markdown plan | Lower (read + markdown edit only) |
| **Code** | Actual implementation — writes and edits files | Medium |
| **Advanced** | Code + MCP tools (e.g. GitHub API calls from Bob) | Higher |
| **Orchestrator** | Break a complex multi-step task into subtasks, delegates to other modes | Variable |

**For this project:**
- Use **Ask** to explore tracer-cloud repo structure before writing prompts
- Use **Plan** to draft each stage's prompt architecture
- Use **Code** for the FastAPI backend, JSON schema, boilerplate
- Use **Advanced** only when you need Bob to call GitHub API via MCP directly
- Do NOT use Orchestrator unless you have Bobcoins to burn — it's powerful but expensive

### The context window reality

- **200k token limit.** Auto-condenses at 140k. When it condenses, it summarizes older context — you lose precision.
- **Every message sends the ENTIRE current context.** A 50k token context costs 50k tokens per message, not just the new message. This compounds fast.
- **Large files in `@mentions` are included every single turn.** If you `@tracer-cloud/src` (a big directory), you're paying for that on every message in the session.
- **Bobcoins deplete faster in long sessions.** A 10-message session with 80k context costs 800k tokens total. That's why short, focused sessions win.

### Context poisoning — the silent killer

Context poisoning is when bad data (a hallucination, an incorrect tool output, garbled logs) gets into the context and Bob starts reasoning from it. The symptoms are: nonsensical suggestions, Bob looping, tool calls that don't match what you asked for.

**The fix is NOT a corrective prompt. The fix is a new session.** There is no "reset" prompt — IBM confirmed this in their docs. If you notice Bob going sideways, don't keep sending messages trying to fix it. Start a new chat immediately, re-provide context cleanly.

This will happen during the hackathon. Don't panic. It's expected.

### .bobignore — use it

Create a `.bobignore` file in your project root before the hackathon. Exclude everything Bob doesn't need to reason about:

```
node_modules/
__pycache__/
.git/
*.log
*.env
venv/
dist/
build/
```

This alone will save meaningful Bobcoins by preventing Bob from accidentally loading massive irrelevant files.

### Custom rules — set them up in advance

Bob has a custom rules feature (`/.bob/rules/` directory). You can give Bob persistent instructions without burning context on every message. Before the hackathon, create a rules file for your project:

```
# ContribFlow Rules
- Always output structured JSON for stage results, never plain text
- When analyzing a GitHub repo, focus on Python files unless specified
- Confidence scores are traceability confidence (0.0–1.0), not code quality scores
- Never suggest modifications to test files unless explicitly asked
```

This runs once and doesn't cost per-message context the way inline instructions do.

---

## PROJECT: CONTRIBFLOW — WHAT IT ACTUALLY IS

Four-stage OSS contribution co-pilot. Each stage takes a GitHub repo URL or a diff as input and produces a structured JSON artifact. The demo is grounded in your real merged PRs.

```
Stage 1 — Gap Finder          → finds real contribution gaps (not doc typos)
Stage 2 — Idea Deduplication  → checks if your idea already exists in issues/PRs
Stage 3 — Change Impact       → blast radius analysis with confidence scores  ← YOUR STAGE
Stage 4 — Pre-PR Quality      → catches lint/bugs/convention violations before CI does
```

### What "powered by Bob" means in this context

Bob is not an API you call — it's an IDE. "Using Bob" for this project means:
1. You use Bob in the IDE to help build the FastAPI backend, write prompts, design the JSON schema
2. You also use Bob's reasoning capabilities to actually run the analysis logic — i.e., you feed it a repo or diff and use Bob sessions to produce the structured output that becomes the product's demo
3. You export these Bob sessions as the evidence of usage

The product itself is the FastAPI app + frontend. Bob is both the tool that built it AND the reasoning engine behind the core analysis. Both need to show up in your session exports.

---

## TEAM DIVISION

| Member | Stage | Bob Role | Primary Mode |
|--------|-------|----------|--------------|
| **Jeel** | Stage 3 — Change Impact + overall Bob prompt architecture | Impact tracing sessions on tracer-cloud | Plan → Code → Ask |
| Member 2 | Stage 2 — Idea Dedup + GitHub API integration | Deduplication sessions | Code → Advanced (if MCP) |
| Member 3 | Stage 1 — Gap Finder | Gap analysis sessions | Ask → Plan → Code |
| Member 4 | Stage 4 — Pre-PR Quality Check + Frontend | Quality check sessions | Code |

Each member handles their own Bobcoin budget. Each member exports their own session report. Commit all 4 to `/bob-sessions/` in the repo.

---

## BOBCOIN BUDGET — PLAN THIS SERIOUSLY

40 Bobcoins free trial. At 1 Bobcoin = $0.50, that's $20 worth of compute per account.

You do NOT know what a Bobcoin actually costs in tokens (IBM abstracts it). But based on the context window math, long sessions eat them fast. Here's how to budget:

**Per-member allocation (40 coins each):**
- 10 coins: Pre-hackathon exploration and prompt testing (May 12–14)
- 20 coins: Hackathon Day 1 — building and iterating your stage
- 8 coins: Hackathon Day 2 — polish, demo run-through
- 2 coins: Reserve for re-running the final demo for recording

**Rules to stay in budget:**
1. Never `@` a full directory. Only `@` specific files or line ranges.
2. New session every time you switch focus (don't mix "explore repo" with "write API endpoint" in one chat).
3. If a session hits 100k tokens (visible in top-right), kill it. Summarize the output in a fresh session.
4. Ask and Plan modes are cheaper than Code and Advanced. Use them for reasoning. Use Code only to actually write.
5. Do NOT run exploratory "what if" questions in a Code session. Use Ask.

> ⚠️ At kickoff, IBM may give you additional Bobcoins for the hackathon. Check immediately. If they do, adjust budget accordingly. If they don't, the 4-account split is your safety net.

---

## PHASE 0 — PREP (Today, May 14)

You're late on earlier prep items. Here's what matters TODAY before 8:30 PM IST tomorrow:

### Tonight (May 14)
- [ ] All 4 members: sign up at bob.ibm.com, start free trial, download Bob IDE
- [ ] Spend 20 min in Bob — enough to know where the mode switcher is, what a session looks like, and how to export. Don't explore tracer-cloud yet (save coins).
- [ ] Create GitHub repo: public, MIT license, add `/bob-sessions/` folder, add `.bobignore`
- [ ] Create `/.bob/rules/contribflow.md` with project rules (see above)
- [ ] Everyone individually registered on lablab.ai
- [ ] Finalize and commit JSON schema for all 4 stages' outputs. This cannot change during the hackathon without breaking things.

### JSON Schema (agree on this tonight)

```json
// Stage 1 — Gap
{ "gaps": [{ "title": "", "file": "", "impact": "high|medium|low", "reasoning": "" }] }

// Stage 2 — Dedup  
{ "status": "clear|conflict", "conflicts": [{ "issue_url": "", "similarity": 0.0, "summary": "" }] }

// Stage 3 — Change Impact
{ "files_affected": [], "services_at_risk": [], "tests_to_update": [], 
  "findings": [{ "finding": "", "confidence": 0.0, "type": "direct|indirect|dynamic" }],
  "suggested_order": [] }

// Stage 4 — Pre-PR
{ "issues": [{ "severity": "error|warning|info", "file": "", "line": "", "issue": "", "fix": "" }],
  "passes_check": true }
```

---

## PHASE 1 — DAY 1 (May 15)

### Before 7:30 PM IST
Lock team. Registration closes at 12:00 PM IST (7:00 AM EDT). This is earlier than the guide says. Don't miss it.

### 8:30 PM IST — Kickoff
Watch the stream. The moment it's done, check email for:
1. Hackathon guide (has Bob session export instructions — do not skip reading this)
2. Any extra Bobcoins / Bob access credentials
3. Confirmation that multi-account usage is allowed

If multi-account is NOT allowed, consolidate to one account immediately. Priority order: Stage 2 (dedup) → Stage 3 (impact) → Stage 4 (quality check) → Stage 1 (gap finder). Build in this order.

---

### Hour 0–3 (8:30 PM – 11:30 PM IST)

**All members simultaneously:**

- [ ] Read hackathon guide fully — both of you, not just one
- [ ] Confirm Bob session export process. Screenshot the instructions.
- [ ] GitHub repo: confirm all 4 members have push access
- [ ] Start Bob sessions — one session per stage, use **Ask mode first**

**Jeel (Stage 3):**
Open tracer-cloud in Bob. Ask mode. Ask:

```
@/tracer-cloud/[relevant dir] 
Give me a dependency map of this codebase. For each major module, list:
1. Files it depends on
2. Files that depend on it  
3. Any dynamic imports or runtime-loaded dependencies
Format as JSON.
```

This is your recon session. Save the output. It becomes the input for your Stage 3 prompt.

**Member 2 (Stage 2 + backend):**
Build the GitHub API layer first. This is the dependency everything else needs.

FastAPI endpoints needed:
```
GET /repo/issues?url={repo_url}&state=open|closed|all
GET /repo/prs?url={repo_url}&state=open|closed|all
GET /repo/tree?url={repo_url}
GET /repo/commits?url={repo_url}&limit=50
```

Use your GitHub personal access token. Standard REST API, nothing Bob-specific here. Get this working before anything else.

---

### Hour 3–15 (11:30 PM May 15 – 11:30 AM May 16)

**Build order matters. Do Stage 2 first — it validates the GitHub API layer and is the most self-contained.**

#### Stage 2 — Idea Deduplication (Member 2, hours 3–8)

Bob prompt template for Stage 2:

```
You are analyzing whether a proposed OSS contribution idea already exists.

Contribution idea: {user_idea}

Existing issues (JSON): {issues_json}
Existing PRs (JSON): {prs_json}

Task:
1. Semantically compare the contribution idea against each issue and PR
2. "Add retry logic" matches "implement exponential backoff" — understand intent, not just keywords
3. For each overlap found, note: URL, similarity score (0.0–1.0), one-line summary of overlap
4. Return ONLY valid JSON in this exact schema:
{"status": "clear|conflict", "conflicts": [...]}

Do not include any explanation outside the JSON.
```

Run this in **Ask mode** (cheaper, no file writes needed). Feed it the GitHub API output.

Test it on tracer-cloud with a fake idea: "Add retry logic to the HTTP client." See what it finds.

#### Stage 3 — Change Impact (Jeel, hours 3–10)

This is your most important stage. The demo depends on it being accurate against PR #1395.

First, manually review PR #1395 in tracer-cloud. Know exactly:
- Which files it touched
- Which tests were affected
- What reviewers said about impact

Then build your Bob prompt:

```
You are analyzing the blast radius of a proposed change.

Repo dependency map: {dependency_map}  ← from your recon session
Proposed change description: {change_description}
Relevant files (to load with @): {targeted_files}

Task:
1. Identify ALL files that would need to change — direct changes only
2. Identify downstream files that import or call the changed code
3. Identify tests that cover the changed code
4. Flag any dynamic imports or runtime dependencies (these get confidence: 0.3)
5. For each finding, assign confidence (0.0–1.0) based on HOW CERTAIN you are it's affected:
   - Direct function call in file: 0.9+
   - Imported but usage unclear: 0.6
   - Dynamic import / runtime: 0.3
6. Return ONLY valid JSON matching this schema:
{"files_affected": [], "services_at_risk": [], "tests_to_update": [], 
 "findings": [{"finding": "", "confidence": 0.0, "type": "direct|indirect|dynamic"}],
 "suggested_order": []}
```

**Critical for the demo:** Run this against PR #1395's change description. Compare Bob's output to what the PR actually touched. The closer they match, the stronger your demo moment. Iterate the prompt until they match well. This is worth spending 2–3 Bob sessions on.

**What to do if Bob's output is wrong:**
- Don't add more instructions to the same session (context poisoning risk)
- Start new session, refine the prompt, feed the same input
- Keep a text file of prompt versions and their accuracy against the ground truth PR

#### Stage 1 — Gap Finder (Member 3, hours 5–12)

Bob prompt:

```
You are analyzing an open source repository for meaningful contribution gaps.

Repo structure: {repo_tree}
Recent commits (last 30): {commits_json}
Open issues: {issues_json}

Task — identify real contribution gaps. NOT documentation typos. Real gaps:
- Modules with no error handling that are called frequently  
- Functions with no test coverage in core paths
- Deprecated dependencies with no migration path
- Undocumented public APIs that external code depends on
- Obvious missing features noted in TODOs/FIXMEs in core files

For each gap, provide:
- Title (one line)
- File path
- Impact: high|medium|low
- Reasoning (2-3 sentences, grounded in the actual code)

Return ONLY valid JSON: {"gaps": [...]}
```

Use **Plan mode** to refine the prompt structure, then **Ask mode** to run it (since it's reading files, not writing them).

#### Stage 4 — Pre-PR Quality Check (Member 4, hours 5–12)

Bob prompt:

```
You are reviewing a git diff before PR submission.

Repository conventions (sample files for context):
@/[2-3 representative source files from the repo]

Git diff:
{diff_text}

Task:
1. Check for unused imports
2. Check for obvious logic bugs or unhandled edge cases
3. Check for violations of the repo's naming/style conventions (inferred from context files)
4. Check for missing error handling in new code paths
5. Flag anything that would fail standard CI lint checks

For each issue, provide severity (error|warning|info), file, approximate line, issue description, and suggested fix.
Return ONLY valid JSON: {"issues": [...], "passes_check": true|false}
```

This one is straightforward but the quality depends heavily on which context files you provide. Provide 2–3 files that represent the repo's coding style — NOT large files. Target files similar in nature to what the diff touches.

---

### Hour 15–24 (11:30 AM – 8:30 PM IST, May 16)

- [ ] All 4 stages producing JSON output end-to-end
- [ ] FastAPI routes wired up: each stage has a `/stage/{n}` POST endpoint
- [ ] Integration test: feed tracer-cloud URL → Stage 1 → Stage 2 (with fake idea) → Stage 3 (PR #1395 description) → Stage 4 (PR #1395 diff)
- [ ] Stage 3 ground truth check: Bob's output vs. what PR #1395 actually touched. If it's not matching well enough, iterate ONE MORE TIME before Day 2.
- [ ] Start recording Bob session screenshots now — not later

---

## PHASE 2 — DAY 2 (May 16–17)

### Hour 24–36 (8:30 PM May 16 – 8:30 AM May 17 IST)

- [ ] Polish JSON outputs — clean, parseable, no garbage fields
- [ ] Frontend: Streamlit is faster than React to get working in 48 hours. Use it unless Member 4 is fast with React. A working Streamlit beats a broken React every time.
  - Input: GitHub repo URL + optional contribution idea + optional diff
  - Tabs for each stage
  - Clean display of the JSON output (not raw JSON — rendered)
  - Export to Markdown button
- [ ] Error handling: what happens if the GitHub API rate-limits? What if Bob returns invalid JSON? Handle both.
- [ ] For Stage 3: show a side-by-side of "Bob's predicted impact" vs "what actually happened in PR #1395"

### Hour 36–42 (8:30 AM – 2:30 PM IST, May 17)

#### Recording the demo video (3–5 min)

This is how you win. Do not wing this. Script it.

**Script outline:**

```
0:00 – 0:20: "OSS contribution is painful at every stage. 
              ContribFlow fixes that with 4 stages, powered by IBM Bob."

0:20 – 0:50: Stage 1 — "Here's tracer-cloud. Bob found [X] real gaps. 
              Not typos. This one: [specific gap]. Here's why it matters."

0:50 – 1:30: Stage 2 — "I have a contribution idea: [idea]. 
              Bob checks 200 issues and PRs for semantic overlap. 
              Result: [clear/conflict]. Here's why."

1:30 – 3:00: Stage 3 (THE KILLER MOMENT) — 
              "This is PR #1395. It touched [list of files].
              Before writing a line, we fed the change description to Bob.
              Here's what Bob predicted. [show output]
              Here's what the PR actually touched. [show PR]
              They match. Bob predicted the blast radius before we wrote the code."

3:00 – 3:45: Stage 4 — "Before submitting, feed your diff to Bob.
              It catches [specific issue] that would have failed CI."

3:45 – 4:00: "Four stages. One pipeline. No more surprised maintainers."
```

**Recording rules:**
- Bob IDE must be visible on screen at all times during stages
- Zoom in on the Bob chat panel when Bob is reasoning
- Show the token counter in the top-right (this demonstrates real Bob usage)
- Have the session already running before you hit record — don't show setup
- Record in 1080p minimum

### Hour 42–46 (2:30 PM – 6:30 PM IST, May 17)

#### Bob session exports

Each member exports their Bob session report. The hackathon guide (released at kickoff) will have exact export steps. Expected process based on Bob docs:
- Go to session history in Bob IDE
- Export to PDF or JSON (confirm format at kickoff)
- Commit to `/bob-sessions/member-name-stage-N.pdf` in repo

Do this BEFORE writing the pitch deck. Don't run out of time on exports.

#### Pitch deck (5–6 slides)

```
Slide 1: Title — ContribFlow. One-liner. Team name.
Slide 2: Problem — contributing to OSS is painful at every stage. 3 bullet points.
Slide 3: Solution — 4-stage pipeline diagram. One line per stage.
Slide 4: How Bob is used — explicit. "Bob does X in Stage 2. Bob does Y in Stage 3." Judges check this.
Slide 5: Demo screenshot — Stage 3, side-by-side of Bob prediction vs actual PR.
Slide 6: Business value — "saves N hours per contribution" / who buys this.
```

Keep it plain. Judges read 50 decks. No decorative nonsense.

### Hour 46–48 (6:30 PM – 8:30 PM IST, May 17)

- [ ] Fill lablab.ai submission form
  - Be specific about Bob usage: "Bob's Ask mode analyzed repo structure, Plan mode designed stage prompts, Code mode built the FastAPI endpoints. Bob session exports in /bob-sessions/."
  - Don't write "We used Bob to build our app." That's not specific enough.
- [ ] Video link: YouTube unlisted or Loom
- [ ] GitHub repo: confirm it's public, MIT license is in root, all 4 Bob session reports are committed
- [ ] Submit at hour 46, not hour 48. Buffer exists for a reason.

---

## COMPLETE SUBMISSION CHECKLIST

- [ ] Public GitHub repo with MIT license in root
- [ ] `/bob-sessions/` — all 4 members' exported session reports
- [ ] Demo video (3–5 min) — Bob IDE visible, all 4 stages shown
- [ ] Pitch deck (5–6 slides) — includes explicit Bob usage description
- [ ] Working prototype — all 4 stages functional end-to-end
- [ ] lablab.ai submission form filled — Bob usage described specifically

**Disqualification risks:**
- No meaningful Bob usage shown → disqualified
- Missing Bob session exports → likely disqualified
- Private repo or missing MIT license → disqualified  
- Missed deadline → disqualified
- Teammate not individually registered on lablab.ai → problem

---

## WHAT NOT TO DO

**Don't do these things. They will cost you coins or lose you the hackathon.**

1. **Don't `@` entire directories.** `@/src` on tracer-cloud loads the whole codebase into context on every message. Use `@/src/specific_file.py:40-80` instead.

2. **Don't mix tasks in one Bob session.** One session per focused task. Mixing "explore the repo" with "write the endpoint" bloats context and confuses Bob.

3. **Don't try to fix a broken Bob session with more prompts.** If Bob starts producing garbage, start a new session. No corrective prompt reliably fixes a poisoned context.

4. **Don't use Orchestrator mode unless you understand what it costs.** It's powerful but it delegates to other modes, each of which burns its own tokens. Reserve it for genuinely multi-step orchestration if you have coins to spare.

5. **Don't skip the `.bobignore`.** Without it, Bob might accidentally load `node_modules/` or your full virtual environment into context.

6. **Don't paste entire GitHub API responses into Bob.** If an issue list has 300 issues, trim it to the relevant fields (`number`, `title`, `body`, `state`, `created_at`) before sending. Raw API responses are token-heavy.

7. **Don't record your demo at the last minute.** Record it at hour 36–38 when you still have time to re-record if something goes wrong.

8. **Don't use Claude Code or other tools for the core Bob reasoning work.** Your session exports will show gaps. Judges will notice.

---

## WHAT TO DO IF THINGS GO WRONG

| Problem | What to do |
|---------|-----------|
| Bob output is wrong/hallucinating | New session. Refine prompt. Don't try to fix in-session. |
| Bobcoins running out | Switch to Ask mode (cheapest). Cut scope to Stage 2 + Stage 3 only. |
| Stage 3 doesn't match PR #1395 well | Narrow the context files you provide. Less is often more precise. |
| GitHub API rate limit | Add `time.sleep(1)` between calls. Use a GitHub token with higher rate limits. |
| Multi-account rule issue at kickoff | Drop Stages 1 and 4 immediately. Do 2 and 3 well on one account. |
| Bob session export is missing a stage | Recreate a demo session showing that stage's reasoning. It doesn't have to be the exact build session — it has to show Bob reasoning through the problem. |
| Demo video has no time for all 4 stages | Cut Stage 1 (weakest differentiator). Keep 2, 3, 4 in video. |

---

## KEY LINKS

| Resource | Link |
|----------|------|
| Hackathon page | lablab.ai/ai-hackathons/ibm-bob-hackathon |
| Your team | lablab.ai/ai-hackathons/ibm-bob-hackathon/chaintogather |
| IBM Bob | bob.ibm.com |
| Bob docs | bob.ibm.com/docs/ide |
| Bob context window docs | bob.ibm.com/docs/ide/core-concepts/context-window-management |
| Bob modes docs | bob.ibm.com/docs/ide/features/modes |
| Bob context poisoning docs | bob.ibm.com/docs/ide/core-concepts/context-poisoning |
| Bob Bobcoins docs | bob.ibm.com/docs/ide/account/bobcoins |
| Bob download | bob.ibm.com/download |
| lablab Discord | lablab.ai/discord |
| Kickoff stream | twitch.tv/lablabai |
| Demo repo | github.com/opensre/tracer-cloud |

---

## TIME ZONE CHEAT SHEET (CORRECTED)

| Event | Time | IST |
|-------|------|-----|
| Registration closes | May 15 — 7:00 AM EDT | May 15 — **12:00 PM IST** |
| Kickoff stream starts | May 15 — 8:00 AM PDT | May 15 — **8:30 PM IST** |
| Submission deadline | May 17 — 8:00 AM PDT | May 17 — **8:30 PM IST** |

Note: EDT = UTC-4 (East Coast in May). PDT = UTC-7 (West Coast in May).
