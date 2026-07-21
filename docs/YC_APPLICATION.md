# Argus — YC Application (draft answers)

Reusable draft responses for the standard YC application. Tighten to the voice of
the founder(s) before submitting.

## Company

**What does your company do? (one line)**
Argus is an autonomous Third-Party Risk Management department — a crew of AI agents
that assesses and continuously monitors a company's vendors (including AI tools and
agents), so teams without a security analyst get enterprise-grade vendor due diligence
in minutes.

**Describe what your company does in 50 characters or less.**
Autonomous vendor risk management, AI-native.

## Problem

Every company now depends on dozens of SaaS and AI vendors. Before adopting each one,
someone has to vet its security posture — collect SOC 2 / ISO reports, read the DPA,
check for breaches, map controls to frameworks, fill a 100–300 question security
questionnaire, and keep watching for changes. At mid-market and AI-first companies
there is **no GRC analyst** to do this, so it lands on an engineer or ops lead doing
it in spreadsheets and email. Reviews take weeks, block deals, and go stale the day
they finish. AI vendors (tools, agents, MCP servers) make it worse: they're the
fastest-growing, riskiest vendor class and traditional TPRM has no playbook for them.

## Insight / Why now

Vendor risk is a **context + network** problem, and it's newly automatable:
- Agents can now do the whole job end-to-end (research, read documents, map controls,
  score, monitor), not just draft answers.
- AI/MCP vendors are exploding and need a new risk lens (prompt injection, tool
  permissions, data retention, autonomous actions) — an emerging category with no incumbent.
- The companies most exposed (mid-market, AI-first) are exactly the ones incumbents
  (enterprise-priced, analyst-augmenting) ignore.

## Product

Add a vendor by uploading its compliance pack or pasting its trust-center link. A crew
of nine agents autonomously profiles and tiers the vendor, ingests evidence (handling
the reality that ~90% of trust-center docs are gated behind NDA), maps it to SOC 2 /
ISO 27001 / GDPR / HIPAA / PCI / NIST / ISO 42001, auto-completes SIG/CAIQ with cited
evidence, computes an explainable residual-risk score and decision, and arms continuous
monitoring. Everything renders in a portfolio + per-vendor dashboard.

## Moat / defensibility

- **Trust Passport network effect:** shared, evidence-cited vendor profiles that get
  richer with every assessment across every customer — siloed enterprise deployments
  can't replicate this.
- **AI-vendor risk corpus:** a growing structured library of AI/agent/MCP risk profiles
  becomes the reference layer as this vendor class scales.
- **System of record:** becomes the vendor-risk register + monitoring backbone for
  companies that never had one.

## Market

TPRM / vendor security is large and enterprise-locked (SecureOS, Vanta, UpGuard,
Diligence; procurement-side: Zip). The underserved mid-market + the entirely new
AI-vendor layer is the entry point to a horizontal "trust graph" for the vendor economy.

## Why us

Backend / distributed-systems background — able to build convincing autonomous
multi-agent risk infrastructure quickly (this working prototype was built in a
hackathon on top of open-source foundations using Codex + GPT-5.6).

## Business model

Self-serve PLG: free for the first N vendor assessments, then per-seat or
per-monitored-vendor subscription (~$50–$500/mo mid-market). Expansion via continuous
monitoring tiers, more frameworks, audit-export/SSO, and a paid vendor-side Trust
Passport (network revenue).

## Competition — why we win

We don't compete on feature parity. We win a segment incumbents can't serve
(mid-market/AI-first, no analyst, no ERP), own the AI-vendor risk lens they lack, and
compound a data network effect their siloed deployments structurally cannot.
