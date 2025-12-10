import os
import argparse
from dotenv import load_dotenv
from google import genai

# ENV Solving
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
gemini_model = os.environ.get("GEMINI_MODEL")

if api_key is None:
    raise ValueError("GEMINI_API_KEY either does not exist in 'env.' file or is empty.")

# CLI Params solving:
parser = argparse.ArgumentParser(description="Chatbot")
parser.add_argument("user_prompt", type=str, help="User prompt")
args = parser.parse_args()

client = genai.Client(api_key=api_key)

response = client.models.generate_content(model=gemini_model, contents=args.user_prompt)
print(f"Prompt tokens: {response.usage_metadata.prompt_token_count} \nResponse tokens: {response.usage_metadata.candidates_token_count}\n Response:\n{response.text}")