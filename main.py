import os
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

import call_function
from prompts import system_prompt
from config import MAX_ITERATIONS

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

# this is the list of messages i keep during the back and forth, its initiated with the original user input
messages = [
    types.Content(
        role="user", 
        parts=[types.Part(text=args.user_prompt)]
    )]

# our conversation stoppers
iteration = 0
last_response = False

while iteration < MAX_ITERATIONS or last_response:
    print(f"\n\n*** Starting iteration {iteration}! ***")
    # we start by providing the llm input, it will be our whole conversation as we will build up the meassages list, we also provide system prompt and avaible tools
    response = client.models.generate_content(
        model=gemini_model,
        contents=messages,
        config=types.GenerateContentConfig(system_instruction=system_prompt, tools=[call_function.available_functions]),
    )

    # if LLM asked us to call function for him  we do that and treat functions ouput as users response
    returned_function_call = False

    # in case there are more than one function calls results i'm gonna send them as one user response after checing all the candidates
    function_calls_results = []

    # lets check candidates of responses for any function calls
    #TODO: Theoretically this could return more than one response. What then? I need to extend logic to handle this. Are these possible branching points for interaction?
    
    for candidate in response.candidates:
        try:
            print(f"Candidate: {candidate.content}\n\n")

            function_call_result = None
            
            if response.function_calls:
                for function_call in response.function_calls:
                    print(f"Call of {function_call.name}, args: {function_call.args}")
                    function_call_result = call_function.call_function(function_call)

                    if function_call_result:
                        print(f"Function call result: {function_call_result.parts[0].function_response.response}")
                        function_calls_results.append(function_call_result)
                        returned_function_call = True
                    else:
                        raise ValueError(f"Call of {function_call.name}, returned empty result field")
            else:
                raise ValueError("There is no function to call for this candidate.")

        except Exception as e:
            print(f"Error: {e}")
            function_calls_results.append(types.Content(role="tool", parts=[types.Part.from_function_response(name="error", response={"error": str(e)})]))
            raise
        
    # Lets generate and append coherent user response
    user_response = ""
    for function_call_result in function_calls_results:
        user_response += f"- {function_call_result.parts[0].function_response.response}\n"
    
    messages.append(types.Content(role="user", parts=[types.Part(text=user_response)]))
        
        
    # breaking conditions
    if not returned_function_call and response.text:
        last_response = True

    iteration += 1

    # printing into the console at the end so even when breaking condition is present the last response will be printed
    if args.verbose:
        print(  
            f"User prompt: {args.user_prompt}\nPrompt tokens: {response.usage_metadata.prompt_token_count} \nResponse tokens: {response.usage_metadata.candidates_token_count}\nFunction calls:\n{response.function_calls}\nResponse:\n{response.text}"
        )
    else:
        print(response.text)
        