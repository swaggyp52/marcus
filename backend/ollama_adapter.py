import requests
from typing import Optional

class OllamaAdapter:
    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.host}/v1/models", timeout=1)
            return r.status_code == 200
        except Exception:
            return False

    def generate(self, prompt: str, model: str = "llama2") -> Optional[str]:
        try:
            r = requests.post(f"{self.host}/v1/generate", json={"model": model, "prompt": prompt}, timeout=10)
            if r.status_code == 200:
                return r.json().get("text")
        except Exception:
            return None
        return None
