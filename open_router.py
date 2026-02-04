from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

def generate_with_openrouter(full_prompt):
    try:    
        completion = client.chat.completions.create(
            model="google/gemma-3-27b-it:free",
            messages=[
            # {
            #     "role": "system",
            #     "content": os.environ.get("SYSTEM_PROMPT")
            # },
            {
                "role": "user",
                "content": full_prompt
            },
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return None