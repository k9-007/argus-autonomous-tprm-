"""Curated vendor knowledge base.

Provides rich, realistic evidence for demo vendors so Argus produces a full,
compelling assessment fully offline. When live tools (Bright Data / GPT-5.6)
are configured, agents augment or override these with fetched data.

Each entry documents what a trust-center ingest / discovery pass would surface.
`doc_state` reflects the real-world reality that most trust-center docs are gated
behind request-access + NDA.
"""

from __future__ import annotations


# doc states: public | requested | nda_pending | granted | downloaded | parsed | expired
DEMO_VENDORS: dict[str, dict] = {
    "stripe.com": {
        "name": "Stripe",
        "website": "https://stripe.com",
        "trust_center_url": "https://stripe.com/legal/privacy-center",
        "trust_platform": "custom",
        "category": "Payments / Fintech Infrastructure",
        "vendor_type": "saas",
        "description": "Payment processing and financial infrastructure APIs.",
        "data_sensitivity": "regulated",  # cardholder data, PII
        "system_access": "production",
        "documents": [
            {"doc_type": "soc2_type2", "name": "SOC 2 Type II Report", "source": "trust_center",
             "state": "parsed", "issued_at": "2025-11-01", "expires_at": "2026-11-01",
             "parsed": {"report_type": "Type II", "period_months": 12, "opinion": "unqualified",
                        "auditor": "Deloitte", "scope": "Payments platform"}},
            {"doc_type": "iso27001", "name": "ISO/IEC 27001 Certificate", "source": "trust_center",
             "state": "parsed", "issued_at": "2025-03-15", "expires_at": "2028-03-15",
             "parsed": {"body": "Schellman (accredited)", "current": True}},
            {"doc_type": "pci_dss", "name": "PCI DSS Level 1 AoC", "source": "trust_center",
             "state": "parsed", "issued_at": "2026-01-15", "expires_at": "2027-01-15",
             "parsed": {"level": "Level 1 Service Provider"}},
            {"doc_type": "pentest", "name": "Penetration Test Executive Summary", "source": "trust_center",
             "state": "nda_pending", "parsed": {}},
            {"doc_type": "dpa", "name": "Data Processing Agreement", "source": "trust_center",
             "state": "public", "parsed": {"gdpr_scc": True, "subprocessors_listed": True}},
        ],
        "subprocessors": ["AWS", "Google Cloud", "Cloudflare"],
        "findings": [],
        "monitoring": [
            {"event_type": "cert_expiry", "severity": "low",
             "title": "TLS certificate healthy", "detail": "api.stripe.com cert valid, renews automatically."},
        ],
    },
    "cursor.com": {
        "name": "Cursor (Anysphere)",
        "website": "https://cursor.com",
        "trust_center_url": "https://trust.cursor.com/",
        "trust_platform": "vanta",
        "category": "AI Developer Tools",
        "vendor_type": "ai_agent",
        "description": "AI-powered code editor; agents read/write source code and run commands.",
        "data_sensitivity": "high",  # source code / IP
        "system_access": "limited",
        "documents": [
            # SOC 2 Type II is verifiable via the Microsoft 365 App Certification
            # registry (most recent cert date 2025-08-01); the full report is
            # available on request via the Vanta Trust Center.
            {"doc_type": "soc2_type2", "name": "SOC 2 Type II Report", "source": "trust_center",
             "state": "parsed", "issued_at": "2025-08-01", "expires_at": "2026-08-01",
             "parsed": {"report_type": "Type II", "period_months": 12, "opinion": "unqualified",
                        "auditor": "Independent CPA firm", "scope": "Cursor platform",
                        "note": "SOC 2 Type II certification verified via Microsoft 365 App "
                                "Certification registry; full report available on request."}},
            {"doc_type": "pentest", "name": "Penetration Test Report", "source": "trust_center",
             "state": "nda_pending", "parsed": {"note": "Available on request via trust.cursor.com"}},
            {"doc_type": "dpa", "name": "Data Processing Addendum", "source": "trust_center",
             "state": "public", "parsed": {"gdpr_scc": True, "url": "https://cursor.com/dpa"}},
            {"doc_type": "subprocessors", "name": "Subprocessor List", "source": "trust_center",
             "state": "public", "parsed": {}},
        ],
        "subprocessors": ["AWS", "OpenAI", "Anthropic", "Fireworks AI", "Pinecone"],
        "findings": [
            {"category": "ai_risk", "severity": "high",
             "title": "Code and prompts sent to third-party model providers",
             "detail": "Source code context is transmitted to OpenAI/Anthropic; retention and "
                       "training-use terms must be verified under a zero-retention agreement. "
                       "Cursor offers Privacy Mode (zero retention) which should be enforced by policy."},
            {"category": "compliance_gap", "severity": "medium",
             "title": "No ISO 27001 certification",
             "detail": "Anysphere is not ISO 27001 certified; SOC 2 Type II is the primary "
                       "third-party assurance. Acceptable for most buyers but note for ISO-mandated programs."},
        ],
        "monitoring": [
            {"event_type": "subprocessor", "severity": "medium",
             "title": "New model subprocessor added", "detail": "Fireworks AI added to subprocessor list."},
            {"event_type": "control", "severity": "low",
             "title": "Enterprise audit logging available", "detail": "Admin/security/auth audit logs with SIEM streaming (Splunk/Datadog/S3)."},
        ],
        "ai_profile": {
            "sends_data_to_models": True,
            "model_providers": ["OpenAI", "Anthropic", "Fireworks AI"],
            "data_retention": "Zero-retention available on Privacy Mode; default retains for abuse monitoring",
            "training_use": "Opt-out available; Privacy Mode disables training",
            "tool_permissions": "Reads/writes files, executes terminal commands with user approval",
            "autonomous_actions": "Agent mode runs multi-step edits/commands, but actions require user approval by default",
            # Exposure exists (ingests untrusted repo/web content) but is mitigated by
            # human-in-the-loop approval, so rated medium rather than high.
            "prompt_injection_exposure": "Medium - ingests untrusted repo content and web results, mitigated by user-approval gating",
        },
    },
    "acme-mcp.dev": {
        "name": "Acme MCP Connectors",
        "website": "https://acme-mcp.dev",
        "trust_center_url": None,
        "trust_platform": None,
        "category": "MCP Server / AI Tooling",
        "vendor_type": "mcp",
        "description": "Third-party MCP server exposing CRM, email and file tools to AI agents.",
        "data_sensitivity": "high",
        "system_access": "production",
        "documents": [
            {"doc_type": "dpa", "name": "Data Processing Agreement", "source": "vendor",
             "state": "requested", "parsed": {}},
        ],
        "subprocessors": ["Vercel", "Supabase"],
        "findings": [
            {"category": "ai_risk", "severity": "critical",
             "title": "Broad tool permissions with no scoped OAuth",
             "detail": "MCP server requests full read/write to CRM and email with a single static token; "
                       "no per-action consent and no audit log of agent actions."},
            {"category": "compliance_gap", "severity": "high",
             "title": "No SOC 2 or ISO 27001",
             "detail": "No third-party audit evidence available; security posture is self-attested only."},
        ],
        "monitoring": [
            {"event_type": "github_leak", "severity": "high",
             "title": "Potential secret in public repo", "detail": "API key pattern found in acme-mcp GitHub org."},
        ],
        "ai_profile": {
            "sends_data_to_models": True,
            "model_providers": ["Unknown"],
            "data_retention": "Undisclosed",
            "training_use": "Undisclosed",
            "tool_permissions": "Full CRM + email read/write via static token",
            "autonomous_actions": "Executes actions on behalf of agents without per-action consent",
            "prompt_injection_exposure": "Critical - tools act on untrusted model output with no guardrails",
        },
    },
}


