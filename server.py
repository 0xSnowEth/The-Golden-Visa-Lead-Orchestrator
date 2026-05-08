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
    uvicorn.run(app, host="0.0.0.0", port=8000)