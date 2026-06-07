from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Principal(BaseModel):
    """Identidade extraída de um token validado do Auth Service.

    Reflete os claims do JWT (ver INTEGRATION.md do auth-service): `sub`,
    `scopes`, `principal_type` e — em tokens de usuário — `email`.
    """

    sub: str = Field(..., description="id do usuário ou client_id do serviço")
    scopes: list[str] = Field(default_factory=list, description="permissões do token")
    principal_type: str = Field(..., description='"user" ou "service"')
    email: str | None = Field(None, description="e-mail (apenas tokens de usuário)")

    model_config = ConfigDict(extra="ignore")


class UserResponse(BaseModel):
    """Authenticated user returned by the Auth service /users/me endpoint."""

    id: UUID = Field(..., description="ID único do usuário")
    email: str = Field(..., description="E-mail do usuário")
    username: str = Field(..., description="Nome de usuário")
    access_level: str = Field(..., description="Nível de acesso do usuário")
    is_active: bool = Field(..., description="Indica se a conta está ativa")

    model_config = ConfigDict(extra="ignore")
