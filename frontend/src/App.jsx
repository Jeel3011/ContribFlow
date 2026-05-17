import React, { useState, useCallback, useEffect } from "react";

const API = "http://localhost:8000/api";

// ─── Premium Light Design tokens ────────────────────────────────────
const T = {
  bg:      "#0A0F1C",
  surface: "rgba(17, 24, 39, 0.65)",
  border:  "rgba(255, 255, 255, 0.08)",
  borderHover: "rgba(255, 255, 255, 0.2)",
  text:    "#F8FAFC",
  muted:   "#94A3B8",
  dim:     "#475569",
  blue:    "#3B82F6",
  blueGlow:"rgba(59, 130, 246, 0.15)",
  cyan:    "#06B6D4",
  amber:   "#F59E0B",
  red:     "#EF4444",
  green:   "#10B981",
  purple:  "#8B5CF6",
  mono:    "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
  sans:    "'Inter', 'Outfit', 'Segoe UI', system-ui, sans-serif",
};

// ─── Reusable primitives ───────────────────────────────────────────
const Badge = ({ color = T.muted, children, style = {} }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "3px 10px", borderRadius: 8, fontSize: 11, fontWeight: 600,
    letterSpacing: "0.05em", textTransform: "uppercase",
    background: color + "15", color, border: `1px solid ${color}33`,
    fontFamily: T.sans, transition: "all 0.2s", ...style
  }} className="badge-hover">{children}</span>
);

const Chip = ({ label, value, color = T.blue, icon }) => (
  <div style={{
    background: T.surface, border: `1px solid ${T.border}`,
    borderRadius: 16, padding: "16px 20px", flex: 1, minWidth: 0,
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)"
  }} className="hover-card">
    <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans, fontWeight: 600,
      textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
      {icon && <span style={{ marginRight: 5 }}>{icon}</span>}{label}
    </div>
    <div style={{ fontSize: 32, fontWeight: 700, color, fontFamily: T.mono }}>{value}</div>
  </div>
);

const ConfBar = ({ confidence, type }) => {
  const color = type === "direct" ? T.cyan : type === "indirect" ? T.amber : T.red;
  const pct = Math.round(confidence * 100);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 12 }}>
      <div style={{ flex: 1, height: 6, background: T.border, borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", background: color,
          borderRadius: 3, transition: "width 1s cubic-bezier(0.4, 0, 0.2, 1)" }} />
      </div>
      <span style={{ fontSize: 12, color, fontFamily: T.mono, minWidth: 32,
        textAlign: "right", fontWeight: 700 }}>{pct}%</span>
      <Badge color={color} style={{ fontSize: 10, padding: "2px 8px" }}>{type}</Badge>
    </div>
  );
};

const FileChip = ({ path }) => (
  <span style={{
    display: "inline-flex", alignItems: "center", gap: 4,
    padding: "4px 10px", borderRadius: 8, fontSize: 11, fontWeight: 500,
    background: T.blueGlow, color: T.blue, fontFamily: T.mono,
    border: `1px solid ${T.blue}33`, margin: "2px",
    userSelect: "all", cursor: "text", transition: "all 0.2s"
  }} className="hover-chip">
    <span style={{ opacity: 0.5 }}>›</span>{path}
  </span>
);

const STAGE_LOGS = {
  stage1: [
    "Initializing Gap Finder Agent...",
    "Running score_file_suspiciousness() heuristic...",
    "Scanning directory tree (max 100 paths)...",
    "Filtering known test files and READMEs...",
    "Analyzing recent commit history for bug hotspots...",
    "Identifying high-impact contribution areas...",
    "Formulating gap descriptions..."
  ],
  stage2: [
    "Initializing Deduplication Agent...",
    "Fetching recent repository issues...",
    "Fetching pull requests (filtering 'pull_request')...",
    "Generating semantic embeddings for your idea...",
    "Comparing similarity scores against open issues...",
    "Filtering matches below 0.5 threshold...",
    "Evaluating conflict status..."
  ],
  stage3: [
    "Initializing Change Impact Agent...",
    "Building pre-Bob static dependency map...",
    "Identifying target files via keyword matching...",
    "Tracing dynamic imports (importlib, getattr)...",
    "Mapping downstream services at risk...",
    "Validating traceability confidence scores...",
    "Structuring dependency traces..."
  ],
  stage4: [
    "Initializing Quality Check Agent...",
    "Running static_precheck() (bare excepts, unused imports)...",
    "Fetching 2-3 similar files for convention baseline...",
    "Analyzing AST for anti-patterns...",
    "Evaluating diff against established patterns...",
    "Formatting review suggestions..."
  ]
};

const LiveLogStream = ({ stageKey }) => {
  const logs = STAGE_LOGS[stageKey] || ["Processing..."];
  const [currentLog, setCurrentLog] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentLog(prev => (prev < logs.length - 1 ? prev + 1 : prev));
    }, 2000 + Math.random() * 1000); // Randomize step time slightly
    return () => clearInterval(interval);
  }, [logs.length]);

  return (
    <div style={{
      background: "rgba(0, 0, 0, 0.3)", border: `1px solid rgba(255, 255, 255, 0.05)`,
      borderRadius: 8, padding: "12px 16px", marginTop: 16,
      fontFamily: T.mono, fontSize: 12, color: T.blue,
      boxShadow: "inset 0 2px 10px rgba(0,0,0,0.5)",
      position: "relative", overflow: "hidden"
    }} className="log-stream-container">
      <div style={{ position: "absolute", top: 0, left: 0, width: "2px", height: "100%", background: T.cyan, boxShadow: `0 0 10px ${T.cyan}` }} />
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {logs.slice(0, currentLog + 1).map((log, i) => (
          <div key={i} style={{ 
            opacity: i === currentLog ? 1 : 0.5,
            display: "flex", alignItems: "center", gap: 10
          }} className="slide-up-log">
            <span style={{ color: i === currentLog ? T.cyan : T.dim, textShadow: i === currentLog ? `0 0 8px ${T.cyan}` : 'none' }}>{">"}</span>
            <span style={{ color: i === currentLog ? "#E2E8F0" : T.muted }}>{log}</span>
            {i === currentLog && <span className="blinking-cursor" style={{ width: 6, height: 14, background: T.cyan, display: "inline-block", boxShadow: `0 0 8px ${T.cyan}` }} />}
          </div>
        ))}
      </div>
    </div>
  );
};

