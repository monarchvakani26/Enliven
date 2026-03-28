import os, sys, logging
logging.disable(logging.CRITICAL)  # suppress all logging

from dotenv import load_dotenv
load_dotenv('.env')

key = os.getenv('GEMINI_API_KEY', 'NOT_FOUND')
print(f"Key loaded: {key[:15]}...")

try:
    import google.generativeai as genai
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    r = model.generate_content('Reply with exactly one word: OK')
    print(f"SUCCESS: {r.text.strip()[:80]}")
except Exception as e:
    print(f"ERROR: {str(e)[:400]}")
