# server.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fastapi.responses import FileResponse

from dotenv import load_dotenv
load_dotenv()
os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.getenv("AWS_BEARER_TOKEN_BEDROCK")

from fastapi import FastAPI, Form, Request
from fastapi.responses import JSONResponse
from twilio.rest import Client as TwilioClient
from twilio.request_validator import RequestValidator
from golden_visa.agent import app as agent_app
from collections import defaultdict
from time import time
import httpx

rate_limit_store = defaultdict(list)

def is_rate_limited(phone: str, max_requests: int = 5, window: int = 60) -> bool:
    now = time()
    timestamps = rate_limit_store[phone]
    rate_limit_store[phone] = [t for t in timestamps if now - t < window]
    if len(rate_limit_store[phone]) >= max_requests:
        return True
    rate_limit_store[phone].append(now)
    return False

# ── App & clients ──────────────────────────────────────────────
app = FastAPI()

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))

TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")


# ── Routes ─────────────────────────────────────────────────────

@app.get("/pdf/{thread_id}")
async def serve_pdf(thread_id: str):
    path = f"/tmp/lead_{thread_id}.pdf"
    if os.path.exists(path):
        return FileResponse(path, media_type="application/pdf")
    return JSONResponse(content={"error": "not found"}, status_code=404)

@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, From: str = Form(...), Body: str = Form(...)):
    # 1. Verify the request actually came from Twilio
    form_data = await request.form()
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    if not validator.validate(url, dict(form_data), signature):
        return JSONResponse(content={"error": "invalid signature"}, status_code=403)
    # 2. Run the agent pipeline
    try:
        thread_id = From.replace("whatsapp:", "").replace("+", "")

        if is_rate_limited(thread_id):
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=From,
                body="Please wait a moment before sending another message."
            )
            return JSONResponse(content={"status": "rate_limited"})

        result = agent_app.invoke(
            {"messages": [{"role": "user", "content": Body}]},
            config={"configurable": {"thread_id": thread_id}}
        )

        response_text = result["messages"][-1].content

        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=From,
            body=response_text
        )

        pdf_path = result.get("pdf_path")
        if pdf_path and os.path.exists(pdf_path):
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_NUMBER,
                to=From,
                body="Your Lead Intelligence Report is ready.",
                media_url=[f"https://sthenic-unadoringly-lilia.ngrok-free.dev/pdf/{thread_id}"]
            )

        # CRM webhook logic (optional)
        crm_webhook = os.getenv("CRM_WEBHOOK_URL")
        if crm_webhook and pdf_path:
            try:
                httpx.post(crm_webhook, json={
                    "lead_name": result.get("lead_name"),
                    "lead_phone": thread_id,
                    "budget_aed": result.get("budget_aed"),
                    "nationality": result.get("nationality"),
                    "timeline_months": result.get("timeline_months"),
                    "property_interest": result.get("property_interest"),
                    "eligible": result.get("golden_visa_eligible"),
                    "pdf_url": f"https://sthenic-unadoringly-lilia.ngrok-free.dev/pdf/{thread_id}"
                }, timeout=5)
            except Exception:
                pass  # CRM failure should never crash the main flow

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        print(f"Error: {e}")
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=From,
            body="We're experiencing a brief technical issue. Our team will follow up with you shortly."
        )
        return JSONResponse(content={"status": "error"}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "running"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)