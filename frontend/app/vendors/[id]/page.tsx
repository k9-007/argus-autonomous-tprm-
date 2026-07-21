"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "../../lib/api";
import { RiskBadge, TierBadge, DecisionText, TypeBadge, Gauge, Bar, TrendChart } from "../../components/ui";
import { AssessmentStream } from "../../components/AssessmentStream";

function overallCoverage(coverage: Record<string, any> = {}): number {
  let scored = 0;
  let total = 0;
  Object.values(coverage).forEach((c: any) => {
    const t = c.total || 0;
    total += t;
    scored += ((c.coverage_pct || 0) / 100) * t;
  });
  return total ? Math.round((scored / total) * 100) : 0;
}

function coverageColor(pct: number): string {
  return pct >= 70 ? "#34d399" : pct >= 40 ? "#fbbf24" : "#f87171";
}

const TABS = ["Overview", "Compliance", "Evidence", "Questionnaire", "AI Risk", "Monitoring", "Actions"];

export default function VendorDetail() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [v, setV] = useState<any>(null);
  const [tab, setTab] = useState("Overview");
  const [reassessing, setReassessing] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    const d = await api.vendor(id);
    setV(d);
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  // Continuous monitoring is live: refresh the feed + risk trend on an interval
  // while the Monitoring tab is open.
  useEffect(() => {
    if (tab !== "Monitoring" || reassessing) return;
    const iv = setInterval(() => {
      load();
    }, 5000);
    return () => clearInterval(iv);
  }, [tab, reassessing, load]);

  if (!v) return <div className="loading">Loading vendor…</div>;

  const score = v.score;
  const isAI = v.vendor_type === "ai_agent" || v.vendor_type === "mcp";
  const cov = overallCoverage(v.coverage);

  async function reassess() {
    const res = await api.reassess(id);
    setReassessing(res.assessment_id);
  }

  async function remove() {
    if (!confirm(`Delete ${v.name}? This permanently removes the vendor and all its assessments, evidence and findings.`)) {
      return;
    }
    setDeleting(true);
    try {
      await api.deleteVendor(id);
      router.push("/");
    } catch (err) {
      alert("Delete failed: " + err);
      setDeleting(false);
    }
  }

  return (
    <>
      <div className="topbar">
        <div>
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <button className="btn btn-ghost" onClick={() => router.push("/")}>← Portfolio</button>
          </div>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn" onClick={reassess}>↻ Re-assess</button>
          <button className="btn btn-danger" onClick={remove} disabled={deleting}>
            {deleting ? "Deleting…" : "Delete vendor"}
          </button>
        </div>
      </div>

      <div className="content">
        <div className="vendor-head">
          <div>
            <h2>{v.name}</h2>
            <div className="meta">
              <TypeBadge type={v.vendor_type} />
              <TierBadge tier={v.tier} />
              <span>{v.category}</span>
              {v.trust_center_url && <span className="mono">{v.trust_center_url}</span>}
            </div>
          </div>
          <div style={{ textAlign: "right", minWidth: 240 }}>
            <div className="muted" style={{ fontSize: 12, color: "var(--text-faint)" }}>Control coverage</div>
            <div style={{ fontSize: 30, fontWeight: 800, color: coverageColor(cov), lineHeight: 1.1 }}>{cov}%</div>
            <div style={{ marginTop: 6 }}>
              <Bar pct={cov} color={coverageColor(cov)} />
            </div>
            <div className="muted" style={{ fontSize: 12, color: "var(--text-faint)", marginTop: 8 }}>
              Recommendation: <DecisionText decision={v.assessment?.decision} />
            </div>
          </div>
        </div>

        {reassessing && (
          <div className="card" style={{ marginBottom: 16 }}>
            <AssessmentStream
              assessmentId={reassessing}
              onComplete={() => {
                setTimeout(() => {
                  setReassessing(null);
                  load();
                }, 800);
              }}
            />
          </div>
        )}

        <div className="tabs">
          {TABS.map((t) => {
            if (t === "AI Risk" && !isAI) return null;
            return (
              <button key={t} className={tab === t ? "active" : ""} onClick={() => setTab(t)}>
                {t}
              </button>
            );
          })}
        </div>

        {tab === "Overview" && <Overview v={v} score={score} />}
        {tab === "Compliance" && <Compliance v={v} />}
        {tab === "Evidence" && <Evidence v={v} onUploaded={load} />}
        {tab === "Questionnaire" && <Questionnaire v={v} />}
        {tab === "AI Risk" && <AIRisk v={v} />}
        {tab === "Monitoring" && <Monitoring v={v} />}
        {tab === "Actions" && <Actions v={v} />}
      </div>
    </>
  );
}

