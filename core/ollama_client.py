import requests
import json


def send_prompt(system_prompt, user_text):
    # Purpose: send one request to Ollama and return the raw response text
    # Input: system_prompt (string) - the role/instruction for the model
    #        user_text (string) - the news text to analyze
    # Output: (string) Ollama's reply text, or None if request fails

    url = "http://localhost:11434/api/chat"

    payload = {
        "model": "qwen2.5:14b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
    except requests.exceptions.ConnectionError:
        print("ollama_client: cannot connect to Ollama at http://localhost:11434")
        return None
    except requests.exceptions.Timeout:
        print("ollama_client: request timed out after 60 seconds")
        return None

    if response.status_code == 200:
        raw = response.json()
        return raw["message"]["content"]
    else:
        print("ollama_client: request failed, status code:", response.status_code)
        print("ollama_client: error body:", response.text)
        return None


def parse_json_response(raw_text):
    # Purpose: extract and parse the JSON object from Ollama's reply text
    # Input: raw_text (string) - the full reply from Ollama, may have extra words
    # Output: (dict) parsed JSON, or None if no valid JSON found

    if raw_text is None:
        return None

    # find the JSON boundaries in case model added extra text
    start = raw_text.find("{")
    end = raw_text.rfind("}") + 1

    if start == -1 or end == 0:
        print("ollama_client: no JSON found in response:", raw_text)
        return None

    json_text = raw_text[start:end]

    try:
        result = json.loads(json_text)
        return result
    except json.JSONDecodeError as e:
        print("ollama_client: JSON parse error:", e)
        print("ollama_client: raw text was:", json_text)
        return None
