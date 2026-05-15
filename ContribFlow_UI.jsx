import { useState, useCallback } from "react";

const API = "http://localhost:8000/api";

// ─── Design tokens ────────────────────────────────────────────────
const T = {
  bg:      "#0D1117",
  surface: "#161B22",
  border:  "#21262D",
  borderHover: "#30363D",
  text:    "#E6EDF3",
  muted:   "#7D8590",
  dim:     "#484F58",
  blue:    "#388BFD",
  blueGlow:"#1F6FEB22",
  cyan:    "#39C5CF",
  amber:   "#D29922",
  red:     "#F85149",
  green:   "#3FB950",
  purple:  "#A371F7",
  mono:    "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  sans:    "'Inter', 'Segoe UI', system-ui, sans-serif",
};

// ─── Reusable primitives ───────────────────────────────────────────
const Badge = ({ color = T.muted, children, style = {} }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 500,
    letterSpacing: "0.04em", textTransform: "uppercase",
    background: color + "22", color, border: `1px solid ${color}44`,
    fontFamily: T.sans, ...style
  }}>{children}</span>
);

const Chip = ({ label, value, color = T.blue, icon }) => (
  <div style={{
    background: T.surface, border: `1px solid ${T.border}`,
    borderRadius: 8, padding: "12px 16px", flex: 1, minWidth: 0
  }}>
    <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans,
      textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
      {icon && <span style={{ marginRight: 5 }}>{icon}</span>}{label}
    </div>
    <div style={{ fontSize: 26, fontWeight: 600, color, fontFamily: T.mono }}>{value}</div>
  </div>
);

const ConfBar = ({ confidence, type }) => {
  const color = type === "direct" ? T.cyan : type === "indirect" ? T.amber : T.red;
  const pct = Math.round(confidence * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
      <div style={{ flex: 1, height: 4, background: T.border, borderRadius: 2, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color,
          borderRadius: 2, transition: "width 0.6s ease" }} />
      </div>
      <span style={{ fontSize: 11, color, fontFamily: T.mono, minWidth: 32,
        textAlign: "right", fontWeight: 600 }}>{pct}%</span>
      <Badge color={color} style={{ fontSize: 10, padding: "1px 6px" }}>{type}</Badge>
    </div>
  );
};

const FileChip = ({ path }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "2px 8px", borderRadius: 4, fontSize: 11,
    background: "#21262D", color: T.cyan, fontFamily: T.mono,
    border: `1px solid ${T.border}`, margin: "2px",
    userSelect: "all", cursor: "text"
  }}>
    <span style={{ opacity: 0.5 }}>›</span>{path}
  </span>
);

const Spinner = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 10, color: T.muted,
    padding: "32px 0", justifyContent: "center", fontFamily: T.sans, fontSize: 13 }}>
    <div style={{
      width: 16, height: 16, borderRadius: "50%",
      border: `2px solid ${T.border}`, borderTopColor: T.blue,
      animation: "spin 0.8s linear infinite"
    }} />
    <span>Bob is analyzing…</span>
  </div>
);

