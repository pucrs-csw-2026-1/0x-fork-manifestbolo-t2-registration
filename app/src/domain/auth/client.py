"""
Client HTTP para o microsserviço de Auth.

ATENÇÃO: Este é um EXEMPLO ILUSTRATIVO da estrutura do client — a URL base,
os endpoints, os headers de autenticação e o tratamento de erros devem ser
ajustados conforme o contrato real do auth-service.
"""

import logging
from uuid import UUID

import httpx

from src.config import get_settings

from .schemas import UserResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# EXEMPLO — adapte a URL e os endpoints conforme o ambiente real
# ---------------------------------------------------------------------------

AUTH_SERVICE_BASE_URL = "http://auth-service:8000"  # EXEMPLO: ajuste via settings


class AuthClient:
    """Encapsula todas as chamadas HTTP ao microsserviço de Auth.

    EXEMPLO: esta classe é um ponto de partida. Adicione autenticação
    (ex: Bearer token de serviço), retry logic e tratamento de erros conforme
    os requisitos do projeto.
    """

    def __init__(self, base_url: str = AUTH_SERVICE_BASE_URL) -> None:
        self._base_url = base_url

    def get_user_by_id(self, user_id: UUID) -> UserResponse | None:
        """Busca os dados de um usuário pelo ID.

        EXEMPLO: endpoint e schema hipotéticos — alinhe com a API real do auth-service.
        """
        # EXEMPLO de chamada — substitua pelo endpoint correto
        with httpx.Client(base_url=self._base_url, timeout=5.0) as client:
            response = client.get(f"/users/{user_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return UserResponse(**response.json())

    def validate_token(self, token: str) -> UserResponse | None:
        """Valida um Bearer token e retorna os dados do usuário autenticado.

        EXEMPLO: endpoint e schema hipotéticos — alinhe com a API real do auth-service.
        """
        # EXEMPLO de chamada
        with httpx.Client(base_url=self._base_url, timeout=5.0) as client:
            response = client.get(
                "/auth/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code in (401, 403):
                return None
            response.raise_for_status()
            return UserResponse(**response.json())


# ---------------------------------------------------------------------------
# Dependency injection (FastAPI)
# ---------------------------------------------------------------------------


def get_auth_client() -> AuthClient:
    """Retorna uma instância do client de auth para uso via Depends()."""
    return AuthClient()
