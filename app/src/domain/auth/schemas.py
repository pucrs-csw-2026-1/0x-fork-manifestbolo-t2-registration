"""
Schemas que modelam as respostas do microsserviço de Auth.

ATENÇÃO: Este é um EXEMPLO ILUSTRATIVO — os campos reais devem ser alinhados
com o contrato (OpenAPI) exposto pelo microsserviço de auth.
Ajuste os tipos, nomes e campos conforme a documentação oficial do serviço.
"""

from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# EXEMPLO — adapte conforme o contrato real do microsserviço de auth
# ---------------------------------------------------------------------------


class UserResponse(BaseModel):
    """Representa um usuário retornado pelo microsserviço de auth.

    EXEMPLO: campos hipotéticos — alinhe com o schema real do auth-service.
    """

    id: UUID = Field(..., description="ID único do usuário")
    name: str = Field(..., description="Nome completo do usuário")
    email: str = Field(..., description="E-mail do usuário")
    is_active: bool = Field(..., description="Indica se a conta está ativa")
