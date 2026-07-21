# Argus — Demo Video Script (< 3 minutes)

Target length: **2:45**. Public YouTube, with clear audio. Speak in first person, upbeat but calm.

---

## Pre-record checklist

- [ ] Fresh portfolio: stop the backend, `rm backend/argus.db`, restart backend + frontend (so the portfolio starts empty).
- [ ] Both servers up: backend `http://127.0.0.1:8000`, frontend `http://localhost:3000`.
- [ ] Browser zoom ~110%, window maximized, notifications off, dark mode.
- [ ] Have the 3 examples ready: **Cursor** (link), **Stripe** (upload — a compliance pack of ≤25 files), **Acme MCP** (AI risk).
- [ ] Optional: set a working LLM key (`ARGUS_LLM_PROVIDER` + key) to show live reasoning; otherwise offline heuristics work fine.

---

## Script (timed)

### 0:00 – 0:20 · Hook + problem
**[SCREEN]** Empty Argus portfolio dashboard.

**[VOICEOVER]**
> "Every company now runs on dozens of SaaS and AI vendors — and someone has to vet each one's security before you can use it. At mid-market and AI-first companies there's no security analyst to do it, so it lands on an engineer, in spreadsheets, for weeks. This is **Argus** — an autonomous third-party risk management department, built as a crew of AI agents."

### 0:20 – 1:05 · Add a vendor → watch the crew (Cursor)
**[SCREEN]** Click **Add vendor** → name "Cursor", paste trust-center link `https://trust.cursor.com/` → **Assess vendor**. The live **agent-crew flow** lights up.

**[VOICEOVER]**
> "I add Cursor with just its trust-center link. Now watch: an orchestrator dispatches nine specialized agents — Intake, Discovery, Compliance, Questionnaire, AI-Vendor Risk, Scoring, Negotiation, Monitoring, and Executive. Each lights up as it works, in real time. In seconds it profiles the vendor, ingests evidence, and maps controls — the whole workflow a TPRM analyst would run manually."

**[SCREEN]** Click **View full report →**.

### 1:05 – 1:40 · Explainability + controls (Cursor detail)
**[SCREEN]** Vendor page: **control-coverage** headline, then the **score drivers**, then the **Compliance** tab.

**[VOICEOVER]**
> "Control coverage is front and center. Every risk score is fully explainable — here are the exact drivers that raise and lower it. And in Compliance, each control is rated against real evidence — compliant, partial, gated behind an NDA, or expired — with the exact artifact and citation. Claims without evidence count as non-compliant. Cursor is SOC 2 Type II certified, so it lands at **approve with conditions**, not a blanket block."

### 1:40 – 2:10 · The AI-vendor differentiator (Acme MCP)
**[SCREEN]** Add / open **Acme MCP Connectors** → **AI Risk** tab.

**[VOICEOVER]**
> "Here's what no traditional tool does. Acme is an MCP server — an AI vendor. Argus evaluates prompt-injection exposure, unscoped tool permissions, undisclosed data retention, and autonomous actions, mapping toward ISO 42001. Broad token access with no audit trail and no third-party audit means **critical risk — block**. That's the AI-vendor risk lens, first-class."

### 2:10 – 2:35 · Evidence + real-time monitoring (Stripe)
**[SCREEN]** Open **Stripe** (added via upload) → **Evidence** tab (show parsed docs) → **Monitoring** tab (live residual-risk graph).

**[VOICEOVER]**
> "With Stripe I uploaded its actual compliance pack — Argus parsed each PDF, extracted dates, and cited it. And risk isn't a one-time score: continuous monitoring tracks changes and re-scores over time, shown here as a live trend graph. Every assessment also enriches a shared Trust Passport, so the next company to assess this vendor starts ahead."

### 2:35 – 2:45 · Close + how it's built
**[SCREEN]** Back to the portfolio (now populated) or the architecture diagram.

**[VOICEOVER]**
> "Argus turns weeks of vendor security work into minutes — an autonomous department for teams that never had one. Built on FastAPI and Next.js, with GPT-5.6 / Gemini reasoning and deterministic fallbacks so it runs anywhere. Thanks for watching."

---

## Voiceover-only version (paste into a teleprompter)

Every company now runs on dozens of SaaS and AI vendors, and someone has to vet each one's security before you can use it. At mid-market and AI-first companies there's no analyst to do it — so it lands on an engineer, in spreadsheets, for weeks. This is Argus: an autonomous third-party risk management department, built as a crew of AI agents.

I add Cursor with just its trust-center link. An orchestrator dispatches nine specialized agents — intake, discovery, compliance, questionnaire, AI-vendor risk, scoring, negotiation, monitoring, and executive — and each lights up as it works, in real time, running the whole workflow an analyst would do by hand.

Control coverage is front and center, and every score is fully explainable, with the exact drivers that move it. In compliance, each control is judged against real evidence — compliant, partial, gated behind an NDA, or expired — with the citation to prove it. Cursor is SOC 2 Type II certified, so it lands at approve-with-conditions, not a blanket block.

Here's what no traditional tool does. Acme is an MCP server — an AI vendor. Argus evaluates prompt injection, unscoped tool permissions, undisclosed retention, and autonomous actions, mapping toward ISO 42001. Broad token access with no audit trail and no third-party audit means critical risk — block.

With Stripe, I uploaded its real compliance pack — Argus parsed each PDF, extracted the dates, and cited it. And risk isn't a one-time score: continuous monitoring re-scores over time, shown as a live trend graph. Every assessment also enriches a shared Trust Passport, so the next company starts ahead.

Argus turns weeks of vendor security work into minutes — an autonomous department for teams that never had one. Built on FastAPI and Next.js, with GPT-5.6 and Gemini reasoning and deterministic fallbacks so it runs anywhere. Thanks for watching.

---

## Recording tips

- Record at 1080p+; screen capture at 30 fps is fine.
- Do one silent screen-capture pass, then record voiceover over it — easier than doing both live.
- Keep the crew-flow animation on screen long enough to see nodes go active → done (it's the "wow").
- Trim dead air; aim to finish under 3:00 with buffer.

---

## ⚠️ Note on the "built with Codex" requirement

OpenAI Build Week requires the demo video to explain **how you used Codex + GPT-5.6**, and asks for a Codex `/feedback` session ID. If you did **not** build this with Codex, do **not** claim you did in the video — that risks disqualification. Either (a) do genuine work in Codex now and narrate that honestly, or (b) submit to a hackathon that fits, and keep the "how it's built" line about GPT-5.6/Gemini + AI-assisted development as written above.
