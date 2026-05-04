# server.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()
os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.getenv("AWS_BEARER_TOKEN_BEDROCK")

from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from twilio.rest import Client as TwilioClient
from golden_visa.agent import app as agent_app

app = FastAPI()

twilio_client = TwilioClient(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)

TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")


@app.post("/whatsapp")
async def whatsapp_webhook(
    From: str = Form(...),
    Body: str = Form(...)
):
    try:
        # Use the sender's phone number as thread_id
        # This means each lead has their own persistent conversation
        thread_id = From.replace("whatsapp:", "").replace("+", "")

        result = agent_app.invoke(
            {"messages": [{"role": "user", "content": Body}]},
            config={"configurable": {"thread_id": thread_id}}
        )

        # Get the last message from the agent
        response_text = result["messages"][-1].content

        # Send response back to lead via Twilio
        twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            to=From,
            body=response_text
        )

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {"status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)