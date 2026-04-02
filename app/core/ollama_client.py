import requests
from app.core.llm import LLMClient

class OllamaClient(LLMClient):
    def __init__(self, model="qwen2.5-coder:7b", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json().get("response", "")