const Spinner = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, color: T.blue,
    padding: "40px 0", justifyContent: "center", fontFamily: T.sans, fontSize: 14, fontWeight: 500 }}>
    <div style={{
      width: 24, height: 24, borderRadius: "50%",
      border: `3px solid rgba(59, 130, 246, 0.2)`, borderTopColor: T.cyan,
      animation: "spin 0.8s linear infinite", boxShadow: `0 0 15px rgba(6, 182, 212, 0.4)`
    }} />
    <span style={{ background: "linear-gradient(90deg, #3B82F6, #06B6D4)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", textShadow: "0 0 20px rgba(6, 182, 212, 0.3)" }}>
      Agent is reasoning…
    </span>
  </div>
);

// ─── Orchestrator: Stage status card ──────────────────────────────────────────
const STAGE_STATUS = {
  pending:  { icon: "○", color: T.dim,    label: "Pending" },
  running:  { icon: "⏳", color: T.blue,  label: "Running" },
  done:     { icon: "✅", color: T.green,  label: "Done" },
  skipped:  { icon: "—",  color: T.muted, label: "Skipped" },
  error:    { icon: "❌", color: T.red,   label: "Error" },
  conflict: { icon: "⚠️", color: T.amber, label: "Conflict" },
};

function StageCard({ stageKey, stageName, status, summary, data, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const s = STAGE_STATUS[status] || STAGE_STATUS.pending;
  return (
    <div style={{
      background: T.surface, border: `1px solid ${status === "running" ? T.blue : T.border}`,
      borderRadius: 12, overflow: "hidden", transition: "all 0.3s",
      boxShadow: status === "running" ? `0 0 0 3px ${T.blue}22` : "0 1px 3px rgba(0,0,0,0.06)"
    }}>
      <div style={{ padding: "16px 20px", display: "flex", alignItems: "center",
        gap: 12, cursor: data ? "pointer" : "default" }}
        onClick={() => data && setOpen(o => !o)}>
        <span style={{ fontSize: 18 }}>{s.icon}</span>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontFamily: T.sans, fontSize: 14, color: T.text }}>{stageName}</div>
          {summary && <div style={{ fontSize: 12, color: T.muted, marginTop: 2, fontFamily: T.sans }}>{summary}</div>}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {status === "running" && (
            <div style={{ width: 14, height: 14, borderRadius: "50%",
              border: `2px solid ${T.blueGlow}`, borderTopColor: T.blue,
              animation: "spin 0.8s linear infinite" }} />
          )}
          <span style={{ fontSize: 11, fontWeight: 600, color: s.color,
            fontFamily: T.sans, textTransform: "uppercase", letterSpacing: "0.05em" }}>
            {s.label}
          </span>
          {data && (
            <span style={{ color: T.dim, fontSize: 12,
              transform: open ? "rotate(180deg)" : "rotate(0)", transition: "transform 0.3s" }}>▼</span>
          )}
        </div>
      </div>
      {status === "running" && stageKey && (
        <div style={{ padding: "0 20px 20px" }}><LiveLogStream stageKey={stageKey} /></div>
      )}
      {open && data && (
        <div style={{ padding: "16px 20px", borderTop: `1px solid ${T.border}` }} className="slide-down">
          {stageName === "Gap Finder" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(data.gaps || []).map((g, i) => (
                <div key={i} style={{ padding: 12, background: T.bg, borderRadius: 8, borderLeft: `3px solid ${T.blue}` }}>
                  <div style={{ fontWeight: 600, fontSize: 13, color: T.text, marginBottom: 4 }}>{g.title}</div>
                  <div style={{ fontSize: 11, color: T.muted, fontFamily: T.mono }}>{g.file} | {g.impact} impact</div>
                  <div style={{ fontSize: 12, color: T.dim, marginTop: 6 }}>{g.reasoning}</div>
                </div>
              ))}
            </div>
          )}

          {stageName === "Idea Deduplication" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div style={{ fontSize: 13, color: T.text, padding: 12, background: data.status === "conflict" ? "rgba(239, 68, 68, 0.1)" : "rgba(16, 185, 129, 0.1)", borderRadius: 8, border: `1px solid ${data.status === "conflict" ? "rgba(239, 68, 68, 0.3)" : "rgba(16, 185, 129, 0.3)"}` }}>
                <strong>Recommendation:</strong> {data.recommendation_text}
              </div>
              {data.conflicts?.length > 0 && (
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: T.muted, marginBottom: 8, textTransform: "uppercase" }}>Conflicts Found</div>
                  {(data.conflicts || []).map((c, i) => (
                    <div key={i} style={{ padding: 10, background: T.bg, borderRadius: 6, marginBottom: 6, borderLeft: `3px solid ${T.amber}` }}>
                      <a href={c.url} target="_blank" rel="noreferrer" style={{ fontSize: 13, fontWeight: 500, color: T.blue, textDecoration: "none" }}>#{c.number} {c.title}</a>
                      <div style={{ fontSize: 11, color: T.muted, marginTop: 4 }}>Similarity: {c.similarity} | State: {c.state}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {stageName === "Change Impact Analysis" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: T.muted, marginBottom: 8, textTransform: "uppercase" }}>Services at Risk</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  {(data.services_at_risk || []).length === 0 ? <span style={{fontSize: 12, color: T.dim}}>None identified</span> : 
                    data.services_at_risk.map((s, i) => (
                      <span key={i} style={{ fontSize: 11, fontWeight: 600, padding: "5px 12px", background: "linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.15))", color: "#FCD34D", borderRadius: 20, border: "1px solid rgba(245, 158, 11, 0.3)" }}>{s}</span>
                    ))
                  }
                </div>
              </div>
              <div>
                <div style={{ fontSize: 12, fontWeight: 600, color: T.muted, marginBottom: 8, textTransform: "uppercase" }}>
                  Files Affected & Dependency Traces
                  <span style={{ marginLeft: 8, color: T.dim, fontWeight: 400, textTransform: "none" }}>
                    ({(data.files_affected || []).length} files)
                  </span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 6,
                  maxHeight: 320, overflowY: "auto", paddingRight: 4 }}>
                  {(data.files_affected || []).length === 0
                    ? <span style={{fontSize: 12, color: T.dim}}>None</span>
                    : data.files_affected.map((f, i) => (
                      <div key={i} style={{ background: T.surface, border: `1px solid ${T.border}`,
                        borderRadius: 6, padding: "10px 14px", flexShrink: 0 }}>
                        <div style={{ fontSize: 12, fontFamily: T.mono, color: T.text, fontWeight: 500 }}>{f}</div>
                        {data.dependency_traces?.[f] && (
                          <div style={{ fontSize: 11, color: T.muted, marginTop: 4,
                            paddingLeft: 12, borderLeft: `2px solid ${T.blue}` }}>
                            {data.dependency_traces[f]}
                          </div>
                        )}
                      </div>
                    ))
                  }
                </div>
              </div>
            </div>
          )}

          {stageName === "Pre-PR Quality Check" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(data.issues || []).map((issue, i) => (
                <div key={i} style={{ padding: 12, background: T.bg, borderRadius: 8,
                  borderLeft: `3px solid ${issue.severity === "error" ? T.red : issue.severity === "warning" ? T.amber : T.blue}` }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    <span style={{ fontFamily: T.mono, fontSize: 11, color: T.blue }}>{issue.file}:{issue.line}</span>
                    <span style={{ fontSize: 10, padding: "2px 6px", background: T.surface,
                      border: `1px solid ${T.border}`, borderRadius: 10, color: T.muted }}>{issue.severity}</span>
                    {issue.source === "static" && <span style={{ fontSize: 10, color: T.dim }}>static</span>}
                  </div>
                  <div style={{ fontSize: 13, color: T.text, marginBottom: 4 }}>{issue.issue}</div>
                  {issue.fix && issue.fix !== "N/A" && (
                    <div style={{ fontSize: 11, color: T.green, fontFamily: T.mono,
                      background: "rgba(16,185,129,0.08)", padding: "6px 10px", borderRadius: 6,
                      borderLeft: `2px solid ${T.green}` }}>
                      fix: {issue.fix}
                    </div>
                  )}
                </div>
              ))}
              {(data.issues || []).length === 0 && (
                <div style={{ fontSize: 13, color: T.green, padding: 12,
                  background: "rgba(16, 185, 129, 0.1)", borderRadius: 8,
                  border: `1px solid rgba(16, 185, 129, 0.3)` }}>
                  ✅ No issues found. Code is clean!
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ScoreCard({ summary }) {
  const score = summary?.overall_score ?? 0;
  const color = score >= 80 ? T.green : score >= 60 ? T.amber : T.red;
  return (
    <div style={{ background: `linear-gradient(135deg, ${color}08, ${color}15)`,
      border: `1px solid ${color}33`, borderRadius: 16, padding: "28px 32px",
      marginTop: 24 }} className="slide-up">
      <div style={{ fontSize: 13, fontWeight: 700, color, fontFamily: T.sans,
        textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 16 }}>
        Contribution Readiness Report
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 24 }}>
        <div style={{ fontSize: 64, fontWeight: 800, color, fontFamily: T.mono, lineHeight: 1 }}>
          {score}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ height: 10, background: T.border, borderRadius: 5, overflow: "hidden" }}>
            <div style={{ width: `${score}%`, height: "100%", background: color,
              borderRadius: 5, transition: "width 1.5s cubic-bezier(0.4, 0, 0.2, 1)" }} />
          </div>
          <div style={{ fontSize: 12, color: T.muted, marginTop: 6, fontFamily: T.sans }}>out of 100</div>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
        {[
          { label: "Uniqueness", value: summary?.uniqueness === "clear" ? "✅ Clear" :
            summary?.uniqueness === "conflict" ? "❌ Conflict" : "⚠️ Partial", color: T.text },
          { label: "Files Impacted", value: summary?.impact_scope?.files ?? "—", color: T.blue },
          { label: "Services at Risk", value: summary?.impact_scope?.services ?? "—", color: T.amber },
          { label: "Code Errors", value: summary?.code_quality?.errors ?? "—",
            color: (summary?.code_quality?.errors ?? 0) > 0 ? T.red : T.green },
        ].map(({ label, value, color: c }) => (
          <div key={label} style={{ background: T.surface, borderRadius: 10, padding: "12px 16px",
            border: `1px solid ${T.border}` }}>
            <div style={{ fontSize: 11, color: T.muted, fontFamily: T.sans,
              fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 4 }}>{label}</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: c, fontFamily: T.mono }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Master Orchestrator UI ────────────────────────────────────────────────────
function Orchestrator({ repoUrl }) {
  const [idea, setIdea] = useState("");
  const [diff, setDiff] = useState("");
  const [workflowMode, setWorkflowMode] = useState("full");
  const [stages, setStages] = useState({
    stage1: { status: "pending", stageName: "Gap Finder",            summary: "Find where to contribute" },
    stage2: { status: "pending", stageName: "Idea Deduplication",   summary: "Check if already proposed" },
    stage3: { status: "pending", stageName: "Change Impact Analysis",summary: "Map blast radius" },
    stage4: { status: "pending", stageName: "Pre-PR Quality Check", summary: "Review before CI" },
  });
  const [scoreSummary, setScoreSummary] = useState(null);
  const [running, setRunning] = useState(false);
  const [finalData, setFinalData] = useState(null);
  const [orchMessage, setOrchMessage] = useState("");
  const [error, setError] = useState(null);

  const updateStage = (stageKey, patch) =>
    setStages(prev => ({ ...prev, [stageKey]: { ...prev[stageKey], ...patch } }));

  const runOrchestrator = async () => {
    if (!repoUrl || !idea.trim()) return;
    const cleanRepoUrl = repoUrl.trim();
    setRunning(true); setError(null); setScoreSummary(null); setFinalData(null);
    setOrchMessage("");
    // Reset all stages
    setStages({
      stage1: { status: workflowMode === "impact_only" ? "skipped" : "pending", stageName: "Gap Finder", summary: "Find where to contribute" },
      stage2: { status: workflowMode === "impact_only" ? "skipped" : "pending", stageName: "Idea Deduplication", summary: "Check if already proposed" },
      stage3: { status: "pending", stageName: "Change Impact Analysis", summary: "Map blast radius" },
      stage4: { status: "pending", stageName: "Pre-PR Quality Check", summary: diff.trim() ? "Review before CI" : "Skipped: no diff provided" },
    });

    try {
      const resp = await fetch(`${API}/orchestrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_url: cleanRepoUrl, user_idea: idea, diff, workflow_mode: workflowMode })
      });

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        
        const parts = buffer.split("\n\n");
        buffer = parts.pop(); // Keep the last incomplete part in the buffer
        
        for (const part of parts) {
          const lines = part.split("\n").filter(l => l.startsWith("data: "));
          for (const line of lines) {
            try {
              const event = JSON.parse(line.slice(6));
              handleSSEEvent(event);
            } catch (_) {}
          }
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  };

  const handleSSEEvent = (event) => {
    switch (event.type) {
      case "orchestrator_start":
        setOrchMessage(event.message);
        break;
      case "stage_start":{
        const key = event.stage;
        updateStage(key, { status: "running", summary: event.message });
        break;
      }
      case "stage_complete":{
        const key = event.stage;
        updateStage(key, { status: "done", summary: event.summary, data: event.data });
        break;
      }
      case "stage_skipped":{
        const key = event.stage;
        updateStage(key, { status: "skipped", summary: event.message });
        break;
      }
      case "stage_error":{
        const key = event.stage;
        updateStage(key, { status: "error", summary: event.message });
        break;
      }
      case "orchestrator_stop":
        setOrchMessage(event.message);
        // Mark remaining pending stages as skipped
        setStages(prev => {
          const next = { ...prev };
          for (const k of Object.keys(next)) {
            if (next[k].status === "pending") next[k] = { ...next[k], status: "skipped", summary: "Skipped due to conflict" };
          }
          return next;
        });
        break;
      case "orchestrator_complete":
        setScoreSummary(event.summary);
        setOrchMessage(event.message);
        break;
      case "stream_end":
        setFinalData(event.final_state);
        break;
    }
  };

  const allDone = Object.values(stages).every(s => s.status !== "running");

  return (
    <div className="fade-in">
      {/* Workflow mode toggle (moved from header to avoid navigation conflict) */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <span style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, fontWeight: 600,
          textTransform: "uppercase", letterSpacing: "0.05em" }}>Mode:</span>
        <div style={{ display: "flex", background: "rgba(255,255,255,0.06)", borderRadius: 8,
          padding: 4, border: `1px solid ${T.border}` }}>
          {[{id:"full",label:"Full Workflow"},{id:"impact_only",label:"Impact Only"}].map(m => (
            <button key={m.id} onClick={() => setWorkflowMode(m.id)}
              style={{
                background: workflowMode === m.id ? T.surface : "transparent",
                color: workflowMode === m.id ? (m.id === "impact_only" ? T.cyan : T.text) : T.muted,
                border: "none", padding: "7px 16px", borderRadius: 6,
                fontSize: 13, fontWeight: 600, fontFamily: T.sans, cursor: "pointer",
                boxShadow: workflowMode === m.id ? "0 1px 3px rgba(0,0,0,0.15)" : "none",
                transition: "all 0.2s"
              }}>{m.label}</button>
          ))}
        </div>
      </div>

      {/* Unified input area */}
      <div style={{ background: T.surface, border: `1px solid ${T.border}`,
        borderRadius: 16, padding: "28px 32px", marginBottom: 28,
        boxShadow: "0 4px 20px -8px rgba(0,0,0,0.08)" }}>
        <div style={{ fontWeight: 700, fontSize: 17, color: T.text,
          fontFamily: T.sans, marginBottom: 20, display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 20 }}>💡</span> Describe Your Contribution
        </div>
        <div style={{ marginBottom: 16 }}>
          <label style={{ ...labelStyle, display: "block", marginBottom: 8 }}>What would you like to contribute?</label>
          <textarea
            value={idea}
            onChange={e => setIdea(e.target.value)}
            placeholder="e.g. Add retry logic with exponential backoff to the HTTP client in the error handling module"
            rows={3}
            style={{ ...inputStyle, resize: "vertical", fontFamily: T.sans, lineHeight: 1.6 }}
          />
        </div>
        <div style={{ marginBottom: 20 }}>
          <label style={{ ...labelStyle, display: "block", marginBottom: 8 }}>
            Git diff <span style={{ color: T.dim, fontWeight: 400 }}>(optional — paste output of `git diff HEAD`)</span>
          </label>
          <textarea
            value={diff}
            onChange={e => setDiff(e.target.value)}
            placeholder="Paste git diff here to enable Stage 4 Pre-PR Quality Check..."
            rows={4}
            style={{ ...inputStyle, resize: "vertical", fontFamily: T.mono, fontSize: 12, lineHeight: 1.5 }}
          />
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <button
            onClick={runOrchestrator}
            disabled={!repoUrl || !idea.trim() || running}
            style={{ ...primaryBtn, padding: "14px 32px", fontSize: 15 }}
            className="premium-btn"
          >
            {running ? "Running…" : "🚀 Run Analysis"}
          </button>
          {orchMessage && !running && (
            <span style={{ fontSize: 13, color: T.muted, fontFamily: T.sans }}>{orchMessage}</span>
          )}
        </div>
      </div>

      {/* Live stage progress */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 24 }}>
        {Object.entries(stages)
          .filter(([k]) => workflowMode === "impact_only" ? ["stage3", "stage4"].includes(k) : true)
          .map(([key, s]) => (
            <StageCard key={key} stageKey={key} stageName={s.stageName} status={s.status}
              summary={s.summary} data={s.data} defaultOpen={false} />
          ))}
      </div>

      {error && <ErrorBox msg={error} />}

      {/* Final report card */}
      {scoreSummary && <ScoreCard summary={scoreSummary} />}
    </div>
  );
}


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
    <div className="fade-in">
      <div style={{ display: "flex", gap: 16, marginBottom: 24, alignItems: "flex-end" }}>
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
        <button onClick={analyze} disabled={!repoUrl || loading} style={primaryBtn} className="premium-btn">
          Find Gaps
        </button>
      </div>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}
      {result && (
        <div className="slide-up">
          <div style={{ display: "flex", gap: 16, marginBottom: 24 }}>
            <Chip label="High impact" value={result.summary?.high_count ?? 0} color={T.red} />
            <Chip label="Medium" value={result.summary?.medium_count ?? 0} color={T.amber} />
            <Chip label="Low" value={result.summary?.low_count ?? 0} color={T.green} />
            <Chip label="Files scanned" value={result.files_analyzed ?? 0} color={T.muted} />
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {(result.gaps || []).map((gap, i) => (
              <GapCard key={gap.id || i} gap={gap}
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
    <div style={{ ...cardStyle, borderLeft: `4px solid ${impactColor[gap.impact] || T.muted}` }} className="hover-card">
      <div style={{ display: "flex", justifyContent: "space-between",
        alignItems: "flex-start", gap: 16, cursor: "pointer" }}
        onClick={() => setOpen(o => !o)}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, color: T.text, fontFamily: T.sans,
            fontSize: 15, marginBottom: 6 }}>{gap.title}</div>
          <div style={{ fontFamily: T.mono, fontSize: 12, color: T.blue }}>
            {gap.file}{gap.line_range ? `:${gap.line_range}` : ""}
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
          <Badge color={impactColor[gap.impact]}>{gap.impact}</Badge>
          <Badge color={T.muted}>{categoryLabel[gap.category] || gap.category}</Badge>
          {gap.good_first_issue &&
            <Badge color={T.green}>Good first issue</Badge>}
          <div style={{ color: T.muted, fontSize: 12, marginLeft: 8,
             transform: open ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }}>
            ▼
          </div>
        </div>
      </div>
      {open && (
        <div style={{ marginTop: 16, borderTop: `1px solid ${T.border}`, paddingTop: 16 }} className="slide-down">
          <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans,
            lineHeight: 1.6, marginBottom: 12 }}>{gap.reasoning}</div>
          {gap.evidence && (
            <div style={{ fontFamily: T.mono, fontSize: 12, color: T.amber,
              background: "rgba(245, 158, 11, 0.05)", padding: "10px 14px", borderRadius: 8,
              borderLeft: `3px solid ${T.amber}` }}>
              <span style={{ color: T.muted, marginRight: 8, fontWeight: 600 }}>EVIDENCE:</span>
              {gap.evidence}
            </div>
          )}
          <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ fontSize: 12, color: T.muted, fontFamily: T.sans }}>
              Effort: <span style={{ color: T.text, fontWeight: 600, textTransform: "capitalize" }}>{gap.estimated_effort || "unknown"}</span>
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
    <div className="fade-in">
      <div style={{ marginBottom: 24 }}>
        <label style={labelStyle}>Your contribution idea</label>
        <textarea
          value={idea}
          onChange={e => setIdea(e.target.value)}
          placeholder="Add retry logic with exponential backoff to the HTTP client so failed requests are retried up to 3 times before raising an exception."
          rows={4}
          style={textareaStyle}
        />
        <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, marginTop: 8 }}>
          Plain English. Don't worry about technical precision — describe the goal. The Agent will semantically match it.
        </div>
      </div>
      <button onClick={check} disabled={!repoUrl || !idea.trim() || loading} style={primaryBtn} className="premium-btn">
        Check for Duplicates
      </button>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}
      {result && (
        <div style={{ marginTop: 24 }} className="slide-up">
          <div style={{
            display: "flex", alignItems: "center", gap: 16,
            padding: "20px 24px", borderRadius: 12,
            background: (statusColor[result.status] || T.muted) + "0A",
            border: `1px solid ${(statusColor[result.status] || T.muted)}33`,
            marginBottom: 24, boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)"
          }}>
            <div style={{
              width: 14, height: 14, borderRadius: "50%",
              background: statusColor[result.status] || T.muted, flexShrink: 0,
              boxShadow: `0 0 10px ${(statusColor[result.status] || T.muted)}88`
            }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 18, fontFamily: T.sans,
                color: statusColor[result.status] || T.muted }}>
                {statusLabel[result.status] || result.status}
              </div>
              {result.recommendation_text && (
                <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans, marginTop: 4 }}>
                  {result.recommendation_text}
                </div>
              )}
            </div>
            {result.checked_against && (
              <div style={{ fontSize: 12, color: T.dim, fontFamily: T.sans, textAlign: "right" }}>
                Checked {Object.values(result.checked_against).reduce((a,b) => a+b, 0)} items
              </div>
            )}
          </div>

          {(result.conflicts || []).map(c => (
            <div key={c.number} style={{
              ...cardStyle,
              borderLeft: `4px solid ${c.type === "pr" ? T.purple : T.blue}`,
              marginBottom: 16
            }} className="hover-card">
              <div style={{ display: "flex", justifyContent: "space-between", gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                    <Badge color={c.type === "pr" ? T.purple : T.blue}>
                      {c.type === "pr" ? "PR" : "Issue"} #{c.number}
                    </Badge>
                    {c.state && <Badge color={c.state === "open" ? T.green : T.muted}>{c.state}</Badge>}
                    {c.assigned && <Badge color={T.amber}>Assigned → {c.assignee}</Badge>}
                  </div>
                  <a href={c.url} target="_blank" rel="noreferrer"
                    style={{ color: T.text, fontFamily: T.sans, fontSize: 16,
                      fontWeight: 600, textDecoration: "none" }} className="link-hover">
                    {c.title}
                    <span style={{ color: T.blue, marginLeft: 6, fontSize: 12 }}>↗</span>
                  </a>
                  <div style={{ fontSize: 14, color: T.muted, fontFamily: T.sans,
                    marginTop: 8, lineHeight: 1.6 }}>{c.summary}</div>
                </div>
                <div style={{ flexShrink: 0, textAlign: "center", background: T.surface, 
                  padding: "12px 16px", borderRadius: 12, border: `1px solid ${T.border}` }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: T.red,
                    fontFamily: T.mono }}>{Math.round(c.similarity * 100)}%</div>
                  <div style={{ fontSize: 11, fontWeight: 600, color: T.muted, fontFamily: T.sans, textTransform: "uppercase" }}>Match</div>
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
    <div className="fade-in">
      <div style={{ marginBottom: 20 }}>
        <label style={labelStyle}>Describe your change</label>
        <textarea
          value={desc}
          onChange={e => setDesc(e.target.value)}
          placeholder="Modify the retry function in http_client.py to use exponential backoff instead of a fixed 1-second interval. The new behavior retries up to 3 times with delays of 1s, 2s, and 4s."
          rows={4}
          style={textareaStyle}
        />
        <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, marginTop: 8 }}>
          Describe the goal. You don't need to know which files are affected — the Agent will trace the dependency graph.
        </div>
      </div>

      <button
        onClick={() => setShowDiff(s => !s)}
        style={{ ...ghostBtn, marginBottom: 20, fontWeight: 500 }}>
        {showDiff ? "▼ Hide diff" : "▶ Paste git diff (optional, improves accuracy)"}
      </button>
      {showDiff && (
        <textarea
          value={diff}
          onChange={e => setDiff(e.target.value)}
          placeholder="Paste output of: git diff HEAD"
          rows={6}
          style={{ ...textareaStyle, fontFamily: T.mono, fontSize: 12, marginBottom: 20 }}
        />
      )}

      <div>
        <button onClick={analyze} disabled={!repoUrl || !desc.trim() || loading} style={primaryBtn} className="premium-btn">
          Analyze Blast Radius
        </button>
      </div>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}

      {result && (
        <div style={{ marginTop: 32 }} className="slide-up">
          {/* Analysis mode badge */}
          <div style={{ display: "flex", gap: 12, marginBottom: 20, alignItems: "center" }}>
            <Badge color={result.analysis_mode === "diff" ? T.green : T.blue}>
              {result.analysis_mode === "diff" ? "Diff-based Analysis" : "Description-based Analysis"}
            </Badge>
            {result.has_dynamic_risks && (
              <Badge color={T.red}>Dynamic Risks Detected</Badge>
            )}
          </div>

          {/* Metrics row */}
          <div style={{ display: "flex", gap: 16, marginBottom: 28 }}>
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
          <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 24 }}>
            {/* Findings */}
            <div>
              <SectionTitle>Impact Findings</SectionTitle>
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {(result.findings || []).map((f, i) => (
                  <div key={f.id || i}
                    style={{
                      ...cardStyle,
                      cursor: "pointer",
                      borderLeft: `4px solid ${
                        f.type === "direct" ? T.cyan :
                        f.type === "indirect" ? T.amber : T.red
                      }`
                    }}
                    className="hover-card"
                    onClick={() => setOpenFinding(openFinding === i ? null : i)}>
                    <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans,
                      lineHeight: 1.6, marginBottom: 10, fontWeight: 500 }}>{f.finding}</div>
                    <ConfBar confidence={f.confidence} type={f.type} />
                    {openFinding === i && f.evidence_files?.length > 0 && (
                      <div style={{ marginTop: 14, borderTop: `1px solid ${T.border}`, paddingTop: 14 }} className="slide-down">
                        <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, fontWeight: 600,
                          marginBottom: 8, textTransform: "uppercase" }}>Evidence files</div>
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {f.evidence_files.map(p => <FileChip key={p} path={p} />)}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Affected files */}
              {result.files_affected?.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <SectionTitle>Files affected</SectionTitle>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {result.files_affected.map(p => <FileChip key={p} path={p} />)}
                  </div>
                </div>
              )}

              {/* Tests */}
              {result.tests_to_update?.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <SectionTitle>Tests to update</SectionTitle>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {result.tests_to_update.map(p => <FileChip key={p} path={p} />)}
                  </div>
                </div>
              )}
            </div>

            {/* Suggested order (right panel) */}
            <div>
              <div style={{
                background: T.bg, border: `1px solid ${T.border}`,
                borderRadius: 16, padding: 24, position: "sticky", top: 100,
                boxShadow: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.02)"
              }}>
                <SectionTitle>Execution Plan</SectionTitle>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  {(result.suggested_order || []).map((step, i) => (
                    <div key={i} style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
                      <div style={{
                        width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
                        background: T.blue, color: "#fff",
                        display: "flex", alignItems: "center", justifyContent: "center",
                        fontSize: 12, fontWeight: 700, fontFamily: T.mono,
                        boxShadow: `0 2px 6px ${T.blue}66`
                      }}>{i + 1}</div>
                      <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans,
                        lineHeight: 1.5, paddingTop: 2, fontWeight: 500 }}>{step}</div>
                    </div>
                  ))}
                </div>

                {result.confidence_explanation && (
                  <div style={{
                    marginTop: 24, paddingTop: 16, borderTop: `1px solid ${T.border}`,
                    fontSize: 12, color: T.dim, fontFamily: T.sans, lineHeight: 1.5
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
    <div className="fade-in">
      <div style={{ marginBottom: 24 }}>
        <label style={labelStyle}>Git diff</label>
        <textarea
          value={diff}
          onChange={e => setDiff(e.target.value)}
          placeholder={"Paste the output of:\n  git diff HEAD\nor\n  git diff main"}
          rows={10}
          style={{ ...textareaStyle, fontFamily: T.mono, fontSize: 12 }}
        />
        <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, marginTop: 8 }}>
          The Agent will review your diff against the repo's existing code conventions before CI runs.
        </div>
      </div>
      <button onClick={review} disabled={!repoUrl || !diff.trim() || loading} style={primaryBtn} className="premium-btn">
        Automated Code Review
      </button>

      {loading && <Spinner />}
      {error && <ErrorBox msg={error} />}

      {result && (
        <div style={{ marginTop: 24 }} className="slide-up">
          {/* Pass/Fail header */}
          <div style={{
            display: "flex", alignItems: "center", gap: 16,
            padding: "20px 24px", borderRadius: 12, marginBottom: 24,
            background: (result.passes_check ? T.green : T.red) + "0A",
            border: `1px solid ${(result.passes_check ? T.green : T.red)}33`,
            boxShadow: "0 4px 6px -1px rgba(0,0,0,0.02)"
          }}>
            <div style={{
              width: 36, height: 36, borderRadius: "50%", flexShrink: 0,
              background: (result.passes_check ? T.green : T.red) + "15",
              border: `2px solid ${result.passes_check ? T.green : T.red}`,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 18, fontWeight: 700, color: result.passes_check ? T.green : T.red
            }}>{result.passes_check ? "✓" : "✕"}</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18, fontFamily: T.sans,
                color: result.passes_check ? T.green : T.red }}>
                {result.passes_check ? "Ready to Submit" : "Quality Issues Detected"}
              </div>
              <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans, marginTop: 4 }}>
                {result.summary}
              </div>
            </div>
            {result.convention_files_used?.length > 0 && (
              <div style={{ marginLeft: "auto", fontSize: 12, color: T.dim,
                fontFamily: T.sans, textAlign: "right" }}>
                Conventions learned from:<br />
                {result.convention_files_used.map(f => (
                  <span key={f} style={{ color: T.blue, display: "block", fontWeight: 500 }}>{f}</span>
                ))}
              </div>
            )}
          </div>

          {/* Issues */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {(result.issues || []).map(issue => (
              <div key={issue.id || Math.random()}
                style={{ ...cardStyle, borderLeft: `4px solid ${sevColor[issue.severity] || T.muted}` }} className="hover-card">
                <div style={{ display: "flex", gap: 14, alignItems: "flex-start" }}>
                  <div style={{
                    width: 24, height: 24, borderRadius: "50%", flexShrink: 0,
                    background: (sevColor[issue.severity] || T.muted) + "15",
                    border: `1.5px solid ${(sevColor[issue.severity] || T.muted)}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 12, fontWeight: 700, color: sevColor[issue.severity] || T.muted,
                  }}>{sevIcon[issue.severity] || "?"}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: 10, alignItems: "center",
                      marginBottom: 8, flexWrap: "wrap" }}>
                      <span style={{ fontFamily: T.mono, fontSize: 12, color: T.blue, fontWeight: 600 }}>
                        {issue.file}:{issue.line}
                      </span>
                      <Badge color={sevColor[issue.severity] || T.muted}>{issue.severity}</Badge>
                      {issue.source === "static" &&
                        <Badge color={T.dim}>Static Check</Badge>}
                    </div>
                    <div style={{ fontSize: 14, color: T.text, fontFamily: T.sans,
                      lineHeight: 1.6, marginBottom: 12 }}>{issue.issue}</div>
                    <div style={{
                      fontFamily: T.mono, fontSize: 12, color: T.green,
                      background: "rgba(16, 185, 129, 0.1)", padding: "10px 14px", borderRadius: 8,
                      borderLeft: `3px solid ${T.green}`
                    }}>
                      <span style={{ color: T.muted, marginRight: 8, fontWeight: 600 }}>FIX:</span>
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
              marginTop: 24, padding: "20px", borderRadius: 12,
              background: T.bg, border: `1px solid ${T.border}`
            }}>
              <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, fontWeight: 600,
                textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 12 }}>
                Conventions Inferred by AI
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {result.convention_notes.map((n, i) => (
                  <div key={i} style={{ fontSize: 13, color: T.text, fontFamily: T.sans,
                    paddingLeft: 14, borderLeft: `2px solid ${T.border}` }}>
                    {n}
                  </div>
                ))}
              </div>
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
    <div style={{ fontSize: 12, color: T.muted, fontFamily: T.sans, fontWeight: 700,
      textTransform: "uppercase", letterSpacing: "0.06em",
      marginBottom: 16 }}>{children}</div>
  );
}