function Overview({ v, score }: any) {
  return (
    <div className="two-col">
      <div className="card">
        <div className="section-title" style={{ marginTop: 0 }}>Risk score</div>
        {score ? (
          <>
            <div className="gauge-wrap">
              <Gauge score={score.residual} label="Residual" />
              <div style={{ flex: 1 }}>
                <div className="kv"><span className="k">Inherent risk</span><b>{score.inherent}/100</b></div>
                <div className="kv"><span className="k">Residual risk</span><b><RiskBadge band={score.band} /> {score.residual}/100</b></div>
                <div className="kv"><span className="k">Tier</span><TierBadge tier={v.tier} /></div>
                <div className="kv"><span className="k">Data sensitivity</span><span>{v.data_sensitivity}</span></div>
                <div className="kv"><span className="k">System access</span><span>{v.system_access}</span></div>
              </div>
            </div>
            <div className="section-title">Why this score (drivers)</div>
            {score.drivers?.map((d: any, i: number) => (
              <div className="driver" key={i}>
                <div>
                  {d.factor}
                  {d.detail && <div className="detail">{d.detail}</div>}
                </div>
                <div className={`impact ${d.impact >= 0 ? "pos" : "neg"}`}>
                  {d.impact >= 0 ? "+" : ""}{typeof d.impact === "number" ? d.impact.toFixed(1) : d.impact}
                </div>
              </div>
            ))}
          </>
        ) : (
          <div className="empty">No score yet.</div>
        )}
      </div>

      <div className="grid">
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Executive summary</div>
          <p style={{ fontSize: 14, lineHeight: 1.6, color: "var(--text-dim)" }}>{v.assessment?.summary}</p>
        </div>
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Subprocessors (4th-party)</div>
          {v.subprocessors?.length ? (
            <div className="pill-row">
              {v.subprocessors.map((s: string) => <span className="pill" key={s}>{s}</span>)}
            </div>
          ) : <div className="empty">None identified.</div>}
        </div>
        <div className="card">
          <div className="section-title" style={{ marginTop: 0 }}>Top findings</div>
          {v.findings?.length ? v.findings.slice(0, 3).map((f: any, i: number) => (
            <div className="finding" key={i}>
              <div className="ftitle">{f.title}<span className={`badge ${f.severity}`}>{f.severity}</span></div>
            </div>
          )) : <div className="empty">No material findings.</div>}
        </div>
      </div>
    </div>
  );
}

const STATUS_LABEL: Record<string, string> = {
  compliant: "Compliant",
  partially_compliant: "Partially compliant",
  no_evidence: "No evidence",
  gated: "Gated (access pending)",
  expired: "Expired",
  not_applicable: "N/A",
  needs_review: "Needs review",
};

