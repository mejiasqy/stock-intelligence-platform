"""Gera fingerprint SHA-256 do contexto de relatório.

O fingerprint permite detectar contextos idênticos sem comparar o JSON completo.
Garante idempotência mesmo quando o signal_id permanece igual mas o conteúdo mudou
(o sinal é atualizado por upsert no scoring).
"""

import hashlib
import json


def compute_fingerprint(context: dict) -> str:
    """Retorna SHA-256 hex (64 chars) do JSON canônico do contexto.

    - sort_keys=True: ordenação estável independente da ordem de inserção
    - ensure_ascii=True: representação determinística de unicode
    - default=str: converte tipos não serializáveis (date, Decimal) para string
    - Nunca inclui segredos — o contexto não deve conter llm_api_key nem tokens
    """
    canonical = json.dumps(context, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
