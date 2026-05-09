# golden_visa/utils/nodes.py
import re
from langgraph.prebuilt import create_react_agent
from golden_visa.utils.state import AgentState
from golden_visa.utils.tools import (
    save_lead_info,
    web_search,
    search_dld_listings,
    check_golden_visa_eligibility,
    generate_lead_pdf
)


# ── Post-model hooks (run after each agent's LLM call, write to state) ────────

def _screener_hook(state: dict) -> dict:
    updates = {"current_step": "screener_complete"}
    messages=state["messages"]
    
    for msg in reversed(messages):
        # Tool call arguments are in AIMessage tool_calls
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "save_lead_info":
                    args = tc.get("args", {})
                    if args.get("lead_name"):
                        updates["lead_name"] = str(args["lead_name"]).replace("*", "").strip()
                    if args.get("lead_phone"):
                        updates["lead_phone"] = str(args["lead_phone"]).strip()
                    if args.get("budget_aed"):
                        updates["budget_aed"] = float(args["budget_aed"])
                    if args.get("nationality"):
                        updates["nationality"] = str(args["nationality"]).strip()
                    if args.get("timeline_months"):
                        updates["timeline_months"] = int(args["timeline_months"])
                    if args.get("property_interest"):
                        updates["property_interest"] = str(args["property_interest"]).strip()
                    return updates
    
    return updates


def _compliance_hook(state: dict) -> dict:
    last_msg = state["messages"][-1].content
    eligible = ("10-Year Golden Visa" in last_msg or "5-Year" in last_msg)
    blocked  = "CRITICAL" in last_msg
    return {
        "golden_visa_eligible": eligible and not blocked,
        "compliance_notes": last_msg,
        "current_step": "compliance_complete"
    }


def _researcher_hook(state: dict) -> dict:
    last_msg = state["messages"][-1].content
    return {
        "matched_properties": last_msg,
        "current_step": "research_complete"
    }


def _matchmaker_hook(state: dict) -> dict:
    updates = {"current_step": "complete"}
    messages = state["messages"]
    
    # First try tool call args for generate_lead_pdf
    for msg in reversed(messages):
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get("name") == "generate_lead_pdf":
                    # PDF path is built from lead_phone in tool args
                    args = tc.get("args", {})
                    phone = str(args.get("lead_phone", "")).replace("+", "").replace(" ", "")
                    if phone:
                        updates["pdf_path"] = f"/tmp/lead_{phone}.pdf"
                    return updates
    
    # Fallback: scan last message text
    last_msg = state["messages"][-1].content
    m = re.search(r"PDF_PATH:\s*(/tmp/\S+\.pdf)", last_msg)
    if m:
        updates["pdf_path"] = m.group(1).strip()
    
    return updates


# ── Agent factories ───────────────────────────────────────────────────────────

def create_screener_agent(model):
    return create_react_agent(
        model=model,
        tools=[save_lead_info],
        name="screener_agent",
        state_schema=AgentState,
        post_model_hook=_screener_hook,
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
        state_schema=AgentState,
        post_model_hook=_compliance_hook,
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
        state_schema=AgentState,
        post_model_hook=_researcher_hook,
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
        state_schema=AgentState,
        post_model_hook=_matchmaker_hook,
        prompt=(
            "You are a property matchmaker for a Dubai luxury real estate agency. "
            "Read from the conversation: lead name, phone, budget, nationality, "
            "timeline, area, compliance notes, and matched properties. "
            "Call generate_lead_pdf with all those values. "
            "The tool returns a file path. Output it on its own line prefixed exactly as: PDF_PATH: /tmp/filename.pdf\n"
            "Then write a warm 2-3 line closing message to the lead thanking them "
            "and confirming their details have been received and that a dedicated property specialist will be in touch shortly."
            "Do NOT mention any phone numbers, file paths, or whatsapp summaries. "
            "Do NOT mention agents by title. No markdown tables."
            "STRICT RULES FOR YOUR CLOSING MESSAGE:\n"
            "- You MAY say a specialist will be in touch shortly, but do NOT mention any phone numbers or WhatsApp\n"
            "- Do NOT mention file paths, /tmp/, PDF locations, or report URLs\n"
            "- Do NOT mention WhatsApp summaries or any messages being sent separately\n"
            "- Do NOT include any phone numbers in your message\n"
            "- Do NOT use markdown tables\n"
            "- End it extremely professionally"
            "- Keep your entire closing message under 300 characters\n"
        )
    )