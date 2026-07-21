"use client";

type Item = { seq: number; agent: string; message: string; status: string };

// The autonomous crew, in execution order. The Orchestrator plans and dispatches
// every downstream agent, so it sits at the top of the flow.
const CREW: { name: string; short: string }[] = [
  { name: "Orchestrator", short: "Plan" },
  { name: "Intake Agent", short: "Profile & tier" },
  { name: "Discovery Agent", short: "Evidence" },
  { name: "Compliance Agent", short: "Controls" },
  { name: "Questionnaire Agent", short: "SIG / CAIQ" },
  { name: "AI-Vendor Risk Agent", short: "AI risk" },
  { name: "Risk Scoring Agent", short: "Residual score" },
  { name: "Negotiation Agent", short: "NDA / outreach" },
  { name: "Monitoring Agent", short: "Continuous watch" },
  { name: "Executive Agent", short: "Decision" },
];

type NodeStatus = "pending" | "active" | "done";

function statusFor(agent: string, items: Item[], allDone: boolean): NodeStatus {
  const mine = items.filter((it) => it.agent === agent);
  if (!mine.length) return "pending";
  if (allDone) return "done";
  const last = mine[mine.length - 1];
  if (last.status === "done") return "done";
  return "active";
}

export function CrewFlow({ items, done }: { items: Item[]; done: boolean }) {
  return (
    <div className="crewflow">
      <div className="crewflow-title">Autonomous agent crew</div>
      <div className="crewflow-track">
        {CREW.map((a, i) => {
          const st = statusFor(a.name, items, done);
          return (
            <div className="crewflow-node-wrap" key={a.name}>
              <div className={`crewflow-node ${st}`}>
                <div className="cf-dot">
                  {st === "done" ? "✓" : st === "active" ? <span className="spinner" /> : i}
                </div>
                <div className="cf-labels">
                  <div className="cf-name">{a.name.replace(" Agent", "")}</div>
                  <div className="cf-short">{a.short}</div>
                </div>
              </div>
              {i < CREW.length - 1 && <div className={`crewflow-arrow ${st === "done" ? "done" : ""}`} />}
            </div>
          );
        })}
      </div>
    </div>
  );
}
