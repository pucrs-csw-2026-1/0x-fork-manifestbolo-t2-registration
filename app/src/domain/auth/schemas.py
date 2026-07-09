from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    """Authenticated user returned by the Auth service /users/me endpoint."""

    id: UUID = Field(..., description="ID único do usuário")
    email: str = Field(..., description="E-mail do usuário")
    username: str = Field(..., description="Nome de usuário")
    access_level: str = Field(..., description="Nível de acesso do usuário")
    is_active: bool = Field(..., description="Indica se a conta está ativa")

    model_config = ConfigDict(extra="ignore")
