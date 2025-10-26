# smartcity_app/ia_manager/ai_api.py

import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "You are an assistant helping manage SmartCity data."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ AI Error: {e}"

# Alias to keep old import working
ai_processor = ask_ai

# Example queries if needed
SampleQueries = [
    "List all vehicles in the city",
    "Show shared vehicle availability",
]
