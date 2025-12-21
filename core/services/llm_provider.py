import os
from dotenv import load_dotenv
from typing import Dict, Any
from langchain_openai import ChatOpenAI

load_dotenv() # Carrega as variáveis do arquivo .env

class LLMProvider:
    def call(self, prompt: str) -> Dict[str, Any]:
        raise NotImplementedError

    @staticmethod
    def create(llm_config: dict):
        provider = llm_config.get("provider", "openai")

        if provider == "openai":
            return ChatOpenAI(
                model=llm_config.get("model", "gpt-5-nano"),
                temperature=llm_config.get("temperature", 0.7),
                max_tokens=llm_config.get("max_tokens", 2**16),
                api_key=os.getenv('OPEN_API_KEY')
            )

        raise ValueError(f"LLM provider não suportado: {provider}")


class MockLLMProvider(LLMProvider):
    def call(self, prompt: str) -> Dict[str, Any]:
        return {
            "result": f"[MOCK] Resposta para: {prompt[:60]}..."
        }
