"""
Run this first to see which models are available on your API key.
python dataset/list_models.py
"""
import os
from dotenv import load_dotenv
load_dotenv()
 
from google import genai
 
api_key = os.getenv("GEMINI_API_KEY")
client  = genai.Client(api_key=api_key)
 
print("Available models that support generateContent:\n")
for m in client.models.list():
    name    = getattr(m, "name", "")
    methods = getattr(m, "supported_actions", []) or []
    if "generateContent" in str(methods) or not methods:
        print(f"  {name}")
 