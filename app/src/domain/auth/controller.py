"""Rotas relacionadas à autenticação contra o Auth Service.

Não emite tokens (isso é responsabilidade do auth-service); apenas demonstra a
validação local do token via JWKS (RS256) e expõe o principal autenticado.
"""

from fastapi import APIRouter, Depends, status

from .schemas import Principal
from .security import get_current_principal

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get(
    "/me",
    response_model=Principal,
    status_code=status.HTTP_200_OK,
    summary="Retorna o principal autenticado",
    description=(
        "Valida o `Authorization: Bearer <token>` contra o JWKS do Auth Service "
        "(RS256 + exp) e devolve os claims do token. Retorna 401 se ausente, "
        "inválido ou expirado."
    ),
)
def me(principal: Principal = Depends(get_current_principal)) -> Principal:
    return principal
