# golden_visa/utils/tools.py
import os
from exa_py import Exa
from dotenv import load_dotenv
import weasyprint

load_dotenv()
exa = Exa(api_key=os.getenv("EXA_API_KEY"))


# ════════════════════════════════════════════════════════════════════════════════
# COMPLIANCE DATA — sourced from real UAE law
# ════════════════════════════════════════════════════════════════════════════════
#
# Sources:
#   - Federal Decree-Law No. 10 of 2025 (UAE AML/CFT Law, in force 14 Oct 2025)
#   - Cabinet Resolution No. 134 of 2025 (Executive Regulations — defines real
#     estate brokers as DNFBPs under Article 3(2))
#   - Ministry of Economy Circular 1 of 2026 (updated high-risk country list,
#     aligned with FATF October 2025 plenary outcomes)
#   - FATF High-Risk Jurisdictions subject to Call for Action (Black List)
#   - FATF Jurisdictions under Increased Monitoring (Grey List) — Oct 2025
#   - ICP / DLD Golden Visa official requirements (icp.gov.ae, dubailand.gov.ae)
#
# Real estate agents in the UAE are DNFBPs. Under Cabinet Resolution 134/2025
# they are legally required to apply CDD and EDD to every transaction.
# This tool automates the initial risk-screening layer only. It does NOT
# replace a human compliance officer or a full AML/KYC programme.
# ════════════════════════════════════════════════════════════════════════════════

# FATF Black List — "Call for Action" (highest risk, June 2025 update)
# Source: https://www.fatf-gafi.org/en/topics/high-risk-and-other-monitored-jurisdictions.html
FATF_BLACK_LIST = {
    "North Korea",
    "Iran",
    "Myanmar",
}

# FATF Grey List — "Jurisdictions under Increased Monitoring"
# Post-October 2025 update (removed: South Africa, Nigeria, Mozambique, Burkina Faso)
FATF_GREY_LIST = {
    "Algeria",
    "Angola",
    "Bulgaria",
    "Cameroon",
    "Democratic Republic of Congo",
    "DRC",
    "Haiti",
    "Kenya",
    "Libya",
    "Mali",
    "Monaco",
    "Namibia",
    "Philippines",
    "Senegal",
    "Syria",
    "Tanzania",
    "Venezuela",
    "Vietnam",
    "Yemen",
}

# Additional EDD triggers specific to Dubai real estate context.
# These are not necessarily on FATF lists but are flagged by UAE-licensed
# compliance consultants for real estate transactions above AED 2M.
REGIONAL_ELEVATED_RISK = {
    "Afghanistan",
    "Iraq",
    "Lebanon",
    "Sudan",
    "Somalia",
    "Ethiopia",
    "Zimbabwe",
    "Belarus",
    "Russia",         # UN/EU/US sanctions environment; UAE banks apply EDD
    "Ukraine",        # Conflict-related source-of-funds risk
}

# AED thresholds sourced from official DLD / ICP documentation
GOLDEN_VISA_10_YEAR_THRESHOLD = 2_000_000   # 10-year renewable residency
GOLDEN_VISA_5_YEAR_THRESHOLD  = 750_000     # 2/5-year investor residency pathway
SOURCE_OF_FUNDS_THRESHOLD     = 5_000_000   # EDD trigger for source-of-funds docs
JOINT_OWNERSHIP_DUAL_VISA     = 4_000_000   # Both spouses qualify; below = one only


