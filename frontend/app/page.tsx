"use client";

import { Fragment, useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "./lib/api";
import { RiskBadge, TierBadge, DecisionText, TypeBadge } from "./components/ui";
import { AddVendorModal } from "./components/AddVendorModal";

export default function Portfolio() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState("all");
  const [exporting, setExporting] = useState(false);

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
  const visibleVendors = vendors.filter((vendor: any) => {
    const needle = query.trim().toLowerCase();
    const matchesSearch = !needle || [vendor.name, vendor.category, vendor.vendor_type]
      .filter(Boolean)
      .some((value: string) => value.toLowerCase().includes(needle));
    const matchesRisk = riskFilter === "all" || vendor.band === riskFilter;
    return matchesSearch && matchesRisk;
  });
  const analytics = data?.analytics;

  async function exportPortfolio() {
    setExporting(true);
    try {
      await api.downloadPortfolioExport();
    } catch (error) {
      alert("Export failed: " + error);
    } finally {
      setExporting(false);
    }
  }

  return (
    <>
      <div className="topbar">
        <div>
          <h2>Vendor Risk Portfolio</h2>
          <div className="sub">{data?.org?.name} · {data?.org?.required_frameworks?.join(" · ")}</div>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn" onClick={exportPortfolio} disabled={exporting}>{exporting ? "Exporting…" : "Export CSV"}</button>
          <button className="btn btn-primary" onClick={() => setShowAdd(true)}>+ Add vendor</button>
        </div>
      </div>

      <div className="content">
        {loading && <div className="loading">Loading portfolio…</div>}
        {data?.error && (
          <div className="card">
            <b>Could not reach the Argus API.</b>
            <p className="hint">Start the backend on {api.base} (see the project README).</p>
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

            <div className="portfolio-insights">
              <div className="card insight-card">
                <div className="section-title" style={{ marginTop: 0 }}>Risk heatmap</div>
                <div className="heatmap" aria-label="Risk tier by risk-band heatmap">
                  <div />{["Critical", "High", "Medium", "Low"].map((band) => <div className="heat-label" key={band}>{band}</div>)}
                  {[1, 2, 3, 4].map((tier) => <Fragment key={tier}>
                    <div className="heat-label" key={`tier-${tier}`}>T{tier}</div>
                    {["critical", "high", "medium", "low"].map((band) => {
                      const count = analytics?.heatmap?.find((cell: any) => cell.tier === tier && cell.band === band)?.count || 0;
                      return <div key={`${tier}-${band}`} className={`heat-cell ${band}`} style={{ opacity: count ? Math.min(.35 + count * .16, 1) : .12 }} title={`Tier ${tier}, ${band}: ${count}`}>{count || "—"}</div>;
                    })}
                  </Fragment>)}
                </div>
              </div>
              <div className="card insight-card">
                <div className="section-title" style={{ marginTop: 0 }}>Concentration risk</div>
                {analytics?.concentration?.length ? analytics.concentration.slice(0, 5).map((item: any) => (
                  <div className="driver" key={item.category}><span>{item.category}</span><b>{item.count} vendor{item.count === 1 ? "" : "s"}</b></div>
                )) : <div className="empty">No vendor concentration yet.</div>}
                <div className="insight-alert"><span>Overdue reviews</span><b>{analytics?.overdue_reviews || 0}</b></div>
              </div>
              <div className="card insight-card">
                <div className="section-title" style={{ marginTop: 0 }}>Highest residual risk</div>
                {data.top_risky?.length ? data.top_risky.slice(0, 4).map((vendor: any) => (
                  <button className="risk-row" key={vendor.id} onClick={() => router.push(`/vendors/${vendor.id}`)}>
                    <span>{vendor.name}</span><span><RiskBadge band={vendor.band} /> <b>{Math.round(vendor.residual)}</b></span>
                  </button>
                )) : <div className="empty">No assessed vendors yet.</div>}
              </div>
            </div>

            <div className="section-heading">
              <div>
                <div className="section-title">All vendors</div>
                <div className="section-subtitle">{visibleVendors.length} of {vendors.length} vendors shown</div>
              </div>
              <div className="table-tools" aria-label="Vendor filters">
                <input
                  aria-label="Search vendors"
                  className="search-input"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search vendors"
                />
                <select aria-label="Filter by risk" value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                  <option value="all">All risk levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            </div>
            <div className="card" style={{ padding: 0 }}>
              {vendors.length === 0 ? (
                <div className="empty">No vendors yet. Add your first vendor to see the crew in action.</div>
              ) : visibleVendors.length === 0 ? (
                <div className="empty">No vendors match those filters. Clear the search or choose a different risk level.</div>
              ) : (
                <div className="table-scroll"><table className="table">
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
                    {visibleVendors.map((v: any) => (
                      <tr key={v.id} onClick={() => router.push(`/vendors/${v.id}`)} tabIndex={0} onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          router.push(`/vendors/${v.id}`);
                        }
                      }}>
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
                </table></div>
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
