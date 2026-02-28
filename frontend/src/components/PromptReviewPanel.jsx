import { useState, useEffect, useCallback } from "react";

const STATUS_COLORS = {
  curated: { bg: "#0d3320", border: "#22c55e", text: "#4ade80", label: "CURATED" },
  evolving: { bg: "#1a2744", border: "#3b82f6", text: "#60a5fa", label: "EVOLVING" },
  draft: { bg: "#3b2a10", border: "#f59e0b", text: "#fbbf24", label: "DRAFT" },
  fallback: { bg: "#3b1019", border: "#ef4444", text: "#f87171", label: "FALLBACK" },
  none: { bg: "#1e293b", border: "#64748b", text: "#94a3b8", label: "NONE" },
};

export default function PromptReviewPanel() {
  const [prompt, setPrompt] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [notes, setNotes] = useState("");
  const [improvements, setImprovements] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState({});
  const [toast, setToast] = useState(null);

  const API = "/api/prompts";

  const showToast = (msg, type = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 4000);
  };

  const fetchPrompt = useCallback(async () => {
    try {
      const res = await fetch(`${API}/active`);
      const data = await res.json();
      setPrompt(data);
      setEditText(data.system_prompt || "");
    } catch (e) {
      console.error("Failed to fetch prompt:", e);
    }
  }, []);

  const fetchPerformance = useCallback(async () => {
    try {
      const res = await fetch(`${API}/performance`);
      setPerformance(await res.json());
    } catch (e) {
      console.error("Failed to fetch performance:", e);
    }
  }, []);

  useEffect(() => {
    fetchPrompt();
    fetchPerformance();
    const interval = setInterval(() => {
      fetchPrompt();
      fetchPerformance();
    }, 60000);
    return () => clearInterval(interval);
  }, [fetchPrompt, fetchPerformance]);

  const handleCurate = async (withEdits) => {
    setLoading((p) => ({ ...p, curate: true }));
    try {
      const body = {
        curator: "human",
        notes: notes || "Curated via dashboard",
      };
      if (withEdits) body.edited_prompt = editText;
      const res = await fetch(`${API}/curate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      showToast(`Prompt curated (v${data.version})`);
      setEditing(false);
      setNotes("");
      fetchPrompt();
      fetchPerformance();
    } catch (e) {
      showToast("Curation failed: " + e.message, "error");
    }
    setLoading((p) => ({ ...p, curate: false }));
  };

  const handleImprove = async () => {
    setLoading((p) => ({ ...p, improve: true }));
    try {
      const res = await fetch(`${API}/improve`);
      const data = await res.json();
      setImprovements(data);
    } catch (e) {
      showToast("Improvement analysis failed", "error");
    }
    setLoading((p) => ({ ...p, improve: false }));
  };

  const handleRollback = async (version) => {
    if (!window.confirm(`Roll back to version ${version}?`)) return;
    try {
      const res = await fetch(`${API}/rollback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ version }),
      });
      const data = await res.json();
      showToast(data.message);
      fetchPrompt();
    } catch (e) {
      showToast("Rollback failed", "error");
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Delete prompt? Next run will auto-generate a new one.")) return;
    try {
      await fetch(`${API}/reset`, { method: "POST" });
      showToast("Prompt reset. Will regenerate on next cycle.");
      fetchPrompt();
      fetchPerformance();
    } catch (e) {
      showToast("Reset failed", "error");
    }
  };

  const status = prompt?.status || "none";
  const sc = STATUS_COLORS[status] || STATUS_COLORS.none;

  return (
    <div style={{ background: "#0a0f1a", borderRadius: 12, padding: 24, marginBottom: 24 }}>
      {/* Toast */}
      {toast && (
        <div
          style={{
            position: "fixed", top: 20, right: 20, zIndex: 9999,
            padding: "12px 20px", borderRadius: 8, fontSize: 14, fontWeight: 600,
            background: toast.type === "error" ? "#7f1d1d" : "#14532d",
            color: toast.type === "error" ? "#fca5a5" : "#86efac",
            border: `1px solid ${toast.type === "error" ? "#dc2626" : "#22c55e"}`,
          }}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ color: "#e2e8f4", margin: 0, fontSize: 20 }}>System Prompt Lifecycle</h2>
          <p style={{ color: "#64748b", margin: "4px 0 0", fontSize: 13 }}>
            Human-in-the-loop curation • Auto-bootstrap • Self-improvement
          </p>
        </div>
        <div
          style={{
            background: sc.bg, border: `1px solid ${sc.border}`,
            color: sc.text, padding: "6px 16px", borderRadius: 20,
            fontSize: 13, fontWeight: 700, letterSpacing: 1,
          }}
        >
          {sc.label} {prompt?.version ? `v${prompt.version}` : ""}
        </div>
      </div>

      {/* Performance Strip */}
      {performance?.performance && (
        <div
          style={{
            display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
            gap: 12, marginBottom: 20,
          }}
        >
          {[
            { label: "Runs", value: performance.performance.runs || 0, color: "#60a5fa" },
            {
              label: "Avg Confidence",
              value: `${((performance.performance.avg_confidence || 0) * 100).toFixed(1)}%`,
              color: performance.performance.avg_confidence > 0.6 ? "#4ade80" : "#fbbf24",
            },
            { label: "Regime Changes", value: performance.performance.regime_changes || 0, color: "#c084fc" },
            { label: "Conflicts", value: performance.performance.conflicts_detected || 0, color: "#f87171" },
          ].map((m) => (
            <div
              key={m.label}
              style={{
                background: "#111827", borderRadius: 8, padding: "10px 14px",
                borderLeft: `3px solid ${m.color}`,
              }}
            >
              <div style={{ color: "#64748b", fontSize: 11, textTransform: "uppercase" }}>{m.label}</div>
              <div style={{ color: m.color, fontSize: 22, fontWeight: 700 }}>{m.value}</div>
            </div>
          ))}

          {/* Health Badge */}
          {performance.health && (
            <div
              style={{
                background: "#111827", borderRadius: 8, padding: "10px 14px",
                borderLeft: `3px solid ${
                  performance.health.grade === "healthy" ? "#22c55e" :
                  performance.health.grade === "needs_attention" ? "#f59e0b" : "#ef4444"
                }`,
              }}
            >
              <div style={{ color: "#64748b", fontSize: 11, textTransform: "uppercase" }}>Health</div>
              <div style={{
                color: performance.health.grade === "healthy" ? "#4ade80" :
                       performance.health.grade === "needs_attention" ? "#fbbf24" : "#f87171",
                fontSize: 16, fontWeight: 700, textTransform: "capitalize",
              }}>
                {performance.health.grade?.replace("_", " ")}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Prompt Viewer / Editor */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          <span style={{ color: "#94a3b8", fontSize: 13, fontWeight: 600 }}>
            SYSTEM PROMPT {prompt?.generated_by ? `(generated by: ${prompt.generated_by})` : ""}
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            {!editing ? (
              <button
                onClick={() => setEditing(true)}
                style={{
                  background: "#1e3a5f", color: "#60a5fa", border: "1px solid #2563eb",
                  borderRadius: 6, padding: "4px 12px", fontSize: 12, cursor: "pointer",
                }}
              >
                Edit
              </button>
            ) : (
              <>
                <button
                  onClick={() => setEditing(false)}
                  style={{
                    background: "#1e293b", color: "#94a3b8", border: "1px solid #475569",
                    borderRadius: 6, padding: "4px 12px", fontSize: 12, cursor: "pointer",
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleCurate(true)}
                  disabled={loading.curate}
                  style={{
                    background: "#14532d", color: "#4ade80", border: "1px solid #22c55e",
                    borderRadius: 6, padding: "4px 12px", fontSize: 12, cursor: "pointer",
                    opacity: loading.curate ? 0.5 : 1,
                  }}
                >
                  {loading.curate ? "Saving..." : "Save & Curate"}
                </button>
              </>
            )}
          </div>
        </div>

        {editing ? (
          <>
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              style={{
                width: "100%", minHeight: 300, background: "#111827", color: "#e2e8f4",
                border: "1px solid #2563eb", borderRadius: 8, padding: 12,
                fontFamily: "monospace", fontSize: 12, resize: "vertical",
                lineHeight: 1.6,
              }}
            />
            <input
              type="text"
              placeholder="Notes: what did you change and why?"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: "100%", background: "#111827", color: "#e2e8f4",
                border: "1px solid #334155", borderRadius: 6, padding: "8px 12px",
                fontSize: 13, marginTop: 8,
              }}
            />
          </>
        ) : (
          <pre
            style={{
              background: "#111827", color: "#cbd5e1", borderRadius: 8,
              padding: 16, fontSize: 12, lineHeight: 1.6, maxHeight: 300,
              overflow: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word",
              border: `1px solid ${sc.border}20`,
            }}
          >
            {prompt?.system_prompt || "No prompt yet — will auto-generate on first synthesis run."}
          </pre>
        )}
      </div>

      {/* Approve without edits (for draft/evolving) */}
      {!editing && (status === "draft" || status === "evolving") && (
        <button
          onClick={() => handleCurate(false)}
          disabled={loading.curate}
          style={{
            background: "#14532d", color: "#4ade80", border: "1px solid #22c55e",
            borderRadius: 8, padding: "8px 20px", fontSize: 14, fontWeight: 600,
            cursor: "pointer", marginBottom: 16, opacity: loading.curate ? 0.5 : 1,
          }}
        >
          ✓ Approve as Curated (no edits)
        </button>
      )}

      {/* Action Bar */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginBottom: 16 }}>
        <button
          onClick={handleImprove}
          disabled={loading.improve}
          style={{
            background: "#1e293b", color: "#c084fc", border: "1px solid #7c3aed",
            borderRadius: 8, padding: "8px 16px", fontSize: 13, cursor: "pointer",
            opacity: loading.improve ? 0.5 : 1,
          }}
        >
          {loading.improve ? "Analyzing..." : "🧠 Ask Opus 4.6 for Improvements"}
        </button>
        <button
          onClick={handleReset}
          style={{
            background: "#1e293b", color: "#f87171", border: "1px solid #7f1d1d",
            borderRadius: 8, padding: "8px 16px", fontSize: 13, cursor: "pointer",
          }}
        >
          Reset (re-bootstrap)
        </button>
      </div>

      {/* Improvement Suggestions */}
      {improvements && (
        <div style={{ background: "#111827", borderRadius: 8, padding: 16, marginBottom: 16, border: "1px solid #7c3aed30" }}>
          <h3 style={{ color: "#c084fc", margin: "0 0 12px", fontSize: 15 }}>
            🧠 Opus 4.6 Improvement Suggestions
          </h3>
          {improvements.overall_assessment && (
            <p style={{ color: "#94a3b8", fontSize: 13, marginBottom: 12 }}>
              <strong>Assessment:</strong> {improvements.overall_assessment}
              {improvements.urgency && (
                <span style={{
                  marginLeft: 8, padding: "2px 8px", borderRadius: 10, fontSize: 11, fontWeight: 700,
                  background: improvements.urgency === "high" ? "#7f1d1d" : improvements.urgency === "medium" ? "#713f12" : "#1e293b",
                  color: improvements.urgency === "high" ? "#fca5a5" : improvements.urgency === "medium" ? "#fde68a" : "#94a3b8",
                }}>
                  {improvements.urgency.toUpperCase()}
                </span>
              )}
            </p>
          )}
          {improvements.improvements?.map((imp, i) => (
            <div
              key={i}
              style={{
                background: "#0a0f1a", borderRadius: 6, padding: 12, marginBottom: 8,
                borderLeft: "3px solid #7c3aed",
              }}
            >
              <div style={{ color: "#c084fc", fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
                Section: {imp.section}
              </div>
              {imp.current && (
                <div style={{ color: "#f87171", fontSize: 12, marginBottom: 4 }}>
                  <span style={{ opacity: 0.6 }}>Current:</span> {imp.current}
                </div>
              )}
              <div style={{ color: "#4ade80", fontSize: 12, marginBottom: 4 }}>
                <span style={{ opacity: 0.6 }}>Suggested:</span> {imp.suggested}
              </div>
              <div style={{ color: "#64748b", fontSize: 11 }}>
                {imp.reasoning}
              </div>
            </div>
          ))}

          <button
            onClick={() => {
              // Apply suggestions: append them to the current prompt as amendments
              const amendments = improvements.improvements
                ?.map((imp) => `\n\n[IMPROVEMENT v${prompt?.version || "?"}]: ${imp.section}\n${imp.suggested}`)
                .join("");
              if (amendments) {
                setEditText((prev) => prev + amendments);
                setEditing(true);
                setNotes("Applied Opus 4.6 suggestions — review before curating");
                showToast("Suggestions appended to prompt. Review and curate.");
              }
            }}
            style={{
              background: "#2e1065", color: "#c084fc", border: "1px solid #7c3aed",
              borderRadius: 6, padding: "6px 14px", fontSize: 12, cursor: "pointer", marginTop: 8,
            }}
          >
            Apply Suggestions to Editor
          </button>
        </div>
      )}

      {/* Version History */}
      {prompt?.history?.length > 0 && (
        <div style={{ background: "#111827", borderRadius: 8, padding: 16, border: "1px solid #1e293b" }}>
          <h3 style={{ color: "#94a3b8", margin: "0 0 12px", fontSize: 14 }}>Version History</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {prompt.history.map((h) => (
              <div
                key={h.version}
                style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  background: "#0a0f1a", borderRadius: 6, padding: "8px 12px",
                }}
              >
                <div>
                  <span style={{ color: "#60a5fa", fontWeight: 600, fontSize: 13 }}>v{h.version}</span>
                  <span style={{ color: "#475569", marginLeft: 8, fontSize: 12 }}>
                    {STATUS_COLORS[h.status]?.label || h.status}
                  </span>
                  <span style={{ color: "#334155", marginLeft: 8, fontSize: 11 }}>
                    {new Date(h.saved_at).toLocaleDateString()}
                  </span>
                </div>
                <button
                  onClick={() => handleRollback(h.version)}
                  style={{
                    background: "transparent", color: "#f59e0b", border: "1px solid #92400e",
                    borderRadius: 4, padding: "2px 8px", fontSize: 11, cursor: "pointer",
                  }}
                >
                  Rollback
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Human Notes */}
      {prompt?.human_notes && (
        <div style={{ marginTop: 12, padding: "8px 12px", background: "#111827", borderRadius: 6, borderLeft: "3px solid #22c55e" }}>
          <span style={{ color: "#64748b", fontSize: 11 }}>CURATOR NOTES:</span>
          <p style={{ color: "#94a3b8", fontSize: 13, margin: "4px 0 0" }}>{prompt.human_notes}</p>
        </div>
      )}
    </div>
  );
}
