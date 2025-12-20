from typing import Dict, Any

class LLMProvider:
    def call(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    def call(self, prompt: str) -> Dict[str, Any]:
        return {
            "result": f"[MOCK] Resposta para: {prompt[:60]}..."
        }
