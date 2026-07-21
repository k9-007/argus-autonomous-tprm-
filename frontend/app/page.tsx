"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "./lib/api";
import { RiskBadge, TierBadge, DecisionText, TypeBadge } from "./components/ui";
import { AddVendorModal } from "./components/AddVendorModal";

export default function Portfolio() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const p = await api.portfolio();
      setData(p);
    } catch (e) {
      setData({ error: String(e) });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const [deletingId, setDeletingId] = useState<string | null>(null);

  const remove = useCallback(
    async (e: React.MouseEvent, v: any) => {
      e.stopPropagation();
      if (!confirm(`Delete ${v.name}? This permanently removes the vendor and all its assessments, evidence and findings.`)) {
        return;
      }
      setDeletingId(v.id);
      try {
        await api.deleteVendor(v.id);
        await load();
      } catch (err) {
        alert("Delete failed: " + err);
      } finally {
        setDeletingId(null);
      }
    },
    [load]
  );

  const counts = data?.counts;
  const vendors = data?.vendors || [];

  return (
    <>
      <div className="topbar">
        <div>
          <h2>Vendor Risk Portfolio</h2>
          <div className="sub">{data?.org?.name} · {data?.org?.required_frameworks?.join(" · ")}</div>
        </div>
        <button className="btn btn-primary" onClick={() => setShowAdd(true)}>
          + Add vendor
        </button>
      </div>

      <div className="content">
        {loading && <div className="loading">Loading portfolio…</div>}
        {data?.error && (
          <div className="card">
            <b>Could not reach the Argus API.</b>
            <p className="hint">Start the backend on {api.base} (see backend/README).</p>
          </div>
        )}

        {data && !data.error && (
          <>
            <div className="cards">
              <div className="card stat">
                <div className="label">Vendors tracked</div>
                <div className="value">{counts.total}</div>
                <div className="foot">{counts.monitoring} under continuous monitoring</div>
              </div>
              <div className="card stat">
                <div className="label">Critical / High</div>
                <div className="value" style={{ color: "var(--red)" }}>
                  {(counts.by_band.critical || 0) + (counts.by_band.high || 0)}
                </div>
                <div className="foot">{counts.by_band.critical || 0} critical, {counts.by_band.high || 0} high</div>
              </div>
              <div className="card stat">
                <div className="label">Tier 1 (critical)</div>
                <div className="value">{counts.tier1}</div>
                <div className="foot">Regulated data or production access</div>
              </div>
              <div className="card stat">
                <div className="label">Expiring evidence</div>
                <div className="value" style={{ color: "var(--amber)" }}>{data.expiring_evidence.length}</div>
                <div className="foot">Reports expired or within 90 days</div>
              </div>
            </div>

            <div className="section-title">All vendors</div>
            <div className="card" style={{ padding: 0 }}>
              {vendors.length === 0 ? (
                <div className="empty">No vendors yet. Add your first vendor to see the crew in action.</div>
              ) : (
                <table className="table">
                  <thead>
                    <tr>
                      <th>Vendor</th>
                      <th>Type</th>
                      <th>Tier</th>
                      <th>Inherent</th>
                      <th>Residual</th>
                      <th>Risk</th>
                      <th>Decision</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {vendors.map((v: any) => (
                      <tr key={v.id} onClick={() => router.push(`/vendors/${v.id}`)}>
                        <td>
                          <div className="name">{v.name}</div>
                          <div className="muted">{v.category}</div>
                        </td>
                        <td><TypeBadge type={v.vendor_type} /></td>
                        <td><TierBadge tier={v.tier} /></td>
                        <td className="mono">{v.inherent ?? "—"}</td>
                        <td className="mono">{v.residual ?? "—"}</td>
                        <td><RiskBadge band={v.band} /></td>
                        <td><DecisionText decision={v.decision} /></td>
                        <td className="muted">{v.assessment_status === "complete" ? v.status : v.assessment_status}</td>
                        <td>
                          <button
                            className="btn btn-danger btn-sm"
                            title="Delete vendor"
                            disabled={deletingId === v.id}
                            onClick={(e) => remove(e, v)}
                          >
                            {deletingId === v.id ? "…" : "Delete"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {data.expiring_evidence.length > 0 && (
              <>
                <div className="section-title">Expiring / expired evidence</div>
                <div className="card">
                  {data.expiring_evidence.map((e: any, i: number) => (
                    <div className="kv" key={i}>
                      <span className="k">{e.vendor} — {e.document}</span>
                      <span className={e.expired ? "badge critical" : "badge medium"}>
                        {e.expired ? "expired" : "expires"} {e.expires_at}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </>
        )}
      </div>

      {showAdd && (
        <AddVendorModal
          onClose={() => {
            setShowAdd(false);
            load();
          }}
        />
      )}
    </>
  );
}
