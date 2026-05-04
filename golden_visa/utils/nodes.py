# golden_visa/utils/nodes.py
from langgraph.prebuilt import create_react_agent
from golden_visa.utils.tools import (
    web_search,
    search_dld_listings,
    check_golden_visa_eligibility,
    generate_lead_pdf
)


def create_screener_agent(model):
    return create_react_agent(
        model=model,
        tools=[],
        name="screener_agent",
        prompt=(
            "You are a friendly lead screener for a luxury Dubai real estate agency. "
            "Your job is to have a natural conversation and collect: "
            "1. Full name "
            "2. Budget in AED "
            "3. Nationality "
            "4. How soon they want to buy (in months) "
            "5. Which area in Dubai they're interested in "
            "Ask one question at a time. Be warm and professional. "
            "Once you have all 5 pieces of information, summarize them clearly."
        )
    )


def create_compliance_agent(model):
    return create_react_agent(
        model=model,
        tools=[check_golden_visa_eligibility],
        name="compliance_agent",
        prompt=(
            "You are a UAE Golden Visa compliance specialist. "
            "When given a lead's budget and nationality, "
            "use the check_golden_visa_eligibility tool to assess their eligibility. "
            "Return the result clearly stating whether they qualify and why."
        )
    )


def create_dld_researcher_agent(model):
    return create_react_agent(
        model=model,
        tools=[web_search, search_dld_listings],
        name="dld_researcher_agent",
        prompt=(
            "You are a Dubai real estate market researcher. "
            "When given an area and budget, use search_dld_listings to find "
            "relevant properties from Emaar, Nakheel, and Damac. "
            "Also use web_search to get current market data for that area. "
            "Return raw findings — prices, available units, developer names."
        )
    )


def create_matchmaker_agent(model):
    return create_react_agent(
        model=model,
        tools=[generate_lead_pdf],
        name="matchmaker_agent",
        prompt=(
            "You are a property matchmaker for a Dubai luxury real estate agency. "
            "You receive a complete lead profile including their budget, area preference, "
            "eligibility status, and market research. "
            "Use generate_lead_pdf to create a professional PDF summary for the agent. "
            "Return the PDF file path and a short WhatsApp-ready summary message."
        )
    )