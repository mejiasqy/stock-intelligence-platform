"""Provider Anthropic síncrono.

Usa anthropic.Anthropic() (cliente síncrono) — consistente com a stack síncrona do projeto.
Nunca loga llm_api_key. Propaga exceções para que o serviço acione o fallback.
"""

import logging

import anthropic
from anthropic.types import TextBlock

from app.domain.reports.protocol import LLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider:
    """Implementa LLMProvider usando o SDK Anthropic síncrono."""

    def __init__(self, api_key: str, model: str, timeout: int, max_tokens: int) -> None:
        # api_key nunca é logada
        self._client = anthropic.Anthropic(api_key=api_key, timeout=float(timeout))
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, prompt: str) -> str:
        """Chama a API Anthropic e retorna o texto da resposta.

        Levanta anthropic.APITimeoutError ou anthropic.APIError em falha.
        """
        logger.debug("Chamando Anthropic model=%s max_tokens=%d", self._model, self._max_tokens)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        block = message.content[0]
        if not isinstance(block, TextBlock):
            raise RuntimeError(f"Unexpected Anthropic block type: {type(block).__name__}")
        return block.text


# Verificação estática de conformidade com o Protocol
_: LLMProvider = AnthropicProvider.__new__(AnthropicProvider)
