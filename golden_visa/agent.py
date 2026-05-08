# golden_visa/agent.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from langgraph_supervisor import create_supervisor
from golden_visa.utils.nodes import (
    create_screener_agent,
    create_compliance_agent,
    create_dld_researcher_agent,
    create_matchmaker_agent
)
import boto3
from langchain_aws import ChatBedrock
from golden_visa.utils.state import AgentState

os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.getenv("AWS_BEARER_TOKEN_BEDROCK")

from anthropic import AnthropicBedrock
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()


llm = ChatBedrock(
    model_id="global.anthropic.claude-opus-4-6-v1",
    region_name="us-east-1"
)
screener = create_screener_agent(llm)
compliance = create_compliance_agent(llm)
researcher = create_dld_researcher_agent(llm)
matchmaker = create_matchmaker_agent(llm)

app = create_supervisor(
    [screener, compliance, researcher, matchmaker],
    model=llm,
    state_schema=AgentState,
    prompt=(
        "You are a supervisor for a Dubai luxury real estate lead qualification system. "
        "Follow this exact sequence for every new lead: "
        "1. ALWAYS start with screener_agent to collect lead information through conversation. "
        "2. Once lead info is collected, send to compliance_agent to check Golden Visa eligibility. "
        "3. Send to dld_researcher_agent to find matching properties for their budget and area. "
        "4. Finally send to matchmaker_agent to generate the PDF and WhatsApp summary, make sure the generated PDF is sent to the user. " 
        "5. Return the final summary to the user. "
        "Never skip steps. Never answer directly. Always delegate."
    )
).compile(checkpointer = checkpointer)