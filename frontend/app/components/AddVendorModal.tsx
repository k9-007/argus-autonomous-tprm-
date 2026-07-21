"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "../lib/api";
import { AssessmentStream } from "./AssessmentStream";

const EXAMPLES = [
  { name: "Stripe", website: "https://stripe.com", mode: "upload" },
  { name: "Cursor (Anysphere)", website: "https://cursor.com", trust: "https://trust.cursor.com/", mode: "link" },
  { name: "Acme MCP Connectors", website: "https://acme-mcp.dev", mode: "manual" },
];

export function AddVendorModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [mode, setMode] = useState<"link" | "upload">("link");
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [trustUrl, setTrustUrl] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [assessmentId, setAssessmentId] = useState<string | null>(null);
  const [vendorId, setVendorId] = useState<string | null>(null);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !assessmentId) onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [assessmentId, onClose]);

  async function submit() {
    if (!name.trim()) return;
    setSubmitting(true);
    try {
      const body: any = { name: name.trim(), website: website.trim() || undefined, intake_mode: mode };
      if (mode === "link") body.trust_center_url = trustUrl || website;
      const res = await api.createVendor(body);
      setVendorId(res.vendor_id);
      if (mode === "upload" && files.length) {
        const up = await api.uploadDocuments(res.vendor_id, files);
        setAssessmentId(up.assessment_id);
      } else {
        setAssessmentId(res.assessment_id);
      }
    } catch (e) {
      alert("Failed to add vendor: " + e);
      setSubmitting(false);
    }
  }

  function useExample(ex: any) {
    setName(ex.name);
    setWebsite(ex.website);
    setTrustUrl(ex.trust || "");
    setMode(ex.mode === "upload" ? "upload" : "link");
  }

  if (assessmentId) {
    return (
      <div className="modal-backdrop">
        <div className="modal" style={{ maxWidth: 680 }}>
          <h3>Assessing {name}</h3>
          <p className="hint">
            Argus's autonomous crew is running the full third-party risk assessment.
          </p>
          <AssessmentStream assessmentId={assessmentId} />
          <div className="modal-actions">
            <button className="btn btn-ghost" onClick={onClose}>
              Close
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                if (vendorId) router.push(`/vendors/${vendorId}`);
              }}
            >
              View full report →
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-labelledby="add-vendor-title">
        <h3 id="add-vendor-title">Add a vendor</h3>
        <p className="hint">Argus profiles, assesses and starts monitoring automatically.</p>

        <div className="mode-toggle">
          <button className={mode === "link" ? "active" : ""} onClick={() => setMode("link")}>
            <b>Trust-center link</b>
            Paste the vendor's trust center. Argus ingests it.
          </button>
          <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}>
            <b>Upload docs</b>
            Use the compliance pack you already have.
          </button>
        </div>

        <div className="field">
          <label>Vendor name</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Stripe" autoFocus />
        </div>
        <div className="field">
          <label>Website</label>
          <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://vendor.com" />
        </div>
        {mode === "link" && (
          <div className="field">
            <label>Trust center URL</label>
            <input
              value={trustUrl}
              onChange={(e) => setTrustUrl(e.target.value)}
              placeholder="https://trust.vendor.com/"
            />
          </div>
        )}
        {mode === "upload" && (
          <div className="field">
            <label>Compliance documents (PDF / text)</label>
            <input
              type="file"
              multiple
              accept=".pdf,.txt,.md"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
            {files.length > 0 && (
              <div className="hint" style={{ marginTop: 6 }}>{files.length} file(s) selected — Argus will parse and map them.</div>
            )}
          </div>
        )}

        <div style={{ marginTop: 10 }}>
          <div className="section-title" style={{ margin: "6px 0" }}>Try an example</div>
          <div className="pill-row">
            {EXAMPLES.map((ex) => (
              <button key={ex.name} className="pill" style={{ cursor: "pointer" }} onClick={() => useExample(ex)}>
                {ex.name}
              </button>
            ))}
          </div>
        </div>

        <div className="modal-actions">
          <button className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-primary" onClick={submit} disabled={submitting || !name}>
            {submitting ? "Starting crew..." : "Assess vendor"}
          </button>
        </div>
      </div>
    </div>
  );
}