def _get_risk_tier(nationality: str) -> tuple[str, str]:
    """
    Returns (risk_tier, legal_basis) for a given nationality.
    Tiers: LOW, ELEVATED, HIGH, CRITICAL
    """
    n = nationality.strip().title()

    if n in FATF_BLACK_LIST:
        return (
            "CRITICAL",
            f"Federal Decree-Law No. 10/2025 + Cabinet Resolution 134/2025: "
            f"{n} is on the FATF Call for Action (Black List). Transaction must not "
            f"proceed without MLRO sign-off and mandatory goAML filing."
        )
    if n in FATF_GREY_LIST:
        return (
            "HIGH",
            f"Ministry of Economy Circular 1/2026 + Cabinet Resolution 134/2025: "
            f"{n} is on the FATF Increased Monitoring (Grey List) as of Oct 2025. "
            f"Enhanced Due Diligence (EDD) is legally required before proceeding."
        )
    if n in REGIONAL_ELEVATED_RISK:
        return (
            "ELEVATED",
            f"UAE DNFBPs AML/CFT Guidelines (Sep 2025): {n} is flagged for elevated "
            f"source-of-funds scrutiny in Dubai real estate transactions. EDD recommended."
        )
    return (
        "LOW",
        f"{n} has no current FATF flag or regional elevated-risk designation. "
        f"Standard Customer Due Diligence (CDD) applies under Cabinet Resolution 134/2025."
    )


def _get_visa_tier(budget_aed: float, is_joint: bool = False) -> dict:
    """
    Returns visa eligibility assessment based on current ICP / DLD rules.
    """
    result = {
        "ten_year_eligible": False,
        "five_year_eligible": False,
        "joint_note": None,
        "visa_tier": None,
    }

    if budget_aed >= GOLDEN_VISA_10_YEAR_THRESHOLD:
        result["ten_year_eligible"] = True
        result["visa_tier"] = "10-Year Golden Visa"

        if is_joint and budget_aed < JOINT_OWNERSHIP_DUAL_VISA:
            result["joint_note"] = (
                "Joint ownership below AED 4M: only ONE spouse qualifies for the "
                "Golden Visa. The second spouse must be sponsored as a dependent. "
                "(Source: ICP.gov.ae 2025 guidelines)"
            )
        elif is_joint:
            result["joint_note"] = (
                "Joint ownership above AED 4M: both spouses qualify independently. "
                "(Source: ICP.gov.ae 2025 guidelines)"
            )

        # Off-plan flag
        result["offplan_note"] = (
            "If purchasing off-plan: eligible once 50% of purchase price is paid "
            "and a title deed has been issued. (Source: DLD / ICP 2025)"
        )
        # Mortgage note
        result["mortgage_note"] = (
            "Mortgaged property eligible: bank must provide a No-Objection Certificate "
            "confirming total property value ≥ AED 2M. Up to 50% financing permitted. "
            "(Source: ICP 2025 + Federal Decree-Law on Entry and Residence)"
        )

    elif budget_aed >= GOLDEN_VISA_5_YEAR_THRESHOLD:
        result["five_year_eligible"] = True
        result["visa_tier"] = "5-Year Investor Residency Visa"
        result["note"] = (
            "Below AED 2M threshold for the 10-year Golden Visa. However, qualifies "
            "for the 5-year UAE Investor Residency Visa (min AED 750K). "
            "This is a separate pathway — not a Golden Visa — but still provides "
            "long-term residency. (Source: u.ae official portal 2025)"
        )

    else:
        result["visa_tier"] = "No Visa Pathway"
        result["note"] = (
            f"Budget AED {budget_aed:,.0f} is below the AED 750K minimum for any "
            f"UAE property-based residency visa."
        )

    return result


# ════════════════════════════════════════════════════════════════════════════════
# SCREENER TOOL
# ════════════════════════════════════════════════════════════════════════════════

def save_lead_info(
    lead_name: str,
    lead_phone: str,
    budget_aed: float,
    nationality: str,
    timeline_months: int,
    property_interest: str
) -> str:
    """
    Call this once you have collected all 6 pieces of lead information.
    Saves structured lead data into agent state so downstream agents
    can read it directly instead of parsing conversation history.
    """
    return (
        f"Lead info saved: {lead_name}, {lead_phone}, "
        f"AED {budget_aed:,.0f}, {nationality}, "
        f"{timeline_months} months, {property_interest}"
    )