function ErrorBox({ msg }) {
  return (
    <div style={{
      padding: "12px 16px", borderRadius: 8, marginTop: 16,
      background: T.red + "0A", border: `1px solid ${T.red}33`,
      fontSize: 13, color: T.red, fontFamily: T.sans, fontWeight: 500
    }} className="slide-up">{msg}</div>
  );
}

// ─── Styles ───────────────────────────────────────────────────────
const cardStyle = {
  background: T.surface, border: `1px solid ${T.border}`,
  borderRadius: 12, padding: "20px",
  boxShadow: "0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03)"
};
const labelStyle = {
  display: "block", fontSize: 12, color: T.text, fontFamily: T.sans,
  textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8, fontWeight: 600
};
const inputStyle = {
  width: "100%", background: T.surface, border: `1px solid ${T.border}`,
  borderRadius: 8, padding: "12px 16px", color: T.text, fontFamily: T.sans,
  fontSize: 14, outline: "none", boxSizing: "border-box",
  boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)", transition: "all 0.2s"
};
const textareaStyle = {
  ...inputStyle, resize: "vertical", fontFamily: T.sans, lineHeight: 1.5
};
const selectStyle = {
  ...inputStyle, cursor: "pointer", appearance: "none",
};
const primaryBtn = {
  background: `linear-gradient(135deg, ${T.blue}, ${T.cyan})`, color: "#fff", border: "none",
  borderRadius: 8, padding: "12px 24px", fontSize: 14, fontWeight: 600,
  fontFamily: T.sans, cursor: "pointer", transition: "all 0.2s",
  boxShadow: `0 4px 12px ${T.blue}44`
};
const ghostBtn = {
  background: "transparent", color: T.blue, border: "none",
  padding: "6px 0", fontSize: 13, fontFamily: T.sans,
  cursor: "pointer", textAlign: "left", transition: "color 0.2s"
};

