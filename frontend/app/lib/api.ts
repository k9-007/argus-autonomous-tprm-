const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "argus_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null) {
  if (typeof window === "undefined") return;
  if (t) window.localStorage.setItem(TOKEN_KEY, t);
  else window.localStorage.removeItem(TOKEN_KEY);
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function req(path: string, opts: RequestInit = {}) {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...(opts.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json();
}

export const api = {
  base: API,
  // auth
  signup: (body: any) => req("/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body: any) => req("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => req("/auth/me"),
  // core
  org: () => req("/org"),
  portfolio: () => req("/dashboard/portfolio"),
  passport: () => req("/dashboard/passport"),
  vendors: () => req("/vendors"),
  vendor: (id: string) => req(`/vendors/${id}`),
  createVendor: (body: any) => req("/vendors", { method: "POST", body: JSON.stringify(body) }),
  deleteVendor: (id: string) => req(`/vendors/${id}`, { method: "DELETE" }),
  reassess: (id: string) => req(`/vendors/${id}/assess`, { method: "POST" }),
  uploadDocuments: async (id: string, files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    const res = await fetch(`${API}/vendors/${id}/upload`, {
      method: "POST",
      headers: { ...authHeaders() },
      body: fd,
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
  assessment: (id: string) => req(`/assessments/${id}`),
  activity: (id: string, after = 0) => req(`/assessments/${id}/activity?after=${after}`),
  activityRecent: (limit = 60) => req(`/activity/recent?limit=${limit}`),
  streamUrl: (id: string) => `${API}/assessments/${id}/stream`,
};

export type Band = "low" | "medium" | "high" | "critical";
