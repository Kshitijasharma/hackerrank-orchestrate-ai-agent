import os
from dotenv import load_dotenv
from anthropic import AnthropicFoundry

load_dotenv()

client = AnthropicFoundry(
    api_key=os.getenv("FOUNDRY_API_KEY", ""),
    base_url=os.getenv("FOUNDRY_ENDPOINT", "")
)

DEPLOYMENT_NAME = os.getenv("FOUNDRY_DEPLOYMENT_NAME", "claude-opus-4-7")

print("Testing Anthropic Foundry connection...")
try:
    response = client.messages.create(
        model=DEPLOYMENT_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": "how is the waether today"}]
    )
    print("Success! Response from model:")
    print(response.content[0].text)
except Exception as e:
    print(f"Error calling LLM: {e}")