// ─── Main App ─────────────────────────────────────────────────────
const TABS = [
  { id: "orchestrator", label: "✦ Auto-Pilot",  sub: "All 4 stages, one click", core: true },
  { id: "gap",          label: "Gap Finder",    sub: "Find where to contribute" },
  { id: "dedup",        label: "Deduplication", sub: "Check if it's already proposed" },
  { id: "impact",       label: "Blast Radius",  sub: "Impact analysis before coding" },
  { id: "prepr",        label: "Pre-PR Check",  sub: "Catch issues before CI does" },
];

// ─── Error Boundary ─────────────────────────────────────────────────────────────
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ error, errorInfo });
    console.error("ErrorBoundary caught an error", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, background: "#FEF2F2", color: "#991B1B", fontFamily: "monospace", minHeight: "100vh" }}>
          <h2 style={{ color: "#7F1D1D", marginTop: 0 }}>🚨 FATAL REACT CRASH 🚨</h2>
          <p>Please share this exact error message with the AI:</p>
          <div style={{ background: "#FEE2E2", padding: 20, borderRadius: 8, border: "1px solid #FCA5A5", overflowX: "auto" }}>
            <strong>{this.state.error && this.state.error.toString()}</strong>
            <br />
            <br />
            <pre style={{ fontSize: 12, margin: 0 }}>
              {this.state.errorInfo && this.state.errorInfo.componentStack}
            </pre>
          </div>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: 20, padding: "10px 20px", background: "#EF4444", color: "white", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: "bold" }}>
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// Wrap the main app with ErrorBoundary
export default function AppWrapper() {
  return (
    <ErrorBoundary>
      <ContribFlow />
    </ErrorBoundary>
  );
}

