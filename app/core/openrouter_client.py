from time import time
import requests
from app.core.llm import LLMClient

class OpenRouterClient(LLMClient):
    def __init__(self, api_key: str, model="deepseek/deepseek-v3.2"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
    
    def generate(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]