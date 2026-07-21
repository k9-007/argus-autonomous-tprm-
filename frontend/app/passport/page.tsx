"use client";

import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { TypeBadge } from "../components/ui";

export default function PassportNetwork() {
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    api.passport().then(setData).catch(() => setData({ error: true }));
  }, []);

  return (
    <>
      <div className="topbar">
        <div>
          <h2>Trust Passport Network</h2>
          <div className="sub">Shared public evidence metadata — tenant-uploaded reports and risk scores stay private</div>
        </div>
      </div>
      <div className="content">
        {!data && <div className="loading">Loading network…</div>}
        {data && !data.error && (
          <>
            <div className="cards">
              <div className="card stat">
                <div className="label">Vendors in network</div>
                <div className="value">{data.total}</div>
                <div className="foot">Seeded common vendors + assessed</div>
              </div>
              <div className="card stat">
                <div className="label">Assessed passports</div>
                <div className="value" style={{ color: "var(--accent)" }}>{data.assessed}</div>
                <div className="foot">Reused on the next org's assessment</div>
              </div>
              <div className="card stat">
                <div className="label">Vendor-claimed</div>
                <div className="value">{data.claimed}</div>
                <div className="foot">Two-sided evidence maintenance</div>
              </div>
              <div className="card stat">
                <div className="label">Network effect</div>
                <div className="value" style={{ color: "var(--emerald)" }}>↑</div>
                <div className="foot">Each assessment enriches the graph</div>
              </div>
            </div>

            <div className="section-title">Vendors</div>
            <div className="card" style={{ padding: 0 }}>
              <table className="table">
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Category</th>
                    <th>Type</th>
                    <th>Assessments</th>
                    <th>Last residual</th>
                  </tr>
                </thead>
                <tbody>
                  {data.passports.map((p: any) => (
                    <tr key={p.vendor_key}>
                      <td>
                        <div className="name">{p.name}</div>
                        <div className="muted mono">{p.vendor_key}</div>
                      </td>
                      <td className="muted">{p.category}</td>
                      <td><TypeBadge type={p.vendor_type} /></td>
                      <td className="mono">{p.assessments_count}</td>
                      <td className="mono">{p.last_residual ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </>
  );
}
