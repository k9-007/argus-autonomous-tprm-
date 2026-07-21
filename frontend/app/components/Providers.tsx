"use client";

import { AuthProvider, useAuth } from "../lib/auth";
import { AuthScreen } from "./AuthScreen";
import { Sidebar } from "./Sidebar";

function Frame({ children }: { children: React.ReactNode }) {
  const { ready, authed } = useAuth();
  if (!ready) return <div className="loading">Loading Argus…</div>;
  if (!authed) return <AuthScreen />;
  return (
    <div className="app">
      <Sidebar />
      <div className="main">{children}</div>
    </div>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <Frame>{children}</Frame>
    </AuthProvider>
  );
}