function ContribFlow() {
  const [repoUrl, setRepoUrl] = useState("");
  const [activeTab, setActiveTab] = useState("orchestrator");
  const [repoValid, setRepoValid] = useState(null);

  const validateUrl = useCallback((val) => {
    const match = val.match(/github\.com\/([^/]+)\/([^/\s?#]+)/);
    setRepoValid(val === "" ? null : !!match);
  }, []);

  const visibleTabs = TABS;

  return (
    <div style={{
      background: T.bg, minHeight: "100vh", color: T.text,
      fontFamily: T.sans
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');
        
        * { box-sizing: border-box; }
        
        body { margin: 0; background: #050505; background-image: radial-gradient(circle at 50% 0%, rgba(59, 130, 246, 0.15), transparent 50%), radial-gradient(circle at 100% 100%, rgba(6, 182, 212, 0.1), transparent 50%); background-attachment: fixed; }
        
        .glass-header { 
          background: rgba(10, 15, 28, 0.6) !important; 
          backdrop-filter: blur(24px) saturate(180%) !important; 
          border-bottom: 1px solid rgba(255,255,255,0.08) !important; 
        }

        .slide-up-log {
          animation: slide-up 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }

        .blinking-cursor {
          animation: blink 1s step-end infinite;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }

        
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slide-up { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slide-down { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        
        .fade-in { animation: fade-in 0.4s ease-out forwards; }
        .slide-up { animation: slide-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        .slide-down { animation: slide-down 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        
        input:focus, textarea:focus, select:focus {
          border-color: #2563EB !important;
          outline: none !important;
          box-shadow: 0 0 0 4px rgba(37,99,235,0.15) !important;
        }
        
        .premium-btn:hover:not(:disabled) { 
          transform: translateY(-1px); 
          box-shadow: 0 6px 16px rgba(37,99,235,0.3) !important; 
        }
        .premium-btn:active:not(:disabled) {
          transform: translateY(1px);
          box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
        }
        button:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; box-shadow: none !important; }
        
        textarea::placeholder, input::placeholder { color: #94A3B8; }
        
        ::-webkit-scrollbar { width: 8px; } 
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }
        
        .hover-card { transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
        .hover-card:hover { 
          transform: translateY(-4px); 
          box-shadow: 0 12px 24px -8px rgba(0,0,0,0.1); 
          border-color: #CBD5E1; 
        }
        
        .glass-header { 
          background: rgba(255, 255, 255, 0.85); 
          backdrop-filter: blur(16px); 
          border-bottom: 1px solid rgba(0,0,0,0.05); 
        }
        
        .link-hover:hover { text-decoration: underline !important; color: #2563EB !important; }
        .badge-hover:hover { filter: brightness(0.95); }
      `}</style>

      {/* Top bar */}
      <div className="glass-header" style={{
        padding: "16px 40px", display: "flex", alignItems: "center", gap: 24,
        position: "sticky", top: 0, zIndex: 10
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: "linear-gradient(135deg, #2563EB, #0891B2)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 4px 10px rgba(37,99,235,0.3)"
          }}>
            <span style={{ fontSize: 18, fontFamily: T.sans, color: "#fff", fontWeight: 700 }}>
              C
            </span>
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, fontFamily: "'Outfit', sans-serif", color: T.text, letterSpacing: "-0.02em" }}>
              ContribFlow
            </div>
            <div style={{
              fontSize: 10, color: T.blue, fontWeight: 600, fontFamily: T.sans, textTransform: "uppercase", letterSpacing: "0.05em"
            }}>
              AI Co-Pilot
            </div>
          </div>
        </div>

        {/* Repo URL input */}
        <div style={{ flex: 1, position: "relative", maxWidth: 600 }}>
          <div style={{ position: "absolute", left: 14, top: "50%",
            transform: "translateY(-50%)", color: T.dim, fontSize: 14 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"></path>
              <path d="M9 18c-4.51 2-5-2-7-2"></path>
            </svg>
          </div>
          <input
            value={repoUrl}
            onChange={e => { setRepoUrl(e.target.value); validateUrl(e.target.value); }}
            placeholder="https://github.com/owner/repo"
            style={{
              ...inputStyle, paddingLeft: 40,
              borderColor: repoValid === false ? T.red : T.border,
              boxShadow: repoValid === false ? `0 0 0 3px ${T.red}15` : "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
            }}
          />
          {repoValid === true && (
            <span style={{ position: "absolute", right: 14, top: "50%",
              transform: "translateY(-50%)", color: T.green, fontSize: 14, fontWeight: 700 }}>✓</span>
          )}
        </div>
        
        {/* Health badge */}
        <a href="http://localhost:8000/health" target="_blank" rel="noreferrer"
          style={{ fontSize: 11, color: T.dim, fontFamily: T.mono, textDecoration: "none",
            padding: "6px 12px", border: `1px solid ${T.border}`, borderRadius: 6,
            flexShrink: 0, transition: "color 0.2s" }}>
          /health
        </a>
      </div>

      {/* Tab bar */}
      <div style={{
        borderBottom: `1px solid ${T.border}`, padding: "0 40px",
        display: "flex", gap: 8, background: T.surface,
        boxShadow: "0 4px 20px -10px rgba(0,0,0,0.05)"
      }}>
        {visibleTabs.map(tab => (
          <button key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              background: "none", border: "none", cursor: "pointer",
              padding: "16px 24px", display: "flex", flexDirection: "column", gap: 4,
              borderBottom: activeTab === tab.id
                ? `3px solid ${tab.core ? T.cyan : T.blue}`
                : "3px solid transparent",
              transition: "all 0.2s",
              opacity: activeTab === tab.id ? 1 : 0.6,
            }}>
            <div style={{
              fontSize: 14, fontWeight: activeTab === tab.id ? 600 : 500,
              color: activeTab === tab.id
                ? (tab.core ? T.cyan : T.text)
                : T.muted,
              fontFamily: T.sans, display: "flex", alignItems: "center", gap: 8
            }}>
              {tab.core && (
                <span style={{
                  fontSize: 10, padding: "2px 6px", borderRadius: 4,
                  background: T.cyan + "15", color: T.cyan, fontWeight: 700,
                  border: `1px solid ${T.cyan}33`, fontFamily: T.sans,
                  textTransform: "uppercase", letterSpacing: "0.05em"
                }}>core</span>
              )}
              {tab.label}
            </div>
            <div style={{ fontSize: 12, color: T.dim, fontFamily: T.sans }}>
              {tab.sub}
            </div>
          </button>
        ))}
      </div>

      {/* Content area */}
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 32px 80px" }}>
        {!repoUrl && (
          <div style={{
            padding: "24px", borderRadius: 12, marginBottom: 32,
            background: T.blueGlow, border: `1px solid ${T.blue}33`,
            fontSize: 15, color: T.blue, fontFamily: T.sans, fontWeight: 500,
            display: "flex", alignItems: "center", gap: 12
          }} className="slide-up">
            <span style={{ fontSize: 24 }}>👋</span>
            Enter a GitHub repository URL above to get started with ContribFlow.
          </div>
        )}

        {activeTab === "orchestrator" && <Orchestrator repoUrl={repoUrl} />}
        {activeTab === "gap"          && <GapFinder repoUrl={repoUrl} />}
        {activeTab === "dedup"        && <IdeaDedup repoUrl={repoUrl} />}
        {activeTab === "impact"       && <ChangeImpact repoUrl={repoUrl} />}
        {activeTab === "prepr"        && <PrePR repoUrl={repoUrl} />}
      </div>
    </div>
  );
}
