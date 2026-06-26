"""Protocolo síncrono que todo provider de LLM deve implementar."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        """Envia o prompt ao provider e retorna o texto bruto da resposta.

        Levanta exceção em caso de timeout ou erro de comunicação.
        Nunca loga segredos (API keys, tokens).
        """
        ...
