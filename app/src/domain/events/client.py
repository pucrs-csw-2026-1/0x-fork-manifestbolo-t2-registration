"""
Client HTTP para o microsserviço de Eventos.

ATENÇÃO: Este é um EXEMPLO ILUSTRATIVO da estrutura do client — a URL base,
os endpoints, os headers de autenticação e o tratamento de erros devem ser
ajustados conforme o contrato real do events-service.
"""

import logging
from uuid import UUID

import httpx

from src.config import get_settings

from .schemas import EventResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# EXEMPLO — adapte a URL e os endpoints conforme o ambiente real
# ---------------------------------------------------------------------------

EVENTS_SERVICE_BASE_URL = "http://events-service:8000"  # EXEMPLO: ajuste via settings


class EventsClient:
    """Encapsula todas as chamadas HTTP ao microsserviço de Eventos.

    EXEMPLO: esta classe é um ponto de partida. Adicione autenticação
    (ex: Bearer token de serviço), retry logic e tratamento de erros conforme
    os requisitos do projeto.
    """

    def __init__(self, base_url: str = EVENTS_SERVICE_BASE_URL) -> None:
        self._base_url = base_url

    def get_all_events(self) -> list[EventResponse]:
        """Busca todos os eventos cadastrados no microsserviço de eventos.

        EXEMPLO: endpoint e schema hipotéticos — alinhe com a API real.
        """
        # EXEMPLO de chamada — substitua pelo endpoint correto
        with httpx.Client(base_url=self._base_url, timeout=5.0) as client:
            response = client.get("/events")
            response.raise_for_status()
            return [EventResponse(**item) for item in response.json()]

    def get_event_by_id(self, event_id: UUID) -> EventResponse | None:
        """Busca um evento específico pelo ID.

        EXEMPLO: endpoint e schema hipotéticos — alinhe com a API real.
        """
        # EXEMPLO de chamada
        with httpx.Client(base_url=self._base_url, timeout=5.0) as client:
            response = client.get(f"/events/{event_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return EventResponse(**response.json())


# ---------------------------------------------------------------------------
# Dependency injection (FastAPI)
# ---------------------------------------------------------------------------


def get_events_client() -> EventsClient:
    """Retorna uma instância do client de eventos para uso via Depends()."""
    return EventsClient()
