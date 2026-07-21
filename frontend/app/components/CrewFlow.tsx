"use client";

type Item = { seq: number; agent: string; message: string; status: string };

type CrewMember = {
  name: string;
  role: string;
  output: string;
  mark: string;
  lane: "orchestrate" | "assess" | "decide";
};

const CREW: CrewMember[] = [
  { name: "Orchestrator", role: "Coordinates the assessment", output: "Assessment plan", mark: "01", lane: "orchestrate" },
  { name: "Intake Agent", role: "Profiles vendor exposure", output: "Tier & data flow", mark: "02", lane: "assess" },
  { name: "Discovery Agent", role: "Collects public evidence", output: "Evidence inventory", mark: "03", lane: "assess" },
  { name: "Compliance Agent", role: "Maps controls to evidence", output: "Control coverage", mark: "04", lane: "assess" },
  { name: "Questionnaire Agent", role: "Completes SIG & CAIQ", output: "Cited responses", mark: "05", lane: "assess" },
  { name: "AI-Vendor Risk Agent", role: "Assesses AI-specific risk", output: "AI risk findings", mark: "06", lane: "assess" },
  { name: "Risk Scoring Agent", role: "Calculates residual exposure", output: "Risk drivers", mark: "07", lane: "decide" },
  { name: "Negotiation Agent", role: "Routes evidence access", output: "NDA & outreach", mark: "08", lane: "decide" },
  { name: "Monitoring Agent", role: "Sets continuous watch", output: "Review cadence", mark: "09", lane: "decide" },
  { name: "Executive Agent", role: "Builds the recommendation", output: "Decision brief", mark: "10", lane: "decide" },
];

type NodeStatus = "pending" | "active" | "done" | "attention";

function activityFor(agent: string, items: Item[]) {
  return items.filter((item) => item.agent === agent).at(-1);
}

function statusFor(agent: string, items: Item[], allDone: boolean): NodeStatus {
  const latest = activityFor(agent, items);
  if (!latest) return allDone ? "done" : "pending";
  if (latest.status === "warn") return "attention";
  if (allDone || latest.status === "done") return "done";
  return "active";
}

export function CrewFlow({ items, done }: { items: Item[]; done: boolean }) {
  const states = CREW.map((member) => statusFor(member.name, items, done));
  const active = CREW.find((member, index) => states[index] === "active");
  const completed = states.filter((state) => state === "done").length;
  const warnings = states.filter((state) => state === "attention").length;

  return (
    <section className="crew-console" aria-label="Autonomous assessment crew" aria-live="polite">
      <div className="crew-console-head">
        <div>
          <div className="eyebrow">Autonomous assessment crew</div>
          <div className="crew-headline">
            {done ? "Decision package ready" : active ? `${active.name.replace(" Agent", "")} is working` : "Preparing specialist crew"}
          </div>
          <p>The orchestrator hands context between specialized agents; each output becomes grounded input for the next decision.</p>
        </div>
        <div className={`crew-state ${done ? "complete" : "running"}`}>
          <span className={done ? "crew-check" : "live-dot"}>{done ? "✓" : ""}</span>
          <span>{done ? "Complete" : "Live run"}</span>
        </div>
      </div>

      <div className="crew-metrics" aria-label="Crew progress">
        <div><b>{completed}<small>/{CREW.length}</small></b><span>stages complete</span></div>
        <div><b>{items.length}</b><span>recorded handoffs</span></div>
        <div><b className={warnings ? "warn-text" : ""}>{warnings || "—"}</b><span>attention items</span></div>
      </div>

      <div className="crew-lanes">
        {(["orchestrate", "assess", "decide"] as const).map((lane) => (
          <div className="crew-lane" key={lane}>
            <div className="crew-lane-label">{lane === "orchestrate" ? "Orchestrate" : lane === "assess" ? "Assess & verify" : "Decide & protect"}</div>
            <div className="crew-lane-nodes">
              {CREW.filter((member) => member.lane === lane).map((member) => {
                const state = statusFor(member.name, items, done);
                const update = activityFor(member.name, items);
                return (
                  <article className={`crew-agent ${state}`} key={member.name}>
                    <div className="crew-agent-top">
                      <span className="crew-mark">{state === "done" ? "✓" : state === "active" ? <span className="spinner" /> : state === "attention" ? "!" : member.mark}</span>
                      <span className="crew-status">{state === "active" ? "Working" : state === "done" ? "Complete" : state === "attention" ? "Needs review" : "Queued"}</span>
                    </div>
                    <strong>{member.name.replace(" Agent", "")}</strong>
                    <span className="crew-role">{member.role}</span>
                    <div className="crew-output"><span>Delivers</span>{member.output}</div>
                    {update && <div className="crew-update" title={update.message}>{update.message}</div>}
                  </article>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