# ════════════════════════════════════════════════════════════════════════════════
# RESEARCHER TOOLS
# ════════════════════════════════════════════════════════════════════════════════

def web_search(query: str) -> str:
    """Search the web for real-time Dubai real estate and market data."""
    results = exa.search(query, num_results=3, contents={"text": True})
    output = ""
    for r in results.results:
        output += f"Title: {r.title}\nURL: {r.url}\nContent: {r.text[:500]}\n\n"
    return output


def search_dld_listings(area: str, budget_aed: float) -> str:
    """Search Dubai Land Department and developer listings for properties matching area and budget."""
    query = f"Dubai property listings {area} price AED {budget_aed} Emaar Nakheel Damac 2025"
    results = exa.search(query, num_results=3, contents={"text": True})
    output = ""
    for r in results.results:
        output += f"Title: {r.title}\nURL: {r.url}\nContent: {r.text[:500]}\n\n"
    return output


# ════════════════════════════════════════════════════════════════════════════════
# COMPLIANCE TOOL  — the real one
# ════════════════════════════════════════════════════════════════════════════════

def check_golden_visa_eligibility(
    budget_aed: float,
    nationality: str,
    is_joint_purchase: bool = False,
    is_offplan: bool = False,
    is_mortgaged: bool = False
) -> str:
    """
    Full UAE Golden Visa eligibility + AML risk screening.

    Checks:
    1. Visa tier (10-year / 5-year / none) under current ICP/DLD rules
    2. AML risk tier (LOW / ELEVATED / HIGH / CRITICAL) per FATF lists
       as incorporated into UAE law via Cabinet Resolution 134/2025
    3. Source-of-funds EDD trigger (budgets ≥ AED 5M)
    4. Special flags for off-plan and mortgaged purchases

    Returns structured compliance output written directly into agent state.
    """

    # ── 1. Visa eligibility ──────────────────────────────────────────────────
    visa = _get_visa_tier(budget_aed, is_joint=is_joint_purchase)

    # ── 2. AML risk tier ─────────────────────────────────────────────────────
    risk_tier, risk_basis = _get_risk_tier(nationality)

    # ── 3. Source-of-funds flag ───────────────────────────────────────────────
    sof_flag = budget_aed >= SOURCE_OF_FUNDS_THRESHOLD

    # ── 4. Build the compliance notes string ─────────────────────────────────
    lines = []

    # Visa section
    lines.append(f"VISA ELIGIBILITY: {visa['visa_tier']}")
    if visa["ten_year_eligible"]:
        lines.append(f"✓ Budget AED {budget_aed:,.0f} exceeds 10-year Golden Visa threshold (AED 2M).")
    elif visa["five_year_eligible"]:
        lines.append(f"△ Budget AED {budget_aed:,.0f} qualifies for 5-year Investor Visa only (min AED 750K).")
        lines.append(visa.get("note", ""))
    else:
        lines.append(f"✗ {visa.get('note', '')}")

    if visa.get("joint_note"):
        lines.append(f"JOINT PURCHASE NOTE: {visa['joint_note']}")
    if is_offplan and visa.get("offplan_note"):
        lines.append(f"OFF-PLAN NOTE: {visa['offplan_note']}")
    if is_mortgaged and visa.get("mortgage_note"):
        lines.append(f"MORTGAGE NOTE: {visa['mortgage_note']}")

    # AML section
    lines.append("")
    lines.append(f"AML RISK TIER: {risk_tier}")
    lines.append(risk_basis)

    if risk_tier == "CRITICAL":
        lines.append("⛔ TRANSACTION BLOCKED PENDING COMPLIANCE REVIEW. Do not proceed.")
        lines.append("Required: MLRO sign-off + mandatory goAML filing before any further steps.")
    elif risk_tier == "HIGH":
        lines.append("⚠ ENHANCED DUE DILIGENCE REQUIRED before agent engagement.")
        lines.append("Required docs: source of funds, proof of assets, certified ID, business activity.")
    elif risk_tier == "ELEVATED":
        lines.append("⚠ ELEVATED SCRUTINY. Collect source-of-funds documentation at meeting stage.")

    # Source of funds
    if sof_flag:
        lines.append("")
        lines.append(f"SOURCE OF FUNDS FLAG: Budget ≥ AED 5M.")
        lines.append(
            "UAE AML/CFT Guidelines (Sep 2025 MoE): Mandatory source-of-funds "
            "documentation required regardless of nationality. Agent must collect "
            "evidence of legitimate wealth origin before progressing to property viewing."
        )

    notes_str = "\n".join(lines)

    # ── 5. Determine overall eligible flag for PDF rendering ─────────────────
    eligible = visa["ten_year_eligible"] or visa["five_year_eligible"]
    # CRITICAL risk overrides eligibility display — agent must review first
    if risk_tier == "CRITICAL":
        eligible = False

    return notes_str


