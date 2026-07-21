"""Standard security questionnaire engine (SIG Lite + CAIQ v4 subsets).

Auto-answers questions from available evidence and cites the source document.
Unbacked answers are flagged as low-confidence self-attestation (the weakest
form of assurance), matching real TPRM practice.
"""

from __future__ import annotations

# Each question maps to the evidence (doc_types) that can answer it "Yes".
SIG_LITE = [
    ("IS-01", "Does the vendor maintain a formal information security program?", ["soc2_type2", "iso27001"]),
    ("IS-02", "Is data encrypted in transit and at rest?", ["soc2_type2", "iso27001", "pentest"]),
    ("IS-03", "Are logical access controls and least privilege enforced?", ["soc2_type2", "iso27001"]),
    ("IS-04", "Is there a documented incident response process?", ["soc2_type2", "iso27001"]),
    ("IS-05", "Are penetration tests performed at least annually?", ["pentest", "pci_dss"]),
    ("IS-06", "Is there a business continuity / disaster recovery plan?", ["soc2_type2", "bcdr", "iso27001"]),
    ("IS-07", "Does the vendor manage subprocessor / fourth-party risk?", ["subprocessors", "soc2_type2", "dpa"]),
    ("PR-01", "Is a GDPR-compliant DPA with SCCs available?", ["dpa"]),
    ("PR-02", "Are subprocessors disclosed and kept current?", ["subprocessors", "dpa"]),
    ("CO-01", "Does the vendor hold a current SOC 2 Type II or ISO 27001?", ["soc2_type2", "iso27001"]),
]

CAIQ_V4 = [
    ("AIS-01", "Are application security testing results available?", ["pentest", "soc2_type2"]),
    ("DSP-01", "Is customer data segregated in multi-tenant systems?", ["soc2_type2", "iso27001"]),
    ("EKM-01", "Is encryption key management documented?", ["soc2_type2", "iso27001"]),
    ("GRC-01", "Is there an established governance & risk program?", ["soc2_type2", "iso27001"]),
    ("IVS-01", "Are infrastructure vulnerabilities scanned regularly?", ["pentest", "soc2_type2"]),
    ("TVM-01", "Is a threat & vulnerability management program in place?", ["soc2_type2", "iso27001"]),
]

# AI-specific questions layered on for AI/agent/MCP vendors (maps toward ISO 42001).
AI_ADDENDUM = [
    ("AI-01", "Is customer data excluded from model training by default?", ["iso42001", "ai_policy"]),
    ("AI-02", "Is a zero/limited data-retention option offered?", ["iso42001", "ai_policy", "dpa"]),
    ("AI-03", "Are tool/action permissions scoped and consent-gated?", ["iso42001", "ai_policy"]),
    ("AI-04", "Are prompt-injection defenses documented?", ["iso42001", "ai_policy"]),
]

QUESTIONNAIRES = {
    "SIG Lite": SIG_LITE,
    "CAIQ v4": CAIQ_V4,
}


def _usable(documents: list[dict]) -> dict[str, dict]:
    usable_states = {"parsed", "downloaded", "granted", "public"}
    return {d["doc_type"]: d for d in documents if d.get("state") in usable_states}


def answer_questionnaire(framework: str, documents: list[dict], include_ai: bool = False) -> dict:
    questions = list(QUESTIONNAIRES.get(framework, []))
    if include_ai and framework == "SIG Lite":
        questions = questions + AI_ADDENDUM
    docs = _usable(documents)
    answers = []
    answered_yes = 0
    for qid, text, evidence_types in questions:
        matched = next((t for t in evidence_types if t in docs), None)
        if matched:
            answers.append({
                "id": qid,
                "question": text,
                "answer": "Yes",
                "evidence": docs[matched]["name"],
                "confidence": "high",
            })
            answered_yes += 1
        else:
            answers.append({
                "id": qid,
                "question": text,
                "answer": "Unverified",
                "evidence": None,
                "confidence": "low",
            })
    total = len(questions) or 1
    return {
        "framework": framework,
        "answers": answers,
        "answered": answered_yes,
        "total": len(questions),
        "completion_pct": round(100 * answered_yes / total, 1),
    }
