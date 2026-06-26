"""Prompt versionado para geração de relatórios analíticos.

PROMPT_VERSION deve ser alterada sempre que o prompt mudar semanticamente,
para que relatórios gerados com versões distintas sejam identificáveis.
"""

import json

PROMPT_VERSION = "1.0.0"

_TEMPLATE = """\
Você é um sistema de análise técnica educacional. Analise os dados fornecidos e gere \
um relatório estruturado. Versão do prompt: {prompt_version}.

REGRAS OBRIGATÓRIAS — qualquer violação invalida a resposta:
1. Responda SOMENTE com JSON válido, sem texto antes ou depois do JSON.
2. Use exclusivamente os reason_codes listados no campo "reason_codes" do contexto.
3. Não mencione outros reason_codes, indicadores inventados ou dados externos.
4. Proibido: recomendações, garantias, previsões de preço, promessas de retorno.
5. Proibido: referências a notícias, eventos, outras empresas, fontes externas.
6. Campos com valor null devem ser descritos como "dado indisponível", nunca estimados.
7. Use apenas números presentes nos campos numéricos do contexto fornecido.
8. O relatório é estritamente educacional e analítico, não constitui conselho financeiro.

FORMATO OBRIGATÓRIO (JSON, sem markdown, sem blocos de código):
{{
  "summary": "Resumo objetivo da situação técnica do ativo em 2-3 frases.",
  "positive_factors": [
    {{"reason_code": "<código do contexto>", "explanation": "<explicação em português>"}}
  ],
  "attention_factors": [
    {{"reason_code": "<código do contexto>", "explanation": "<explicação em português>"}}
  ],
  "limitations": [
    "<limitação técnica ou de dado 1>",
    "<limitação técnica ou de dado 2>"
  ]
}}

CONTEXTO DO ATIVO (use apenas estes dados):
{context_json}
"""


def build_prompt(context: dict) -> str:
    """Constrói o prompt final com o contexto serializado."""
    context_json = json.dumps(context, ensure_ascii=False, indent=2, default=str)
    return _TEMPLATE.format(
        prompt_version=PROMPT_VERSION,
        context_json=context_json,
    )
