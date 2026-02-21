import os
import logging
from abc import ABC, abstractmethod
from typing import Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# ---------- Tipos de mensagem agnósticos de provider ----------

class Message:
    """
    Representa uma mensagem no formato agnóstico.
    Cada provider é responsável por converter para seu próprio formato.
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

    def __init__(self, role: str, content: Any):
        """
        Args:
            role: "system" | "user" | "assistant"
            content: str (texto simples) ou list (conteúdo multimodal)

        Exemplo de content multimodal:
            [
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                {"type": "text", "text": "Descreva esta imagem"}
            ]
        """
        self.role = role
        self.content = content

    def __repr__(self):
        preview = str(self.content)[:80]
        return f"Message(role={self.role!r}, content={preview!r}...)"


# ---------- Interface base ----------

class BaseLLMProvider(ABC):
    """
    Interface base para todos os providers de LLM.

    Para adicionar um novo provider (Claude, Grok, Gemini...):
    1. Crie uma classe que herda de BaseLLMProvider
    2. Implemente os métodos abstratos
    3. Registre no factory LLMProvider.create()
    """

    @abstractmethod
    def invoke(self, messages: list[Message]) -> str:
        """
        Envia mensagens para o LLM e retorna o conteúdo textual da resposta.

        Args:
            messages: Lista de Message agnósticos

        Returns:
            str: Conteúdo textual da resposta
        """
        ...

    @abstractmethod
    def _to_provider_messages(self, messages: list[Message]) -> list[dict]:
        """
        Converte Message agnósticos para o formato específico do provider.
        """
        ...


# ---------- Implementação OpenAI ----------

class OpenAIProvider(BaseLLMProvider):
    """
    Provider para a API da OpenAI usando o SDK oficial.
    Suporta modelos de texto e visão (gpt-4o, gpt-4-vision, etc.)
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Instale o SDK da OpenAI: pip install openai")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API key da OpenAI não encontrada. "
                "Defina OPENAI_API_KEY no .env"
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs
        
        # Há modelos que não suportam temperature
        if self.model in ["gpt-5-nano"]:
            self.temperature = 1

        self.client = OpenAI(api_key=api_key)
        logger.debug(f"OpenAIProvider inicializado — model={model}, temperature={temperature}")

    def invoke(self, messages: list[Message]) -> str:
        provider_messages = self._to_provider_messages(messages)

        logger.debug(f"Enviando {len(provider_messages)} mensagens para OpenAI ({self.model})")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=provider_messages,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            **self.extra_params,
        )

        content = response.choices[0].message.content
        logger.debug(f"Resposta recebida da OpenAI — {len(content)} chars")
        return content

    def _to_provider_messages(self, messages: list[Message]) -> list[dict]:
        """
        Converte para o formato de dicionário da API da OpenAI.
        Suporta conteúdo multimodal (texto + imagens).
        """
        result = []
        for msg in messages:
            if isinstance(msg.content, list):
                # Conteúdo multimodal — já está no formato da OpenAI
                result.append({"role": msg.role, "content": msg.content})
            else:
                result.append({"role": msg.role, "content": str(msg.content)})
        return result


# ---------- Outros providers (esqueletos prontos para implementar) ----------

