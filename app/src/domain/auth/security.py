"""Validação local de tokens emitidos pelo Auth Service (RS256 via JWKS).

Segue o contrato descrito no INTEGRATION.md do auth-service:

1. Busca o JWKS público em ``{AUTH_SERVICE_BASE_URL}/.well-known/jwks.json`` e
   o cacheia (a chave é estável; só refaz o fetch em falha de ``kid``).
2. Casa o ``kid`` do header do token com a chave do JWKS.
3. Valida assinatura **RS256** + ``exp``.
4. Expõe os claims como um :class:`Principal`; a autorização por ``scopes``
   fica a cargo de cada rota (ver :func:`require_scopes`).

Nunca aceita tokens ``HS*`` (algoritmo simétrico): apenas ``RS256``.
"""

import logging
import threading

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import get_settings

from .schemas import Principal

logger = logging.getLogger(__name__)
settings = get_settings()

_JWKS_PATH = "/.well-known/jwks.json"

_jwks_cache: dict | None = None
_jwks_lock = threading.Lock()

bearer_scheme = HTTPBearer(auto_error=True)


def _fetch_jwks(*, force: bool = False) -> dict:
    """Retorna o JWKS do Auth Service, cacheado em memória.

    Com ``force=True`` refaz o fetch (usado quando o ``kid`` do token não casa
    com nenhuma chave cacheada — ex.: rotação de chave no Auth).
    """
    global _jwks_cache
    if _jwks_cache is not None and not force:
        return _jwks_cache
    with _jwks_lock:
        if _jwks_cache is None or force:
            url = f"{settings.AUTH_SERVICE_BASE_URL}{_JWKS_PATH}"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                response.raise_for_status()
                _jwks_cache = response.json()
            logger.info("JWKS carregado de %s", url)
    return _jwks_cache


def verify_token(token: str) -> dict:
    """Valida um JWT do Auth Service e retorna seus claims.

    Levanta ``HTTPException 401`` se o token for inválido/expirado. Em falha de
    validação, refaz o JWKS uma vez (para tolerar rotação de chave) antes de
    desistir.
    """
    options = {"verify_aud": False}  # tokens do Auth não trazem claim `aud`
    try:
        return jwt.decode(token, _fetch_jwks(), algorithms=["RS256"], options=options)
    except JWTError:
        try:
            return jwt.decode(
                token, _fetch_jwks(force=True), algorithms=["RS256"], options=options
            )
        except JWTError as exc:
            logger.warning("Falha ao validar token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc


def get_current_principal(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Principal:
    """Dependency FastAPI: valida o Bearer token e retorna o principal."""
    claims = verify_token(credentials.credentials)
    return Principal(
        sub=claims["sub"],
        scopes=claims.get("scopes", []),
        principal_type=claims.get("principal_type", "user"),
        email=claims.get("email"),
    )


def require_scopes(*required: str):
    """Cria uma dependency que exige que o principal tenha todos os scopes dados.

    Uso::

        @router.get("/x", dependencies=[Depends(require_scopes("manager"))])
    """

    def _checker(principal: Principal = Depends(get_current_principal)) -> Principal:
        missing = [scope for scope in required if scope not in principal.scopes]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope insuficiente: faltam {missing}.",
            )
        return principal

    return _checker
