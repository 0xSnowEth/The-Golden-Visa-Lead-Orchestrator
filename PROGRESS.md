# Golden Visa Lead Orchestrator — Progress

## What This Is
A WhatsApp-based AI lead qualification system for Dubai luxury real estate agencies.
A lead messages the Twilio WhatsApp number → the system screens them, checks
Golden Visa eligibility, researches matching properties, generates a PDF, and
sends a summary to the agent. Built on LangGraph supervisor pattern with
Claude Opus 4.6 via AWS Bedrock.

## Stack
- LangGraph + langgraph-supervisor (multi-agent orchestration)
- Claude Opus 4.6 via AWS Bedrock (global.anthropic.claude-opus-4-6-v1)
- Twilio WhatsApp sandbox (number: +14155238886)
- Exa API (real-time web + DLD property search)
- WeasyPrint (HTML → PDF generation)
- FastAPI + uvicorn (webhook server)
- ngrok (local tunnel — temporary, replace with Railway URL)

## Architecture
Supervisor → Screener → Compliance → DLD Researcher → Matchmaker

- screener_agent: collects name, phone, budget, nationality, timeline, area
- compliance_agent: FATF black/grey list check + Golden Visa tier assessment
- dld_researcher_agent: Exa search for live DLD listings + market data
- matchmaker_agent: generates branded WeasyPrint PDF, returns file path

## File Structure
golden_visa_orchestrator/
├── golden_visa/
│   ├── utils/
│   │   ├── tools.py      ← web_search, search_dld_listings,
│   │   │                    check_golden_visa_eligibility, generate_lead_pdf,
│   │   │                    save_lead_info
│   │   ├── nodes.py      ← create_screener/compliance/researcher/matchmaker
│   │   └── state.py      ← AgentState TypedDict
│   └── agent.py          ← supervisor + InMemorySaver checkpointer + compile
├── server.py             ← FastAPI, Twilio webhook, rate limiting, CRM hook
├── Procfile              ← Railway start command
├── requirements.txt
├── pyproject.toml
├── langgraph.json
└── .env                  ← never committed

## Environment Variables Required
AWS_BEARER_TOKEN_BEDROCK=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
EXA_API_KEY=
LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
CRM_WEBHOOK_URL=          ← optional, Zapier webhook

## Compliance Engine
- FATF Black List (North Korea, Iran, Myanmar) → CRITICAL, blocks transaction
- FATF Grey List (post Oct 2025 update) → HIGH, requires EDD
- Regional Elevated Risk list → ELEVATED, source-of-funds flag
- Golden Visa tiers: 10-year (AED 2M+), 5-year (AED 750K+)
- Source of funds EDD trigger at AED 5M+
- Joint ownership rules (AED 4M threshold for dual visa)
- Off-plan and mortgage flags
Sources: Federal Decree-Law 10/2025, Cabinet Resolution 134/2025,
Ministry of Economy Circular 1/2026, FATF Oct 2025 update

## Current Score: 82/100
Done:
- Multi-agent supervisor architecture ✓
- Real WhatsApp integration via Twilio ✓
- Twilio webhook signature validation ✓
- Rate limiting (5 req/min per phone) ✓
- Real compliance engine with UAE law sources ✓
- WeasyPrint branded PDF ✓
- PDF served via /pdf/{thread_id} endpoint ✓
- CRM webhook output ✓
- Graceful error handling ✓
- Dynamic PORT for Railway ✓
- Procfile ✓

Remaining (week 2):
- Deploy to Railway (replace ngrok URLs)
- Swap InMemorySaver for PostgresSaver (persistent across restarts)
- CRM wired to real HubSpot or Google Sheet
- Dashboard endpoint showing today's qualified leads

## Next Immediate Steps
See WHAT_TO_DO_NEXT.md