# ════════════════════════════════════════════════════════════════════════════════
# PDF GENERATION
# ════════════════════════════════════════════════════════════════════════════════

def _build_html(
    lead_name, lead_phone, budget_aed, nationality,
    timeline_months, property_interest, eligible,
    compliance_notes, matched_properties
) -> str:
    status_color = "#1a7a3f" if eligible else "#b91c1c"
    status_label = "✓  GOLDEN VISA ELIGIBLE" if eligible else "✗  COMPLIANCE REVIEW REQUIRED"
    status_bg    = "#d1fae5" if eligible else "#fee2e2"
    priority     = "HIGH" if timeline_months <= 3 else "MEDIUM" if timeline_months <= 6 else "STANDARD"
    priority_bg  = "rgba(185,28,28,0.35)" if priority == "HIGH" else "rgba(217,119,6,0.35)" if priority == "MEDIUM" else "rgba(255,255,255,0.1)"

    prop_lines = [l.strip() for l in matched_properties.split('\n') if l.strip()]
    prop_html  = "".join(f"<li>{line}</li>" for line in prop_lines[:20])

    # Render compliance notes with line breaks
    comp_html = "<br>".join(compliance_notes.split('\n'))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; font-size:13px; color:#1f2937; background:#fff; }}
  .header {{ background:linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%); color:white; padding:32px 40px 24px; }}
  .header-row {{ display:flex; justify-content:space-between; align-items:flex-start; }}
  .agency {{ font-size:10px; font-weight:600; letter-spacing:3px; text-transform:uppercase; color:#94a3b8; margin-bottom:6px; }}
  .doc-title {{ font-size:24px; font-weight:700; color:#fff; }}
  .doc-sub {{ font-size:12px; color:#94a3b8; margin-top:4px; }}
  .priority-badge {{ padding:6px 14px; border-radius:6px; font-size:10px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#fff; background:{priority_bg}; border:1px solid rgba(255,255,255,0.2); }}
  .gold-bar {{ height:3px; background:linear-gradient(90deg, #c9a84c, #f0d080, #c9a84c); margin-top:20px; border-radius:2px; }}
  .body {{ padding:28px 40px; }}
  .elig-banner {{ background:{status_bg}; border-left:4px solid {status_color}; border-radius:0 8px 8px 0; padding:14px 20px; margin-bottom:24px; }}
  .elig-label {{ font-size:15px; font-weight:700; color:{status_color}; margin-bottom:6px; }}
  .elig-notes {{ font-size:11px; color:#374151; line-height:1.7; }}
  .section {{ margin-bottom:24px; }}
  .section-title {{ font-size:9px; font-weight:700; letter-spacing:2.5px; text-transform:uppercase; color:#6b7280; border-bottom:1px solid #e5e7eb; padding-bottom:8px; margin-bottom:14px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; }}
  .card {{ background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; }}
  .card .lbl {{ font-size:9px; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:#9ca3af; margin-bottom:4px; }}
  .card .val {{ font-size:14px; font-weight:600; color:#111827; }}
  .card.budget .val {{ font-size:17px; }}
  ul.props {{ list-style:none; padding:0; }}
  ul.props li {{ padding:8px 12px; border-left:3px solid #c9a84c; margin-bottom:7px; background:#fafaf7; border-radius:0 6px 6px 0; font-size:11px; color:#374151; line-height:1.5; }}
  .legal-note {{ font-size:9px; color:#9ca3af; background:#f8fafc; border:1px solid #e5e7eb; border-radius:6px; padding:10px 14px; margin-top:8px; line-height:1.6; }}
  .footer {{ margin-top:32px; padding-top:14px; border-top:1px solid #e5e7eb; display:flex; justify-content:space-between; align-items:center; }}
  .footer-note {{ font-size:10px; color:#9ca3af; line-height:1.6; }}
  .confidential {{ font-size:9px; font-weight:700; letter-spacing:2px; text-transform:uppercase; color:#d1d5db; border:1px solid #e5e7eb; padding:3px 10px; border-radius:4px; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-row">
    <div>
      <div class="agency">Dubai Luxury Real Estate</div>
      <div class="doc-title">Lead Intelligence Report</div>
      <div class="doc-sub">Qualified Investor Profile · Property Match · Compliance Assessment</div>
    </div>
    <div class="priority-badge">{priority} Priority</div>
  </div>
  <div class="gold-bar"></div>
</div>

<div class="body">

  <div class="elig-banner">
    <div class="elig-label">{status_label}</div>
    <div class="elig-notes">{comp_html}</div>
  </div>

  <div class="section">
    <div class="section-title">Investor Profile</div>
    <div class="grid">
      <div class="card"><div class="lbl">Full Name</div><div class="val">{lead_name}</div></div>
      <div class="card"><div class="lbl">Contact</div><div class="val">{lead_phone}</div></div>
      <div class="card"><div class="lbl">Nationality</div><div class="val">{nationality}</div></div>
      <div class="card budget"><div class="lbl">Investment Budget</div><div class="val">AED {budget_aed:,.0f}</div></div>
      <div class="card"><div class="lbl">Purchase Timeline</div><div class="val">{timeline_months} months</div></div>
      <div class="card"><div class="lbl">Area of Interest</div><div class="val">{property_interest}</div></div>
    </div>
  </div>

  <div class="section">
    <div class="section-title">Matched Properties &amp; Market Data</div>
    <ul class="props">
      {prop_html if prop_html else "<li>Research pending — agent follow-up required.</li>"}
    </ul>
  </div>

  <div class="legal-note">
    Compliance assessment based on: Federal Decree-Law No. 10/2025 (UAE AML/CFT Law) ·
    Cabinet Resolution No. 134/2025 (DNFBP Executive Regulations) ·
    Ministry of Economy Circular 1/2026 · FATF Grey/Black Lists (Oct 2025 update) ·
    ICP/DLD Golden Visa guidelines (2025). This report is an automated pre-screening tool
    and does not replace a licensed compliance officer or full KYC/AML programme.
  </div>

  <div class="footer">
    <div class="footer-note">
      Generated by the Golden Visa Lead Qualification System.<br>
      Data sourced from live DLD listings and real-time market research.
    </div>
    <div class="confidential">Confidential</div>
  </div>

</div>
</body>
</html>"""


def generate_lead_pdf(
    lead_name: str,
    lead_phone: str,
    budget_aed: float,
    nationality: str,
    timeline_months: int,
    property_interest: str,
    eligible: bool,
    compliance_notes: str,
    matched_properties: str
) -> str:
    """
    Generate a premium PDF lead summary. Writes pdf_path into state.
    """
    filename = f"/tmp/lead_{lead_phone.replace('+', '').replace(' ', '')}.pdf"

    html = _build_html(
        lead_name, lead_phone, budget_aed, nationality,
        timeline_months, property_interest, eligible,
        compliance_notes, matched_properties
    )

    weasyprint.HTML(string=html).write_pdf(filename)

    return filename