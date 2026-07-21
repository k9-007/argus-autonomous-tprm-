"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "../lib/auth";

const items = [
  { href: "/", label: "Portfolio" },
  { href: "/activity", label: "Agent Activity" },
  { href: "/passport", label: "Trust Passport Network" },
];

export function Sidebar() {
  const path = usePathname();
  const { org, user, logout } = useAuth();
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="eye">A</div>
        <div>
          <h1>Argus</h1>
          <span>Autonomous TPRM</span>
        </div>
      </div>
      <nav className="nav">
        {items.map((it) => {
          const active = it.href === "/" ? path === "/" : path.startsWith(it.href);
          return (
            <Link key={it.href} href={it.href} className={active ? "active" : ""}>
              {it.label}
            </Link>
          );
        })}
      </nav>
      <div className="sidebar-foot">
        <div style={{ marginBottom: 8, color: "var(--text-dim)" }}>
          <b style={{ color: "var(--text)" }}>{org?.name}</b>
          <br />
          {user?.email}
        </div>
        <button className="btn btn-ghost" style={{ padding: "4px 8px", fontSize: 12 }} onClick={logout}>
          Sign out
        </button>
      </div>
    </aside>
  );
}
