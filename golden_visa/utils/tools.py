# golden_visa/utils/tools.py
import os
from exa_py import Exa
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from dotenv import load_dotenv

load_dotenv()
exa = Exa(api_key=os.getenv("EXA_API_KEY"))


def web_search(query: str) -> str:
    """Search through the web for real-time Dubai Real estate and Market data"""
    results = exa.search(query, num_results=3, contents={"text":True})
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


def check_golden_visa_eligibility(budget_aed: float, nationality: str) -> dict:
    """Check if a lead qualifies for UAE Golden Visa based on investment amount and nationality."""
    GOLDEN_VISA_THRESHOLD = 2_000_000

    eligible = budget_aed >= GOLDEN_VISA_THRESHOLD

    if eligible:
        notes = (
            f"{nationality} national with AED {budget_aed:,.0f} budget. "
            f"Exceeds AED 2M Golden Visa threshold by AED {budget_aed - GOLDEN_VISA_THRESHOLD:,.0f}. "
            f"Qualifies for 10-year UAE residency."
        )
    else:
        shortfall = GOLDEN_VISA_THRESHOLD - budget_aed
        notes = (
            f"{nationality} national with AED {budget_aed:,.0f} budget. "
            f"Below AED 2M threshold by AED {shortfall:,.0f}. "
            f"Does not qualify for Golden Visa."
        )

    return {"eligible": eligible, "notes": notes}


def generate_lead_pdf(lead_name: str, lead_phone: str, budget_aed: float,
                       nationality: str, timeline_months: int,
                       property_interest: str, eligible: bool,
                       compliance_notes: str, matched_properties: str) -> str:
    """Generate a PDF lead summary for the real estate agent."""
    filename = f"/tmp/lead_{lead_phone.replace('+', '').replace(' ', '')}.pdf"

    c = canvas.Canvas(filename, pagesize=A4)

    # Header
    c.setFont("Helvetica-Bold", 18)
    c.drawString(50, 800, "Golden Visa Lead Summary")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 770, "Lead Information")
    c.setFont("Helvetica", 11)
    c.drawString(50, 752, f"Name:          {lead_name}")
    c.drawString(50, 736, f"Phone:         {lead_phone}")
    c.drawString(50, 720, f"Nationality:   {nationality}")
    c.drawString(50, 704, f"Budget:        AED {budget_aed:,.0f}")
    c.drawString(50, 688, f"Timeline:      {timeline_months} months")
    c.drawString(50, 672, f"Area Interest: {property_interest}")

    # Compliance
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 645, "Golden Visa Eligibility")
    c.setFont("Helvetica", 11)
    status = "QUALIFIED" if eligible else "NOT QUALIFIED"
    c.drawString(50, 628, f"Status: {status}")
    c.drawString(50, 612, f"Notes:  {compliance_notes}")

    # Properties
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 585, "Matched Properties")
    c.setFont("Helvetica", 9)

    # Split long text into lines
    y = 568
    for line in matched_properties[:800].split('\n'):
        c.drawString(50, y, line[:90])
        y -= 14
        if y < 100:
            break

    c.save()
    return filename

