from datetime import datetime

from pydantic import BaseModel


class ReportRunResponse(BaseModel):
    """Resposta pública de relatório.

    Campos nunca presentes: input_snapshot_json, input_fingerprint,
    failure_reason, llm_api_key, tokens, chat_id.
    """

    model_config = {"from_attributes": True}

    id: int
    generated_text: str
    is_fallback: bool
    generation_status: str
    model_name: str
    prompt_version: str
    data_quality: str
    signal_id: int | None
    report_type: str
    created_at: datetime
