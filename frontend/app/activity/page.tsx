"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";

export default function AgentActivity() {
  const router = useRouter();
  const [data, setData] = useState<any>({ running: [], activity: [], audit: [] });
  const timer = useRef<any>(null);

  useEffect(() => {
    let stop = false;
    async function tick() {
      try {
        const [activityData, auditData] = await Promise.all([api.activityRecent(80), api.audit(50)]);
        if (!stop) setData({ ...activityData, audit: auditData.activity || [] });
      } catch {}
      if (!stop) timer.current = setTimeout(tick, 1500);
    }
    tick();
    return () => {
      stop = true;
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  const running = data.running || [];
  const activity = data.activity || [];
  const audit = data.audit || [];

  return (
    <>
      <div className="topbar">
        <div>
          <h2>Agent Activity</h2>
          <div className="sub">Live view of the crew working across every assessment</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {running.length > 0 ? <span className="live-dot" /> : null}
          <span style={{ color: "var(--text-dim)", fontSize: 13 }}>
            {running.length} assessment{running.length === 1 ? "" : "s"} running
          </span>
        </div>
      </div>

      <div className="content">
        {running.length > 0 && (
          <>
            <div className="section-title" style={{ marginTop: 0 }}>In progress</div>
            <div className="cards" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
              {running.map((r: any) => (
                <div className="card" key={r.assessment_id} onClick={() => router.push(`/vendors/${r.vendor_id}`)} style={{ cursor: "pointer" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span className="spinner" />
                    <b>{r.vendor}</b>
                  </div>
                  <div className="foot" style={{ marginTop: 6, color: "var(--text-faint)", fontSize: 12 }}>
                    {r.status} · {r.trigger}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}

        <div className="section-title">Recent agent actions</div>
        <div className="card">
          {activity.length === 0 ? (
            <div className="empty">No agent activity yet. Add a vendor to see the crew work.</div>
          ) : (
            <div className="feed">
              {activity.map((a: any, i: number) => (
                <div className={`feed-item ${a.status}`} key={i}>
                  <div className="agent">{a.agent}</div>
                  <div className="msg">
                    <span className="badge neutral" style={{ marginRight: 8 }}>{a.vendor}</span>
                    {a.message}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="section-title">Workspace audit trail</div>
        <div className="card">
          {audit.length === 0 ? (
            <div className="empty">No workspace actions recorded yet.</div>
          ) : (
            <div className="audit-list">
              {audit.map((entry: any) => (
                <div className="audit-row" key={entry.id}>
                  <div><b>{entry.action.replaceAll(".", " · ")}</b><span>{entry.target || "Workspace"}{entry.detail ? ` · ${entry.detail}` : ""}</span></div>
                  <div><span>{entry.actor}</span><time>{new Date(entry.at).toLocaleString()}</time></div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