class AnthropicProvider(BaseLLMProvider):
    """
    Provider para a API da Anthropic (Claude).
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs):
        try:
            import anthropic
        except ImportError:
            raise ImportError("Instale o SDK da Anthropic: pip install anthropic")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada no .env")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.debug(f"AnthropicProvider inicializado — model={model}")

    def invoke(self, messages: list[Message]) -> str:
        # Separa system messages das demais (Anthropic usa campo dedicado)
        system_parts = [m for m in messages if m.role == Message.SYSTEM]
        user_messages = [m for m in messages if m.role != Message.SYSTEM]

        system_prompt = "\n\n".join(
            m.content if isinstance(m.content, str) else str(m.content)
            for m in system_parts
        )

        provider_messages = self._to_provider_messages(user_messages)

        logger.debug(f"Enviando {len(provider_messages)} mensagens para Anthropic ({self.model})")

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=provider_messages,
        )

        content = response.content[0].text
        logger.debug(f"Resposta recebida da Anthropic — {len(content)} chars")
        return content

    def _to_provider_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for msg in messages:
            if isinstance(msg.content, list):
                # Mapeia image_url (OpenAI) → image (Anthropic)
                anthropic_content = []
                for block in msg.content:
                    if block.get("type") == "image_url":
                        url = block["image_url"]["url"]
                        # "data:image/png;base64,..." → separa media_type e data
                        _, encoded = url.split(",", 1)
                        media_type = url.split(";")[0].split(":")[1]
                        anthropic_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": encoded,
                            },
                        })
                    else:
                        anthropic_content.append(block)
                result.append({"role": msg.role, "content": anthropic_content})
            else:
                result.append({"role": msg.role, "content": str(msg.content)})
        return result


class GrokProvider(BaseLLMProvider):
    """
    Provider para a API do Grok (xAI).
    Usa o mesmo formato de API da OpenAI (compatível).
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Instale o SDK da OpenAI: pip install openai")

        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise ValueError("XAI_API_KEY não encontrada no .env")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )
        logger.debug(f"GrokProvider inicializado — model={model}")

    def invoke(self, messages: list[Message]) -> str:
        provider_messages = self._to_provider_messages(messages)

        logger.debug(f"Enviando {len(provider_messages)} mensagens para Grok ({self.model})")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=provider_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **self.extra_params,
        )

        content = response.choices[0].message.content
        logger.debug(f"Resposta recebida do Grok — {len(content)} chars")
        return content

    def _to_provider_messages(self, messages: list[Message]) -> list[dict]:
        # Mesmo formato da OpenAI
        result = []
        for msg in messages:
            if isinstance(msg.content, list):
                result.append({"role": msg.role, "content": msg.content})
            else:
                result.append({"role": msg.role, "content": str(msg.content)})
        return result


class GeminiProvider(BaseLLMProvider):
    """
    Provider para a API do Google Gemini.
    """

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 1024, **kwargs):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "Instale o SDK do Google: pip install google-generativeai"
            )

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY ou GOOGLE_API_KEY não encontrada no .env")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs

        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)
        logger.debug(f"GeminiProvider inicializado — model={model}")

    def invoke(self, messages: list[Message]) -> str:
        provider_messages = self._to_provider_messages(messages)

        logger.debug(f"Enviando mensagens para Gemini ({self.model})")

        response = self.client.generate_content(
            provider_messages,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            },
        )

        content = response.text
        logger.debug(f"Resposta recebida do Gemini — {len(content)} chars")
        return content

    def _to_provider_messages(self, messages: list[Message]) -> list:
        """
        Gemini usa um formato diferente — converte para lista de partes.
        """
        result = []
        for msg in messages:
            role = "user" if msg.role in (Message.USER, Message.SYSTEM) else "model"
            if isinstance(msg.content, str):
                result.append({"role": role, "parts": [msg.content]})
            else:
                result.append({"role": role, "parts": msg.content})
        return result


# ---------- Factory ----------

_PROVIDER_MAP = {
    "openai":    OpenAIProvider,
    "anthropic": AnthropicProvider,
    "grok":      GrokProvider,
    "gemini":    GeminiProvider,
}


class LLMProvider:
    """
    Factory que instancia o provider correto a partir do llm_config.

    Exemplo de llm_config:
        {
            "provider": "openai",
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1024
        }
    """

    @staticmethod
    def create(llm_config: dict) -> BaseLLMProvider:
        provider_name = llm_config.get("provider", "openai").lower()

        provider_class = _PROVIDER_MAP.get(provider_name)
        if not provider_class:
            supported = ", ".join(_PROVIDER_MAP.keys())
            raise ValueError(
                f"Provider '{provider_name}' não suportado. "
                f"Providers disponíveis: {supported}"
            )

        # Repassa todos os parâmetros do config (exceto 'provider')
        params = {k: v for k, v in llm_config.items() if k != "provider"}

        logger.info(f"Criando provider '{provider_name}' com model='{params.get('model')}'")
        return provider_class(**params)