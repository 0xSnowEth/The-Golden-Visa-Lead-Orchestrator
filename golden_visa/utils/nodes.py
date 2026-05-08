# golden_visa/utils/nodes.py
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
import re
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
            "Collect: full name, budget in AED, nationality, timeline in months, "
            "phone number, and area of interest in Dubai. Ask one question at a time. "
            "Once you have all 6 pieces, call save_lead_info. "
            "Then output a clean summary in this exact format:\n"
            "NAME: <name>\nPHONE: <phone>\nBUDGET_AED: <number>\n"
            "NATIONALITY: <nationality>\nTIMELINE_MONTHS: <number>\nAREA: <area>" 
        )
    )


def create_compliance_agent(model):
    return create_react_agent(
        model=model,
        tools=[check_golden_visa_eligibility],
        name="compliance_agent",
        prompt=(
            "You are a UAE Golden Visa compliance specialist. "
            "Read the lead summary from the conversation to get budget and nationality. "
            "Call check_golden_visa_eligibility with those values. "
            "Output the full result returned by the tool — do not truncate it."
        )
    )


def create_dld_researcher_agent(model):
    return create_react_agent(
        model=model,
        tools=[web_search, search_dld_listings],
        name="dld_researcher_agent",
        prompt=(
            "You are a Dubai real estate market researcher. "
            "Read the lead's area and budget from the conversation. "
            "Call search_dld_listings with those values. "
            "Call web_search for current market data on that area. "
            "Output all findings in full — the matchmaker agent needs this data."
        )
    )


def create_matchmaker_agent(model):
    return create_react_agent(
        model=model,
        tools=[generate_lead_pdf],
        name="matchmaker_agent",
        prompt=(
             "You are a property matchmaker for a Dubai luxury real estate agency. "
            "Read from the conversation: lead name, phone, budget, nationality, "
            "timeline, area, compliance notes, and matched properties. "
            "Call generate_lead_pdf with all those values. "
            "The tool returns a file path. Output it on its own line prefixed with PDF_PATH: "
            "Then write a 3-5 line WhatsApp-ready summary for the agent. No markdown tables."
        )
    )