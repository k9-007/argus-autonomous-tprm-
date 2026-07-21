"use client";

import { useState } from "react";
import { useAuth } from "../lib/auth";

export function AuthScreen() {
  const { login, signup, demo } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [name, setName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function go() {
    setErr("");
    setBusy(true);
    try {
      if (mode === "login") await login(email, password);
      else await signup(name, email, password, orgName);
    } catch (e: any) {
      setErr(String(e.message || e).replace(/^\d+\s*/, ""));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 420 }}>
        <div className="brand" style={{ justifyContent: "center", marginBottom: 20 }}>
          <div className="eye">A</div>
          <div>
            <h1>Argus</h1>
            <span>Autonomous TPRM</span>
          </div>
        </div>

        <div className="modal" style={{ maxWidth: 420 }}>
          <h3>{mode === "login" ? "Sign in" : "Create your account"}</h3>
          <p className="hint">
            {mode === "login"
              ? "Access your vendor risk portfolio."
              : "Spin up a new company workspace in seconds."}
          </p>

          {mode === "signup" && (
            <>
              <div className="field">
                <label>Your name</label>
                <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Founder" />
              </div>
              <div className="field">
                <label>Company / org name</label>
                <input value={orgName} onChange={(e) => setOrgName(e.target.value)} placeholder="NewCo Inc." />
              </div>
            </>
          )}
          <div className="field">
            <label>Work email</label>
            <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" />
          </div>
          <div className="field">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              onKeyDown={(e) => e.key === "Enter" && go()}
            />
          </div>

          {err && <div style={{ color: "var(--red)", fontSize: 13, marginBottom: 10 }}>{err}</div>}

          <button className="btn btn-primary" style={{ width: "100%" }} onClick={go} disabled={busy}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>

          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 14, fontSize: 13 }}>
            <button
              className="btn btn-ghost"
              style={{ padding: 0, border: "none" }}
              onClick={() => setMode(mode === "login" ? "signup" : "login")}
            >
              {mode === "login" ? "Create an account" : "Have an account? Sign in"}
            </button>
            <button className="btn btn-ghost" style={{ padding: 0, border: "none", color: "var(--accent)" }} onClick={() => demo()}>
              Use demo account →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
