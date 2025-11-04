# llm_interface.py
import requests
import json
from typing import List, Dict

# ==============================
# 🔐 OpenRouter Model Config
# ==============================
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

LLM_MODELS = [
    {
        "name": "DeepSeek R1",
        "model": "deepseek/deepseek-r1:free",
        "api_key": "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"
    },
    {
        "name": "Meta LLaMA 3.3",
        "model": "meta-llama/llama-3.3-8b-instruct:free",
        "api_key": "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"
    },
    {
        "name": "Google Gemma",
        "model": "google/gemma-3n-e4b-it:free",
        "api_key": "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"
    },
    {
        "name": "DeepSeek Chat v3",
        "model": "deepseek/deepseek-chat-v3.1:free",
        "api_key": "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"
    }
]

# ==============================
# ⚙️ LLM Interface Class
# ==============================
class LLMInterface:
    """
    Handles OpenRouter LLM calls with automatic fallback.
    """

    def __init__(self, models: List[Dict] = LLM_MODELS):
        self.models = models

    def generate(self, prompt: str, temperature: float = 0.4, max_tokens: int = 800) -> str:
        """
        Sends prompt to LLM with fallback if one model fails.
        """
        for llm in self.models:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm['api_key']}"
            }
            payload = {
                "model": llm["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            try:
                response = requests.post(OPENROUTER_ENDPOINT, headers=headers, data=json.dumps(payload), timeout=60)
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    if content:
                        return content
                else:
                    print(f"[{llm['name']}] API failed: {response.status_code} → {response.text}")
            except Exception as e:
                print(f"[{llm['name']}] Error: {str(e)}")
                continue

        return "❌ All LLMs failed. Check API keys or network connection."


# ==============================
# 🚀 Example usage
# ==============================
if __name__ == "__main__":
    llm = LLMInterface()
    prompt = "Explain the difference between supervised and unsupervised learning in simple terms."
    result = llm.generate(prompt)
    print("💬 LLM Response:\n", result)
