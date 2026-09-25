import os
import subprocess
import json

from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY", "")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY is not configured")


# Updated to use valid OpenRouter Free slugs
MODELS = [
    "openrouter/free",                      # Universal Auto-Router (Always works)
    "nvidia/nemotron-3-ultra:free",         # Active High-Context Free Model
    "poolside/laguna-s-2.1:free",           # Active Coding Free Model
    "inclusionai/ling-3.0-flash-fin:free"   # Active Flash Free Model
]

for model in MODELS:
    print(f"=== {model} ===")
    
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Say OK"}],
        "max_tokens": 20
    })
    
    curl_cmd = [
        "curl", "-s", "https://openrouter.ai/api/v1/chat/completions",
        "-H", f"Authorization: Bearer {API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", payload
    ]
    
    result = subprocess.run(curl_cmd, capture_output=True, text=True)
    
    try:
        response_data = json.loads(result.stdout)
        # Fixed safely accessing nested dictionary objects
        choices = response_data.get('choices', [])
        if choices:
            content = choices[0].get('message', {}).get('content', response_data)
        else:
            content = response_data
        print(content)
    except Exception as e:
        print(f"Error parsing response: {result.stdout or result.stderr}")
        
    print("done\n")
