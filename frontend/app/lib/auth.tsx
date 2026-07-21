"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { api, setToken, getToken } from "./api";

type AuthState = {
  ready: boolean;
  authed: boolean;
  user: any;
  org: any;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string, org_name: string) => Promise<void>;
  demo: () => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [org, setOrg] = useState<any>(null);

  useEffect(() => {
    (async () => {
      if (getToken()) {
        try {
          const me = await api.me();
          setUser(me.user);
          setOrg(me.org);
        } catch {
          setToken(null);
        }
      }
      setReady(true);
    })();
  }, []);

  function apply(res: any) {
    setToken(res.token);
    setUser(res.user);
    setOrg(res.org);
  }

  const value: AuthState = {
    ready,
    authed: !!user,
    user,
    org,
    login: async (email, password) => apply(await api.login({ email, password })),
    signup: async (name, email, password, org_name) =>
      apply(await api.signup({ name, email, password, org_name })),
    demo: async () => apply(await api.login({ email: "demo@acme.com", password: "demo1234" })),
    logout: () => {
      setToken(null);
      setUser(null);
      setOrg(null);
    },
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth outside provider");
  return c;
}
