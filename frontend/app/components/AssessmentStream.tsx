"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { CrewFlow } from "./CrewFlow";

type Item = { seq: number; agent: string; message: string; status: string };

export function AssessmentStream({
  assessmentId,
  onComplete,
}: {
  assessmentId: string;
  onComplete?: () => void;
}) {
  const [items, setItems] = useState<Item[]>([]);
  const [done, setDone] = useState(false);
  const lastSeq = useRef(0);
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let stop = false;
    async function poll() {
      while (!stop) {
        try {
          const res = await api.activity(assessmentId, lastSeq.current);
          if (res.activity?.length) {
            setItems((prev) => [...prev, ...res.activity]);
            lastSeq.current = res.activity[res.activity.length - 1].seq;
          }
          if (res.status === "complete" || res.status === "failed") {
            setDone(true);
            onComplete?.();
            break;
          }
        } catch (e) {
          // keep trying
        }
        await new Promise((r) => setTimeout(r, 450));
      }
    }
    poll();
    return () => {
      stop = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [assessmentId]);

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [items]);

  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        {done ? (
          <span className="badge low dot">Assessment complete</span>
        ) : (
          <>
            <span className="live-dot" />
            <span style={{ color: "var(--text-dim)", fontSize: 13 }}>
              The crew is working autonomously...
            </span>
          </>
        )}
      </div>
      <CrewFlow items={items} done={done} />
      <div className="feed" ref={feedRef}>
        {items.map((it, i) => (
          <div key={i} className={`feed-item ${it.status}`}>
            <div className="agent">{it.agent}</div>
            <div className="msg">
              {it.status === "working" && !done ? <span className="spinner" style={{ marginRight: 6 }} /> : null}
              {it.message}
            </div>
          </div>
        ))}
        {items.length === 0 && <div className="empty">Starting the crew...</div>}
      </div>
    </div>
  );
}
