# golden_visa/utils/nodes.py
from langgraph.prebuilt import create_react_agent
from golden_visa.utils.tools import (
    save_lead_info,
    web_search,
    search_dld_listings,
    check_golden_visa_eligibility,
    generate_lead_pdf
)


def create_screener_agent(model):
    return create_react_agent(
        model=model,
        tools=[save_lead_info],
        name="screener_agent",
        prompt=(
            "You are a friendly lead screener for a luxury Dubai real estate agency. "
            "Your job is to have a natural conversation and collect: "
            "1. Full name "
            "2. Budget in AED "
            "3. Nationality "
            "4. How soon they want to buy (in months) "
            "5. Their phone number"
            "6. Which area in Dubai they're interested in "
            "Ask one question at a time. Be warm and professional. "
            "Once you have all 6 pieces of information, you MUST call the "
            "save_lead_info tool to commit the data. do not just summarize "
            "in a message - call the tool. That is how downstream agents "
            "recieve the structured data they need." 
        )
    )


def create_compliance_agent(model):
    return create_react_agent(
        model=model,
        tools=[check_golden_visa_eligibility],
        name="compliance_agent",
        prompt=(
            "You are a UAE Golden Visa compliance specialist. "
            "the lead's nationality budget and nationality are already in the conversation state, "
            "call check_golden_visa_eligibility tool with those values. "
            "The tool writes the results directly into state - you do not need to "
            "Repeat the full result in your message. Just confirm it's done."
        )
    )


def create_dld_researcher_agent(model):
    return create_react_agent(
        model=model,
        tools=[web_search, search_dld_listings],
        name="dld_researcher_agent",
        prompt=(
            "You are a Dubai real estate market researcher. "
            "Call search_dld_listings with the lead's area and budget. "
            "Also call web_search for current market data on that area. "
            "Both tools write directly into state. "
            "Confirm both calls are complete, do not re-paste the raw results."
        )
    )


def create_matchmaker_agent(model):
    return create_react_agent(
        model=model,
        tools=[generate_lead_pdf],
        name="matchmaker_agent",
        prompt=(
            "You are a property matchmaker for a Dubai luxury real estate agency. "
            "All lead data (name, phone, budget, nationality, timeline, area, "
            "eligibility, compliance notes, matched properties) is in the state. "
            "call generate_lead_pdf with all those values. "
            "The tool writes the PDF path into state. "
            "After the tool call, Return a short WhatsApp-ready summary message."
            "For the agent - 3-5 lines no markdown tables."
        )
    )