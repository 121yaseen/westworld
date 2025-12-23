import os
from dotenv import load_dotenv

# Wrappers for Google GenAI
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash"


def call_llm(prompt: str, json_mode: bool = False, web_search: bool = False, stop_sequences: list = None) -> str:
    """Helper to call Gemini API."""
    if not GEMINI_API_KEY or not HAS_GENAI:
        return ""
    
    try:
        if not hasattr(call_llm, "client"):
            call_llm.client = genai.Client(api_key=GEMINI_API_KEY)
            
        config = types.GenerateContentConfig(
            stop_sequences=stop_sequences
        )

        if json_mode:
             config.response_mime_type = "application/json"
        
        if web_search:
            # Enable Google Search Grounding
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            config.tools = [google_search_tool]

        response = call_llm.client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=config
        )
        return response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        return ""