# ---------------------------------------------------------------------------
# Trust Passport seed catalogue (common vendors mid-market companies use).
# Kept compact but broad so the network shows immediate value on day one.
# ---------------------------------------------------------------------------
_SEED_SAAS = [
    ("Stripe", "stripe.com", "Payments / Fintech"),
    ("Cursor (Anysphere)", "cursor.com", "AI Developer Tools"),
    ("OpenAI", "openai.com", "AI / LLM Provider"),
    ("Anthropic", "anthropic.com", "AI / LLM Provider"),
    ("Amazon Web Services", "aws.amazon.com", "Cloud Infrastructure"),
    ("Google Cloud", "cloud.google.com", "Cloud Infrastructure"),
    ("Microsoft Azure", "azure.microsoft.com", "Cloud Infrastructure"),
    ("Cloudflare", "cloudflare.com", "CDN / Security"),
    ("Datadog", "datadoghq.com", "Observability"),
    ("Snowflake", "snowflake.com", "Data Warehouse"),
    ("Databricks", "databricks.com", "Data / ML"),
    ("MongoDB Atlas", "mongodb.com", "Database"),
    ("Supabase", "supabase.com", "Database / Backend"),
    ("Vercel", "vercel.com", "Hosting / PaaS"),
    ("Netlify", "netlify.com", "Hosting / PaaS"),
    ("GitHub", "github.com", "Dev Platform"),
    ("GitLab", "gitlab.com", "Dev Platform"),
    ("Atlassian (Jira)", "atlassian.com", "Productivity"),
    ("Slack", "slack.com", "Collaboration"),
    ("Notion", "notion.so", "Productivity"),
    ("Figma", "figma.com", "Design"),
    ("Salesforce", "salesforce.com", "CRM"),
    ("HubSpot", "hubspot.com", "CRM / Marketing"),
    ("Zendesk", "zendesk.com", "Support"),
    ("Intercom", "intercom.com", "Support / Messaging"),
    ("Twilio", "twilio.com", "Communications"),
    ("SendGrid", "sendgrid.com", "Email"),
    ("Okta", "okta.com", "Identity"),
    ("Auth0", "auth0.com", "Identity"),
    ("1Password", "1password.com", "Secrets / Security"),
    ("PagerDuty", "pagerduty.com", "Incident Mgmt"),
    ("Segment", "segment.com", "Data / CDP"),
    ("Amplitude", "amplitude.com", "Analytics"),
    ("Mixpanel", "mixpanel.com", "Analytics"),
    ("Zoom", "zoom.us", "Video"),
    ("DocuSign", "docusign.com", "E-signature"),
    ("Workday", "workday.com", "HR / Finance"),
    ("Ramp", "ramp.com", "Fintech / Spend"),
    ("Brex", "brex.com", "Fintech / Spend"),
    ("Plaid", "plaid.com", "Fintech / Data"),
]

