import tomli
import google.generativeai as genai

try:
    with open('/Users/alecarmo/Desktop/FIAP/projeto/tech_challenge_fiap2/tech_challenge_fiap_ii/.streamlit/secrets.toml', 'rb') as f:
        secrets = tomli.load(f)
    api_key = secrets.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)
    print("Available models:")
    for m in genai.list_models():
        print(f"- {m.name} (Methods: {m.supported_generation_methods})")
except Exception as e:
    print(f"Error: {e}")
