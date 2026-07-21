# Devpost Submission Checklist — OpenAI Build Week

**Project:** Argus — Autonomous Third-Party Risk Management
**Track:** Work & Productivity (workflow automation / back-office operations)

## Required items

- [ ] **Text description** — features & functionality (reuse the README intro + "What makes it different").
- [ ] **Demo video (< 3 min, YouTube, public)** — record the [Demo script](./README.md#demo-script--3-minutes).
  - Must have **audio** covering what you built and **how you used Codex + GPT-5.6**.
  - No third-party trademarks / copyrighted music without permission.
- [ ] **Public code repo** (or share privately with `testing@devpost.com` and `build-week-event@openai.com`).
- [ ] **README** documenting Codex collaboration + key decisions — done (see README "How we built this").
- [ ] **/feedback Codex Session ID** — capture the session where core functionality was built and paste it in the submission form.
- [ ] **Testable instance** so judges don't rebuild:
  - Local: follow the README Quickstart (runs offline, no keys needed).
  - Hosted (recommended): deploy backend (Railway/Render — `backend/Procfile`-style `uvicorn app.main:app`) and frontend (Vercel), set `NEXT_PUBLIC_API_URL`.
- [ ] **Category selection:** Work & Productivity.
- [ ] **Prior vs new work:** repo builds on MIT `Studio1HQ/tprm-agent`; the README + in-file notes distinguish vendored code from new hackathon work. Keep dated commit history as evidence.

## Judging criteria mapping (equally weighted)

- **Technological Implementation** — 9-agent orchestration, tool use, structured
  outputs, SSE activity feed, GPT-5.6 reasoning built with Codex.
- **Design** — coherent, runnable product: one input → live crew → polished
  portfolio + per-vendor dashboards (not a POC).
- **Potential Impact** — mid-market/AI-first companies with no analyst; concrete
  before/after (weeks of spreadsheets → minutes).
- **Quality of the Idea** — autonomous *department* + first-class AI-vendor risk +
  Trust Passport network effect.

## Before recording

1. `rm backend/argus.db` for a clean portfolio, then start both servers.
2. Have the three examples ready: Cursor (link), Stripe (upload), Acme MCP (AI risk).
3. Optional: set `OPENAI_API_KEY` + `ARGUS_LLM_MODEL=gpt-5.6` to show live reasoning.
