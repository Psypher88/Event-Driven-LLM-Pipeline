import sys
import os

# add project root to path so we can import from core/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import ollama_client


def get_system_prompt():
    # Purpose: return the instruction text for the buyer agent
    # Input: none
    # Output: (string) system prompt that tells Ollama to reply as a buy-side analyst

    prompt = (
        "You are a professional stock buy-side analyst. "
        "Analyze the following news from a buying perspective. "
        "Reply ONLY with a JSON object, no explanation, no extra text. "
        "Format: {\"score\": <integer -5 to +5, positive is bullish>, "
        "\"reason\": \"<one sentence>\"}"
    )
    return prompt


def run(news_text):
    # Purpose: score a piece of news from a buyer's perspective
    # Input: news_text (string) - the news content to analyze
    # Output: (dict) agent contract: {agent_name, score, reason, weight}
    #         returns default dict with score=0 if Ollama call or parse fails

    system_prompt = get_system_prompt()
    raw = ollama_client.send_prompt(system_prompt, news_text)
    parsed = ollama_client.parse_json_response(raw)

    if parsed is None:
        return {
            "agent_name": "buyer",
            "score": 0,
            "reason": "parse failed",
            "weight": 0.6
        }

    result = {
        "agent_name": "buyer",
        "score": parsed.get("score", 0),
        "reason": parsed.get("reason", "no reason returned"),
        "weight": 0.6
    }
    return result


if __name__ == "__main__":
    test_news = "Company X reports record profits this quarter."
    result = run(test_news)
    print(result)
