import os
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types


# ENV Solving
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
gemini_model = os.environ.get("GEMINI_MODEL")

if api_key is None:
    raise ValueError("GEMINI_API_KEY either does not exist in 'env.' file or is empty.")

# CLI Params solving:
parser = argparse.ArgumentParser(description="Chatbot")
parser.add_argument("user_prompt", type=str, help="User prompt")
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Enable verbose output"
)
args = parser.parse_args()

client = genai.Client(api_key=api_key)

messages = [types.Content(role="user", parts=[types.Part(text=args.user_prompt)])]

response = client.models.generate_content(model=gemini_model, contents=messages)

if args.verbose:
    print(
        f"User prompt: {args.user_prompt}\nPrompt tokens: {response.usage_metadata.prompt_token_count} \nResponse tokens: {response.usage_metadata.candidates_token_count}\nResponse:\n{response.text}"
    )
else:
    print(response.text)
