"use client";

export function RiskBadge({ band }: { band?: string | null }) {
  if (!band) return <span className="badge neutral">n/a</span>;
  return <span className={`badge ${band} dot`}>{band}</span>;
}

export function TierBadge({ tier }: { tier?: number | null }) {
  if (!tier) return <span className="badge neutral">-</span>;
  const cls = tier === 1 ? "critical" : tier === 2 ? "high" : "neutral";
  return <span className={`badge ${cls}`}>Tier {tier}</span>;
}

const DECISION_LABEL: Record<string, string> = {
  approve: "APPROVE",
  approve_with_conditions: "APPROVE W/ CONDITIONS",
  block: "BLOCK",
  pending: "PENDING",
};

export function DecisionText({ decision }: { decision?: string | null }) {
  const d = decision || "pending";
  return <span className={`decision ${d}`}>{DECISION_LABEL[d] || d}</span>;
}

export function TypeBadge({ type }: { type?: string | null }) {
  if (type === "ai_agent") return <span className="badge ai">AI Agent</span>;
  if (type === "mcp") return <span className="badge ai">MCP Server</span>;
  return <span className="badge neutral">SaaS</span>;
}

function bandForScore(score: number): string {
  if (score >= 75) return "critical";
  if (score >= 55) return "high";
  if (score >= 35) return "medium";
  return "low";
}

const BAND_COLOR: Record<string, string> = {
  low: "#34d399",
  medium: "#fbbf24",
  high: "#fb923c",
  critical: "#f87171",
};

export function Gauge({ score, label }: { score: number; label: string }) {
  const r = 54;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const color = BAND_COLOR[bandForScore(score)];
  return (
    <div className="gauge">
      <svg width="128" height="128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#161d2b" strokeWidth="11" />
        <circle
          cx="64"
          cy="64"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="11"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
        />
      </svg>
      <div className="num" style={{ flexDirection: "column" }}>
        <b style={{ color }}>{Math.round(score)}</b>
        <small>{label}</small>
      </div>
    </div>
  );
}

export function Bar({ pct, color }: { pct: number; color?: string }) {
  return (
    <div className="bar">
      <span style={{ width: `${Math.max(0, Math.min(100, pct))}%`, background: color || "#22d3ee" }} />
    </div>
  );
}

type TrendPoint = { at: string; residual: number; band?: string; trigger?: string };

export function TrendChart({
  points,
  height = 180,
}: {
  points: TrendPoint[];
  height?: number;
}) {
  const W = 720;
  const H = height;
  const padX = 36;
  const padY = 22;
  const innerW = W - padX * 2;
  const innerH = H - padY * 2;

  // Ensure at least two points so the line is visible even for a single score.
  const data =
    points.length === 1 ? [{ ...points[0] }, { ...points[0] }] : points;
  if (!data.length) return <div className="empty">No risk history yet.</div>;

  const xFor = (i: number) => padX + (data.length === 1 ? innerW / 2 : (i / (data.length - 1)) * innerW);
  const yFor = (v: number) => padY + innerH - (Math.max(0, Math.min(100, v)) / 100) * innerH;

  const linePts = data.map((p, i) => `${xFor(i)},${yFor(p.residual)}`).join(" ");
  const areaPts = `${padX},${padY + innerH} ${linePts} ${padX + innerW},${padY + innerH}`;
  const last = data[data.length - 1];
  const lastColor = BAND_COLOR[last.band || bandForScore(last.residual)];

  const gridBands = [
    { y: 75, label: "critical", color: "#f87171" },
    { y: 55, label: "high", color: "#fb923c" },
    { y: 35, label: "medium", color: "#fbbf24" },
  ];

  return (
    <div className="trend">
      <svg width="100%" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img">
        <defs>
          <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={lastColor} stopOpacity="0.35" />
            <stop offset="100%" stopColor={lastColor} stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {gridBands.map((g) => (
          <g key={g.label}>
            <line
              x1={padX}
              x2={padX + innerW}
              y1={yFor(g.y)}
              y2={yFor(g.y)}
              stroke={g.color}
              strokeOpacity="0.18"
              strokeDasharray="4 4"
            />
            <text x={padX - 8} y={yFor(g.y) + 3} fontSize="10" fill="#5b6b82" textAnchor="end">
              {g.y}
            </text>
          </g>
        ))}

        <polygon points={areaPts} fill="url(#trendFill)" />
        <polyline points={linePts} fill="none" stroke={lastColor} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

        {data.map((p, i) => (
          <circle
            key={i}
            cx={xFor(i)}
            cy={yFor(p.residual)}
            r={i === data.length - 1 ? 5 : 3}
            fill={BAND_COLOR[p.band || bandForScore(p.residual)]}
            stroke="#0b0f17"
            strokeWidth="1.5"
          >
            <title>
              {new Date(p.at).toLocaleString()} — residual {Math.round(p.residual)} ({p.trigger || "assessment"})
            </title>
          </circle>
        ))}
      </svg>
    </div>
  );
}
