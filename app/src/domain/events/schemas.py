"""
Schemas que modelam as respostas do microsserviço de Eventos.

ATENÇÃO: Este é um EXEMPLO ILUSTRATIVO — os campos reais devem ser alinhados
com o contrato (OpenAPI) exposto pelo microsserviço de eventos.
Ajuste os tipos, nomes e campos conforme a documentação oficial do serviço.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# EXEMPLO — adapte conforme o contrato real do microsserviço de eventos
# ---------------------------------------------------------------------------


class EventResponse(BaseModel):
    """Representa um evento retornado pelo microsserviço de eventos.

    EXEMPLO: campos hipotéticos — alinhe com o schema real do events-service.
    """

    id: UUID = Field(..., description="ID único do evento")
    name: str = Field(..., description="Nome do evento")
    description: str | None = Field(None, description="Descrição do evento")
    max_capacity: int = Field(..., description="Capacidade máxima de participantes")
    start_at: datetime = Field(..., description="Data/hora de início do evento")
    end_at: datetime = Field(..., description="Data/hora de encerramento do evento")