_SEED_AI = [
    ("Perplexity", "perplexity.ai", "AI Search"),
    ("Hugging Face", "huggingface.co", "AI / ML Platform"),
    ("Pinecone", "pinecone.io", "Vector DB"),
    ("LangChain", "langchain.com", "AI Framework"),
    ("Fireworks AI", "fireworks.ai", "AI Inference"),
    ("Together AI", "together.ai", "AI Inference"),
    ("ElevenLabs", "elevenlabs.io", "AI Voice"),
    ("Replicate", "replicate.com", "AI Inference"),
]


def passport_seed() -> list[dict]:
    """Return the seed catalogue for the global Trust Passport network."""
    out: list[dict] = []
    for name, domain, category in _SEED_SAAS:
        out.append(
            {"name": name, "vendor_key": domain, "website": f"https://{domain}",
             "category": category, "vendor_type": "saas"}
        )
    for name, domain, category in _SEED_AI:
        out.append(
            {"name": name, "vendor_key": domain, "website": f"https://{domain}",
             "category": category, "vendor_type": "ai_agent"}
        )
    # Merge in richer demo fixtures (override basics with full evidence).
    for domain, data in DEMO_VENDORS.items():
        entry = {
            "name": data["name"],
            "vendor_key": domain,
            "website": data.get("website"),
            "category": data.get("category"),
            "vendor_type": data.get("vendor_type", "saas"),
            "trust_center_url": data.get("trust_center_url"),
        }
        # replace if already present
        out = [e for e in out if e["vendor_key"] != domain]
        out.append(entry)
    return out


def lookup_demo(vendor_key: str) -> dict | None:
    return DEMO_VENDORS.get(vendor_key)
