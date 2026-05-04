from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    
    #Raw lead data collected by screener
    lead_name: str | None
    lead_phone: str | None
    budget_aed: float | None
    nationality: str | None
    timeline_months: int | None
    property_interest: str | None
    
    
    #Compliance results:
    Golden_visa_eligable: bool | None
    compliance_notes: str | None
    
    #Research results:
    market_data: str | None
    matched_properties: str | None
    
    
    #Final Output:
    pdf_path: str | None
    summary: str | None
    
    #Routing:
    current_step: str | None
    
    
    
  
    
    
    
    
    