// ─── Stage 1: Gap Finder ───────────────────────────────────────────
function GapFinder({ repoUrl }) {
  const [focus, setFocus] = useState("any");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await fetch(`${API}/stage1/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, focus_area: focus })
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const impactColor = { high: T.red, medium: T.amber, low: T.green };
  const categoryLabel = { "error-handling": "Error handling", "test-coverage": "Test coverage",
    "documentation": "Docs", "missing-feature": "Missing feature", "deprecated-dependency": "Deprecated dep" };

  return (
    <div>
      <div style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "flex-end" }}>
        <div style={{ flex: 1 }}>
          <label style={labelStyle}>Focus area</label>
          <select value={focus} onChange={e => setFocus(e.target.value)} style={selectStyle}>
            <option value="any">Any gap</option>
            <option value="error-handling">Error handling</option>
            <option value="test-coverage">Test coverage</option>
            <option value="missing-feature">Missing features</option>
            <option value="deprecated-dependency">Deprecated deps</option>
          </select>
        </div>
        <button onClick={analyze} disabled={!repoUrl || loading} style={primaryBtn}>
          Find gaps
        </button>
      </div>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}
      {result && (
        <div>
          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <Chip label="High impact" value={result.summary?.high_count ?? 0} color={T.red} />
            <Chip label="Medium" value={result.summary?.medium_count ?? 0} color={T.amber} />
            <Chip label="Low" value={result.summary?.low_count ?? 0} color={T.green} />
            <Chip label="Files scanned" value={result.files_analyzed ?? 0} color={T.muted} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {(result.gaps || []).map(gap => (
              <GapCard key={gap.id} gap={gap}
                impactColor={impactColor} categoryLabel={categoryLabel} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function GapCard({ gap, impactColor, categoryLabel }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ ...cardStyle, borderLeft: `3px solid ${impactColor[gap.impact] || T.muted}` }}>
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", gap: 12, cursor: "pointer" }}
        onClick={() => setOpen(o => !o)}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 500, color: T.text, fontFamily: T.sans,
            fontSize: 14, marginBottom: 4 }}>{gap.title}</div>
          <div style={{ fontFamily: T.mono, fontSize: 11, color: T.cyan }}>
            {gap.file}{gap.line_range ? `:${gap.line_range}` : ""}
          </div>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
          <Badge color={impactColor[gap.impact]}>{gap.impact}</Badge>
          <Badge color={T.muted}>{categoryLabel[gap.category] || gap.category}</Badge>
          {gap.good_first_issue &&
            <Badge color={T.green}>Good first issue</Badge>}
          <span style={{ color: T.muted, fontSize: 12 }}>{open ? "▲" : "▼"}</span>
        </div>
      </div>
      {open && (
        <div style={{ marginTop: 12, borderTop: `1px solid ${T.border}`, paddingTop: 12 }}>
          <div style={{ fontSize: 13, color: T.text, fontFamily: T.sans,
            lineHeight: 1.6, marginBottom: 10 }}>{gap.reasoning}</div>
          {gap.evidence && (
            <div style={{ fontFamily: T.mono, fontSize: 11, color: T.amber,
              background: "#21262D", padding: "6px 10px", borderRadius: 4,
              borderLeft: `2px solid ${T.amber}` }}>
              <span style={{ color: T.muted, marginRight: 6 }}>evidence</span>
              {gap.evidence}
            </div>
          )}
          <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 11, color: T.muted, fontFamily: T.sans }}>
              Effort: <span style={{ color: T.text }}>{gap.estimated_effort || "unknown"}</span>
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Stage 2: Idea Deduplication ──────────────────────────────────
function IdeaDedup({ repoUrl }) {
  const [idea, setIdea] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const check = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await fetch(`${API}/stage2/deduplicate`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, idea })
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const statusColor = { clear: T.green, conflict: T.red, partial_overlap: T.amber };
  const statusLabel = { clear: "Safe to proceed", conflict: "Conflict found", partial_overlap: "Partial overlap" };

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Your contribution idea</label>
        <textarea
          value={idea}
          onChange={e => setIdea(e.target.value)}
          placeholder="Add retry logic with exponential backoff to the HTTP client so failed requests are retried up to 3 times before raising an exception."
          rows={3}
          style={textareaStyle}
        />
        <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans, marginTop: 4 }}>
          Plain English. Don't worry about technical precision — describe the goal.
        </div>
      </div>
      <button onClick={check} disabled={!repoUrl || !idea.trim() || loading} style={primaryBtn}>
        Check for duplicates
      </button>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}
      {result && (
        <div style={{ marginTop: 20 }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 12,
            padding: "16px 20px", borderRadius: 8,
            background: (statusColor[result.status] || T.muted) + "11",
            border: `1px solid ${(statusColor[result.status] || T.muted)}33`,
            marginBottom: 16
          }}>
            <div style={{
              width: 10, height: 10, borderRadius: "50%",
              background: statusColor[result.status] || T.muted, flexShrink: 0
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 15, fontFamily: T.sans,
                color: statusColor[result.status] || T.muted }}>
                {statusLabel[result.status] || result.status}
              </div>
              {result.recommendation_text && (
                <div style={{ fontSize: 13, color: T.muted, fontFamily: T.sans, marginTop: 2 }}>
                  {result.recommendation_text}
                </div>
              )}
            </div>
            {result.checked_against && (
              <div style={{ fontSize: 11, color: T.dim, fontFamily: T.sans, textAlign: "right" }}>
                Checked {Object.values(result.checked_against).reduce((a,b) => a+b, 0)} items
              </div>
            )}
          </div>

          {(result.conflicts || []).map(c => (
            <div key={c.number} style={{
              ...cardStyle,
              borderLeft: `3px solid ${c.type === "pr" ? T.purple : T.blue}`
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 6 }}>
                    <Badge color={c.type === "pr" ? T.purple : T.blue}>
                      {c.type === "pr" ? "PR" : "Issue"} #{c.number}
                    </Badge>
                    {c.state && <Badge color={c.state === "open" ? T.green : T.muted}>{c.state}</Badge>}
                    {c.assigned && <Badge color={T.amber}>Assigned → {c.assignee}</Badge>}
                  </div>
                  <a href={c.url} target="_blank" rel="noreferrer"
                    style={{ color: T.text, fontFamily: T.sans, fontSize: 14,
                      fontWeight: 500, textDecoration: "none" }}>
                    {c.title}
                    <span style={{ color: T.blue, marginLeft: 4, fontSize: 11 }}>↗</span>
                  </a>
                  <div style={{ fontSize: 13, color: T.muted, fontFamily: T.sans,
                    marginTop: 6, lineHeight: 1.5 }}>{c.summary}</div>
                </div>
                <div style={{ flexShrink: 0, textAlign: "center" }}>
                  <div style={{ fontSize: 22, fontWeight: 700, color: T.red,
                    fontFamily: T.mono }}>{Math.round(c.similarity * 100)}%</div>
                  <div style={{ fontSize: 10, color: T.muted, fontFamily: T.sans }}>match</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Stage 3: Change Impact (core) ────────────────────────────────
function ChangeImpact({ repoUrl }) {
  const [desc, setDesc] = useState("");
  const [diff, setDiff] = useState("");
  const [showDiff, setShowDiff] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [openFinding, setOpenFinding] = useState(null);

  const analyze = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await fetch(`${API}/stage3/impact`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, change_description: desc, diff: diff || undefined })
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>Describe your change</label>
        <textarea
          value={desc}
          onChange={e => setDesc(e.target.value)}
          placeholder="Modify the retry function in http_client.py to use exponential backoff instead of a fixed 1-second interval. The new behavior retries up to 3 times with delays of 1s, 2s, and 4s."
          rows={3}
          style={textareaStyle}
        />
        <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans, marginTop: 4 }}>
          Describe the goal. You don't need to know which files are affected — that's what this finds.
        </div>
      </div>

      <button
        onClick={() => setShowDiff(s => !s)}
        style={{ ...ghostBtn, marginBottom: 16 }}>
        {showDiff ? "▼ Hide diff" : "▶ Paste git diff (optional, improves accuracy)"}
      </button>
      {showDiff && (
        <textarea
          value={diff}
          onChange={e => setDiff(e.target.value)}
          placeholder="Paste output of: git diff HEAD"
          rows={6}
          style={{ ...textareaStyle, fontFamily: T.mono, fontSize: 11, marginBottom: 16 }}
        />
      )}

      <button onClick={analyze} disabled={!repoUrl || !desc.trim() || loading} style={primaryBtn}>
        Analyze blast radius
      </button>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}

      {result && (
        <div style={{ marginTop: 20 }}>
          {/* Analysis mode badge */}
          <div style={{ display: "flex", gap: 8, marginBottom: 16, alignItems: "center" }}>
            <Badge color={result.analysis_mode === "diff" ? T.green : T.amber}>
              {result.analysis_mode === "diff" ? "Diff-based analysis" : "Description-based analysis"}
            </Badge>
            {result.has_dynamic_risks && (
              <Badge color={T.red}>Dynamic risks detected</Badge>
            )}
          </div>

          {/* Metrics row */}
          <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
            <Chip label="Files affected"
              value={result.files_affected?.length ?? 0} color={T.cyan} />
            <Chip label="Services at risk"
              value={result.services_at_risk?.length ?? 0} color={T.amber} />
            <Chip label="Tests to update"
              value={result.tests_to_update?.length ?? 0} color={T.purple} />
            <Chip label="Findings"
              value={result.findings?.length ?? 0} color={T.blue} />
          </div>

          {/* Two-column layout: findings + order */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 16 }}>
            {/* Findings */}
            <div>
              <SectionTitle>Findings</SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(result.findings || []).map((f, i) => (
                  <div key={f.id || i}
                    style={{
                      ...cardStyle,
                      cursor: "pointer",
                      borderLeft: `3px solid ${
                        f.type === "direct" ? T.cyan :
                        f.type === "indirect" ? T.amber : T.red
                      }`
                    }}
                    onClick={() => setOpenFinding(openFinding === i ? null : i)}>
                    <div style={{ fontSize: 13, color: T.text, fontFamily: T.sans,
                      lineHeight: 1.5, marginBottom: 8 }}>{f.finding}</div>
                    <ConfBar confidence={f.confidence} type={f.type} />
                    {openFinding === i && f.evidence_files?.length > 0 && (
                      <div style={{ marginTop: 10, borderTop: `1px solid ${T.border}`, paddingTop: 10 }}>
                        <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans,
                          marginBottom: 6 }}>Evidence files</div>
                        <div>{f.evidence_files.map(p => <FileChip key={p} path={p} />)}</div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Affected files */}
              {result.files_affected?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <SectionTitle>Files affected</SectionTitle>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {result.files_affected.map(p => <FileChip key={p} path={p} />)}
                  </div>
                </div>
              )}

              {/* Tests */}
              {result.tests_to_update?.length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <SectionTitle>Tests to update</SectionTitle>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {result.tests_to_update.map(p => <FileChip key={p} path={p} />)}
                  </div>
                </div>
              )}
            </div>

            {/* Suggested order (right panel) */}
            <div>
              <div style={{
                background: T.surface, border: `1px solid ${T.border}`,
                borderRadius: 8, padding: 16, position: "sticky", top: 16
              }}>
                <SectionTitle>Suggested order</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {(result.suggested_order || []).map((step, i) => (
                    <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                      <div style={{
                        width: 20, height: 20, borderRadius: "50%", flexShrink: 0,
                        background: T.blueGlow, border: `1px solid ${T.blue}44`,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 10, fontWeight: 600, color: T.blue, fontFamily: T.mono
                      }}>{i + 1}</div>
                      <div style={{ fontSize: 12, color: T.text, fontFamily: T.sans,
                        lineHeight: 1.5, paddingTop: 2 }}>{step}</div>
                    </div>
                  ))}
                </div>

                {result.confidence_explanation && (
                  <div style={{
                    marginTop: 16, paddingTop: 12, borderTop: `1px solid ${T.border}`,
                    fontSize: 11, color: T.dim, fontFamily: T.sans, lineHeight: 1.5
                  }}>{result.confidence_explanation}</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Stage 4: Pre-PR Quality Check ────────────────────────────────
function PrePR({ repoUrl }) {
  const [diff, setDiff] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const review = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const r = await fetch(`${API}/stage4/review`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: repoUrl, diff })
      });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const sevColor = { error: T.red, warning: T.amber, info: T.blue };
  const sevIcon  = { error: "✕", warning: "!", info: "i" };

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <label style={labelStyle}>Git diff</label>
        <textarea
          value={diff}
          onChange={e => setDiff(e.target.value)}
          placeholder={"Paste the output of:\n  git diff HEAD\nor\n  git diff main"}
          rows={8}
          style={{ ...textareaStyle, fontFamily: T.mono, fontSize: 11 }}
        />
        <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans, marginTop: 4 }}>
          Bob will check your diff against the repo's existing code conventions.
        </div>
      </div>
      <button onClick={review} disabled={!repoUrl || !diff.trim() || loading} style={primaryBtn}>
        Review before PR
      </button>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}

      {result && (
        <div style={{ marginTop: 20 }}>
          {/* Pass/Fail header */}
          <div style={{
            display: "flex", alignItems: "center", gap: 14,
            padding: "16px 20px", borderRadius: 8, marginBottom: 20,
            background: (result.passes_check ? T.green : T.red) + "11",
            border: `1px solid ${(result.passes_check ? T.green : T.red)}33`
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%", flexShrink: 0,
              background: (result.passes_check ? T.green : T.red) + "22",
              border: `1.5px solid ${result.passes_check ? T.green : T.red}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 14, color: result.passes_check ? T.green : T.red
            }}>{result.passes_check ? "✓" : "✕"}</div>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16, fontFamily: T.sans,
                color: result.passes_check ? T.green : T.red }}>
                {result.passes_check ? "Ready to submit" : "Issues found"}
              </div>
              <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans }}>
                {result.summary}
              </div>
            </div>
            {result.convention_files_used?.length > 0 && (
              <div style={{ marginLeft: "auto", fontSize: 11, color: T.dim,
                fontFamily: T.sans, textAlign: "right" }}>
                Conventions learned from:<br />
                {result.convention_files_used.map(f => (
                  <span key={f} style={{ color: T.cyan, display: "block" }}>{f}</span>
                ))}
              </div>
            )}
          </div>

          {/* Issues */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(result.issues || []).map(issue => (
              <div key={issue.id}
                style={{ ...cardStyle, borderLeft: `3px solid ${sevColor[issue.severity] || T.muted}` }}>
                <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <div style={{
                    width: 18, height: 18, borderRadius: "50%", flexShrink: 0,
                    background: (sevColor[issue.severity] || T.muted) + "22",
                    border: `1px solid ${(sevColor[issue.severity] || T.muted)}66`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, fontWeight: 700, color: sevColor[issue.severity] || T.muted,
                    marginTop: 1
                  }}>{sevIcon[issue.severity] || "?"}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: 8, alignItems: "center",
                      marginBottom: 4, flexWrap: "wrap" }}>
                      <span style={{ fontFamily: T.mono, fontSize: 11, color: T.cyan }}>
                        {issue.file}:{issue.line}
                      </span>
                      <Badge color={sevColor[issue.severity] || T.muted}>{issue.severity}</Badge>
                      {issue.source === "static" &&
                        <Badge color={T.dim}>Static check</Badge>}
                    </div>
                    <div style={{ fontSize: 13, color: T.text, fontFamily: T.sans,
                      lineHeight: 1.5, marginBottom: 8 }}>{issue.issue}</div>
                    <div style={{
                      fontFamily: T.mono, fontSize: 11, color: T.green,
                      background: "#21262D", padding: "6px 10px", borderRadius: 4,
                      borderLeft: `2px solid ${T.green}`
                    }}>
                      <span style={{ color: T.muted, marginRight: 6 }}>fix →</span>
                      {issue.fix}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Convention notes */}
          {result.convention_notes?.length > 0 && (
            <div style={{
              marginTop: 16, padding: "12px 16px", borderRadius: 8,
              background: T.surface, border: `1px solid ${T.border}`
            }}>
              <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans,
                textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>
                Conventions Bob learned from this repo
              </div>
              {result.convention_notes.map((n, i) => (
                <div key={i} style={{ fontSize: 12, color: T.dim, fontFamily: T.sans,
                  marginBottom: 4, paddingLeft: 12, borderLeft: `2px solid ${T.border}` }}>
                  {n}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Shared small components ───────────────────────────────────────
function SectionTitle({ children }) {
  return (
    <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans,
      textTransform: "uppercase", letterSpacing: "0.06em",
      marginBottom: 10, fontWeight: 500 }}>{children}</div>
  );
}

function ErrorBox({ msg }) {
  return (
    <div style={{
      padding: "10px 14px", borderRadius: 6, marginTop: 12,
      background: T.red + "11", border: `1px solid ${T.red}33`,
      fontSize: 12, color: T.red, fontFamily: T.sans
    }}>{msg}</div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────
const cardStyle = {
  background: T.surface, border: `1px solid ${T.border}`,
  borderRadius: 8, padding: "14px 16px",
};
const labelStyle = {
  display: "block", fontSize: 11, color: T.muted, fontFamily: T.sans,
  textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6, fontWeight: 500
};
const inputStyle = {
  width: "100%", background: T.surface, border: `1px solid ${T.border}`,
  borderRadius: 6, padding: "8px 12px", color: T.text, fontFamily: T.sans,
  fontSize: 13, outline: "none", boxSizing: "border-box",
};
const textareaStyle = {
  ...inputStyle, resize: "vertical", fontFamily: T.sans,
};
const selectStyle = {
  ...inputStyle, cursor: "pointer", appearance: "none",
};
const primaryBtn = {
  background: T.blue, color: "#fff", border: "none",
  borderRadius: 6, padding: "8px 18px", fontSize: 13, fontWeight: 500,
  fontFamily: T.sans, cursor: "pointer", transition: "opacity 0.15s",
};
const ghostBtn = {
  background: "transparent", color: T.muted, border: "none",
  padding: "4px 0", fontSize: 12, fontFamily: T.sans,
  cursor: "pointer", textAlign: "left",
};

// ─── Main App ─────────────────────────────────────────────────────
const TABS = [
  { id: "gap",    label: "Gap finder",    sub: "Find where to contribute" },
  { id: "dedup",  label: "Dedup",         sub: "Check if it's already proposed" },
  { id: "impact", label: "Impact",        sub: "Blast radius before you code", core: true },
  { id: "prepr",  label: "Pre-PR",        sub: "Catch issues before CI does" },
];

export default function ContribFlow() {
  const [repoUrl, setRepoUrl] = useState("");
  const [activeTab, setActiveTab] = useState("impact");
  const [repoValid, setRepoValid] = useState(null); // null | true | false

  const validateUrl = useCallback((val) => {
    const match = val.match(/github\.com\/([^/]+)\/([^/\s?#]+)/);
    setRepoValid(val === "" ? null : !!match);
  }, []);

  return (
    <div style={{
      background: T.bg, minHeight: "100vh", color: T.text,
      fontFamily: T.sans
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600&display=swap');
        * { box-sizing: border-box; }
        @keyframes spin { to { transform: rotate(360deg); } }
        input:focus, textarea:focus, select:focus {
          border-color: #388BFD88 !important;
          outline: none !important;
          box-shadow: 0 0 0 3px #388BFD18 !important;
        }
        button:hover:not(:disabled) { opacity: 0.85; }
        button:disabled { opacity: 0.4; cursor: not-allowed; }
        textarea::placeholder, input::placeholder { color: #484F58; }
        ::-webkit-scrollbar { width: 4px; } 
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #21262D; border-radius: 2px; }
      `}</style>

      {/* Top bar */}
      <div style={{
        borderBottom: `1px solid ${T.border}`, padding: "14px 32px",
        display: "flex", alignItems: "center", gap: 16,
        background: T.surface + "CC", backdropFilter: "blur(8px)",
        position: "sticky", top: 0, zIndex: 10
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexShrink: 0 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: "linear-gradient(135deg, #388BFD, #39C5CF)",
            display: "flex", alignItems: "center", justifyContent: "center"
          }}>
            <span style={{ fontSize: 14, fontFamily: T.mono, color: "#fff", fontWeight: 700 }}>
              C
            </span>
          </div>
          <span style={{ fontWeight: 600, fontSize: 15, fontFamily: T.sans, color: T.text }}>
            ContribFlow
          </span>
          <span style={{
            fontSize: 10, color: T.muted, background: T.border,
            padding: "2px 6px", borderRadius: 4, fontFamily: T.mono
          }}>
            powered by IBM Bob
          </span>
        </div>

        {/* Repo URL input */}
        <div style={{ flex: 1, position: "relative" }}>
          <div style={{ position: "absolute", left: 10, top: "50%",
            transform: "translateY(-50%)", color: T.dim, fontSize: 13 }}>
            ⌥
          </div>
          <input
            value={repoUrl}
            onChange={e => { setRepoUrl(e.target.value); validateUrl(e.target.value); }}
            placeholder="https://github.com/owner/repo"
            style={{
              ...inputStyle, paddingLeft: 28,
              borderColor: repoValid === false ? T.red + "88" : T.border,
            }}
          />
          {repoValid === true && (
            <span style={{ position: "absolute", right: 10, top: "50%",
              transform: "translateY(-50%)", color: T.green, fontSize: 12 }}>✓</span>
          )}
        </div>
      </div>

      {/* Tab bar */}
      <div style={{
        borderBottom: `1px solid ${T.border}`, padding: "0 32px",
        display: "flex", gap: 0, background: T.surface
      }}>
        {TABS.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "12px 20px", display: "flex", flexDirection: "column", gap: 2,
              borderBottom: activeTab === tab.id
                ? `2px solid ${tab.core ? T.cyan : T.blue}`
                : "2px solid transparent",
              transition: "border-color 0.15s",
              opacity: activeTab === tab.id ? 1 : 0.5,
            }}>
            <div style={{
              fontSize: 13, fontWeight: activeTab === tab.id ? 500 : 400,
              color: activeTab === tab.id
                ? (tab.core ? T.cyan : T.text)
                : T.muted,
              fontFamily: T.sans, display: "flex", alignItems: "center", gap: 6
            }}>
              {tab.core && (
                <span style={{
                  fontSize: 9, padding: "1px 5px", borderRadius: 3,
                  background: T.cyan + "22", color: T.cyan,
                  border: `1px solid ${T.cyan}44`, fontFamily: T.mono,
                  textTransform: "uppercase", letterSpacing: "0.05em"
                }}>core</span>
              )}
              {tab.label}
            </div>
            <div style={{ fontSize: 10, color: T.dim, fontFamily: T.sans }}>
              {tab.sub}
            </div>
          </button>
        ))}
      </div>

      {/* Content area */}
      <div style={{ maxWidth: 900, margin: "0 auto", padding: "28px 32px" }}>
        {!repoUrl && (
          <div style={{
            padding: "20px", borderRadius: 8, marginBottom: 24,
            background: T.blueGlow, border: `1px solid ${T.blue}22`,
            fontSize: 13, color: T.muted, fontFamily: T.sans
          }}>
            Enter a GitHub repository URL above to get started.
          </div>
        )}

        {activeTab === "gap"    && <GapFinder repoUrl={repoUrl} />}
        {activeTab === "dedup"  && <IdeaDedup repoUrl={repoUrl} />}
        {activeTab === "impact" && <ChangeImpact repoUrl={repoUrl} />}
        {activeTab === "prepr"  && <PrePR repoUrl={repoUrl} />}
      </div>
    </div>
  );
}
