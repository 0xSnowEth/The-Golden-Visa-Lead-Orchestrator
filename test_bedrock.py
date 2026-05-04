import os
from dotenv import load_dotenv
from anthropic import AnthropicBedrock

load_dotenv()
os.environ['AWS_BEARER_TOKEN_BEDROCK'] = os.getenv("AWS_BEARER_TOKEN_BEDROCK")

client = AnthropicBedrock(aws_region="us-east-1")

message = client.messages.create(
    model="global.anthropic.claude-opus-4-6-v1",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Say hello in one sentence."}]
)

print(message.content[0].text)