function Compliance({ v }: any) {
  const byFw: Record<string, any[]> = {};
  (v.controls || []).forEach((c: any) => {
    (byFw[c.framework] = byFw[c.framework] || []).push(c);
  });
  return (
    <div className="card">
      <div className="section-title" style={{ marginTop: 0 }}>Framework control mapping — evidence-based</div>
      <div className="legend">
        <span><span className="dot-status compliant" /> Compliant</span>
        <span><span className="dot-status partially_compliant" /> Partially compliant</span>
        <span><span className="dot-status no_evidence" /> No evidence</span>
        <span><span className="dot-status gated" /> Gated (NDA/access)</span>
        <span><span className="dot-status expired" /> Expired</span>
      </div>
      {Object.keys(byFw).length === 0 && <div className="empty">No control mapping yet.</div>}
      {Object.entries(byFw).map(([fw, ctrls]) => {
        const cov = v.coverage[fw] || {};
        const pct = Math.round(cov.coverage_pct ?? 0);
        return (
          <div className="matrix-fw" key={fw}>
            <h4>
              <span>{fw}</span>
              <span className="muted" style={{ color: "var(--text-faint)", fontWeight: 400 }}>
                {cov.compliant || 0} compliant · {cov.partial || 0} partial · {cov.gated || 0} gated · {cov.no_evidence || 0} no-evidence · {pct}%
              </span>
            </h4>
            <Bar pct={pct} color={pct >= 70 ? "#34d399" : pct >= 40 ? "#fbbf24" : "#f87171"} />
            <div style={{ marginTop: 10 }}>
              {ctrls.map((c: any, i: number) => (
                <div className="ctrl" key={i}>
                  <span className={`dot-status ${c.status}`} />
                  <span className="cid">{c.control_id}</span>
                  <span className="cname">{c.control_name}</span>
                  <span className={`status-badge ${c.status}`}>{STATUS_LABEL[c.status] || c.status}</span>
                  <div className="cmeta">
                    {c.evidence_name ? (
                      <><span className="cite">Evidence: {c.evidence_name}</span> — {c.citation}</>
                    ) : (
                      <span>{c.observation}</span>
                    )}
                    {c.gap ? <div className="gap">Gap: {c.gap}</div> : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

const STATE_BADGE: Record<string, string> = {
  parsed: "low", downloaded: "low", granted: "low", public: "neutral",
  requested: "medium", nda_pending: "high", expired: "critical",
};

function Evidence({ v, onUploaded }: any) {
  const [busy, setBusy] = useState(false);
  async function onFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setBusy(true);
    try {
      await api.uploadDocuments(v.id, files);
      onUploaded?.();
    } catch (err) {
      alert("Upload failed: " + err);
    } finally {
      setBusy(false);
    }
  }
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div className="section-title" style={{ marginTop: 0 }}>Evidence library</div>
        <label className="btn" style={{ cursor: "pointer" }}>
          {busy ? "Parsing…" : "+ Upload documents"}
          <input type="file" multiple hidden onChange={onFiles} accept=".pdf,.txt,.md" />
        </label>
      </div>
      <p className="hint">
        ~90% of trust-center documents are gated. Argus tracks every document's access state, parses
        uploads (PDF/text), and re-assesses automatically.
      </p>
      {v.documents?.length ? v.documents.map((d: any) => (
        <div className="doc-row" key={d.id}>
          <div style={{ flex: 1 }}>
            <div className="dname">{d.name}</div>
            <div className="dtype">
              {d.doc_type} · via {d.source}
              {d.issued_at ? ` · issued ${d.issued_at}` : ""}
              {d.expires_at ? ` · valid to ${d.expires_at}` : ""}
            </div>
          </div>
          <span className={`badge ${STATE_BADGE[d.state] || "neutral"}`}>{d.state.replace("_", " ")}</span>
        </div>
      )) : <div className="empty">No documents yet. Upload the vendor's compliance pack to verify controls.</div>}
    </div>
  );
}

function Questionnaire({ v }: any) {
  return (
    <div className="grid">
      {v.questionnaires?.length ? v.questionnaires.map((q: any, qi: number) => {
        const yes = q.answers.filter((a: any) => a.answer === "Yes").length;
        return (
          <div className="card" key={qi}>
            <div className="section-title" style={{ marginTop: 0 }}>
              {q.framework} — {yes}/{q.answers.length} evidence-backed
            </div>
            {q.answers.map((a: any, i: number) => (
              <div className="qa" key={i}>
                <div className="q"><span className="mono" style={{ color: "var(--text-faint)" }}>{a.id}</span> {a.question}</div>
                <div className="a">
                  <span className={a.answer === "Yes" ? "yes" : "no"}>{a.answer}</span>
                  {a.evidence ? <span>· cited: {a.evidence}</span> : <span>· unverified (self-attestation)</span>}
                  <span>· confidence {a.confidence}</span>
                </div>
              </div>
            ))}
          </div>
        );
      }) : <div className="empty">No questionnaire completed.</div>}
    </div>
  );
}

function AIRisk({ v }: any) {
  const findings = (v.findings || []).filter((f: any) => f.category === "ai_risk");
  const p = v.subprocessors;
  return (
    <div className="two-col">
      <div className="card">
        <div className="section-title" style={{ marginTop: 0 }}>AI-vendor risk findings</div>
        {findings.length ? findings.map((f: any, i: number) => (
          <div className="finding" key={i}>
            <div className="ftitle">{f.title}<span className={`badge ${f.severity}`}>{f.severity}</span></div>
            <div className="fdetail">{f.detail}</div>
          </div>
        )) : <div className="empty">No AI-specific findings.</div>}
      </div>
      <div className="card">
        <div className="section-title" style={{ marginTop: 0 }}>Why this matters</div>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: "var(--text-dim)" }}>
          AI tools, agents and MCP servers are a new vendor class with no traditional TPRM playbook.
          Argus evaluates prompt-injection exposure, tool/action permissions, data retention &amp; training
          use, and autonomous actions — mapping toward ISO 42001.
        </p>
        {p?.length ? (
          <>
            <div className="section-title">Model / infra subprocessors</div>
            <div className="pill-row">{p.map((s: string) => <span className="pill" key={s}>{s}</span>)}</div>
          </>
        ) : null}
      </div>
    </div>
  );
}

function Monitoring({ v }: any) {
  const history = v.score_history || [];
  const current = history.length ? history[history.length - 1] : null;
  const first = history.length ? history[0] : null;
  const delta = current && first ? Math.round(current.residual - first.residual) : 0;
  const sevRank: Record<string, number> = { low: 0, medium: 1, high: 2, critical: 3 };
  const openSignals = (v.monitoring || []).filter((m: any) => sevRank[m.severity] >= 2).length;

  return (
    <div className="grid">
      <div className="card">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div className="section-title" style={{ marginTop: 0 }}>
            <span className="live-dot" style={{ marginRight: 8 }} />
            Residual risk over time — live
          </div>
          <div className="muted" style={{ fontSize: 12, color: "var(--text-faint)" }}>
            auto-refreshing every 5s · next review {v.next_review_at?.slice(0, 10) || "—"}
          </div>
        </div>
        <div className="monitor-stats">
          <div className="mstat">
            <div className="label">Current residual</div>
            <div className="value">{current ? Math.round(current.residual) : "—"}<span className="unit">/100</span></div>
          </div>
          <div className="mstat">
            <div className="label">Trend</div>
            <div className="value" style={{ color: delta > 0 ? "var(--red)" : delta < 0 ? "#34d399" : "var(--text-dim)" }}>
              {delta > 0 ? "▲" : delta < 0 ? "▼" : "—"} {Math.abs(delta)}
            </div>
          </div>
          <div className="mstat">
            <div className="label">Assessments</div>
            <div className="value">{history.length}</div>
          </div>
          <div className="mstat">
            <div className="label">Open high signals</div>
            <div className="value" style={{ color: openSignals ? "var(--amber)" : "#34d399" }}>{openSignals}</div>
          </div>
        </div>
        <TrendChart points={history} />
      </div>

      <div className="card">
        <div className="section-title" style={{ marginTop: 0 }}>Continuous monitoring feed</div>
        <p className="hint">CVEs, breaches, cert expiry, GitHub leaks and subprocessor changes. High/critical signals trigger an automatic re-score.</p>
        {v.monitoring?.length ? v.monitoring.map((m: any, i: number) => (
          <div className="finding" key={i}>
            <div className="ftitle">
              {m.title}
              <span className={`badge ${m.severity}`}>{m.severity}</span>
            </div>
            <div className="fdetail">
              <span className="mono" style={{ color: "var(--text-faint)" }}>{m.event_type}</span> · {m.detail}
              {m.detected_at && <span className="mono" style={{ color: "var(--text-faint)", marginLeft: 8 }}>· {m.detected_at.slice(0, 16).replace("T", " ")}</span>}
              {m.triggered_rescore && <span className="badge medium" style={{ marginLeft: 8 }}>triggers re-score</span>}
            </div>
          </div>
        )) : <div className="empty">No monitoring signals.</div>}
      </div>
    </div>
  );
}

function Actions({ v }: any) {
  return (
    <div className="card">
      <div className="section-title" style={{ marginTop: 0 }}>Access requests, NDAs &amp; outreach</div>
      <p className="hint">Argus never auto-signs legal terms — NDAs are routed to an authorized Approver.</p>
      {v.tasks?.length ? v.tasks.map((t: any, i: number) => (
        <div className="finding" key={i}>
          <div className="ftitle">
            {t.title}
            <span className="badge neutral">{t.status}</span>
          </div>
          <div className="fdetail">
            <span className="badge ai" style={{ marginRight: 8 }}>{t.task_type}</span>
            owner: {t.owner}
            {t.detail && <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{t.detail}</div>}
          </div>
        </div>
      )) : <div className="empty">No open tasks.</div>}
    </div>
  );
}
