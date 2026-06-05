"""HTTP controller for the registration endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.domain.auth.dependencies import get_current_user
from src.domain.auth.schemas import UserResponse

from .schemas import (
    AvailableEventResponse,
    CheckInStatusResponse,
    ConfirmationCodeRequest,
    ConfirmationResponse,
    GuestRegistrationRequest,
    GuestRegistrationResponse,
    RegistrationCreateRequest,
    RegistrationResponse,
)
from .service import RegistrationService, get_registration_service

router = APIRouter(tags=["registration"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma inscrição",
    description="Cria uma inscrição para o par usuário/evento informado.",
)
def register(
    body: RegistrationCreateRequest,
    service: RegistrationService = Depends(get_registration_service),
    auth_user: UserResponse = Depends(get_current_user),
) -> RegistrationResponse:
    registration = service.register(body.event_id, body.user_id, auth_user.id)
    return RegistrationResponse(
        event_id=registration.event_id,
        user_id=registration.user_id,
        status=registration.status,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
    )


# ---------------------------------------------------------------------------
# GET /events/available – eventos com vagas disponíveis
# ---------------------------------------------------------------------------


@router.get(
    "/events/available",
    response_model=list[AvailableEventResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista eventos disponíveis para inscrição",
    description=(
        "Consulta o microserviço de eventos para obter a lista de eventos cadastrados "
        "e aplica dois filtros antes de retornar: "
        "(1) remove eventos cuja data de encerramento já passou, ou seja, só eventos futuros ou em andamento são considerados; "
        "(2) remove eventos que já atingiram a capacidade máxima de inscritos, "
        "comparando o limite do evento com o total de inscrições registradas neste serviço. "
        "Retorna apenas os eventos que ainda estão dentro do prazo e possuem vagas disponíveis."
    ),
)
def list_available_events() -> list[AvailableEventResponse]:
    # TODO: chamar o microserviço de eventos via HTTP, filtrar eventos não encerrados
    # (data_fim >= now()) e cruzar capacidade máxima com contagem local de inscrições
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
    )


# ---------------------------------------------------------------------------
# GET /events/{event_id}/registrations – inscritos de um evento
# ---------------------------------------------------------------------------


@router.get(
    "/events/{event_id}/registrations",
    response_model=list[GuestRegistrationResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista usuários registrados em um evento",
    description="Consulta no banco de dados deste serviço todos os convidados inscritos no evento informado.",
)
def list_event_registrations(
    event_id: UUID,
    service: RegistrationService = Depends(get_registration_service),
) -> list[GuestRegistrationResponse]:
    registrations = service.list_event_registrations(event_id)
    return [
        GuestRegistrationResponse(
            event_id=r.event_id,
            user_id=r.user_id,
            status=r.status,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in registrations
    ]


# ---------------------------------------------------------------------------
# POST /events/{event_id}/guests – inscrição de convidado
# ---------------------------------------------------------------------------


@router.post(
    "/events/{event_id}/guests",
    response_model=GuestRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscreve um convidado em um evento",
    description=(
        "Registra um usuário como convidado no evento especificado. "
        "Deve verificar se ainda há vagas disponíveis antes de criar a inscrição."
    ),
)
def register_guest(
    event_id: UUID,
    body: GuestRegistrationRequest,
    service: RegistrationService = Depends(get_registration_service),
    auth_user: UserResponse = Depends(get_current_user),
) -> GuestRegistrationResponse:
    registration = service.register(event_id, body.user_id, auth_user.id)
    return GuestRegistrationResponse(
        event_id=registration.event_id,
        user_id=registration.user_id,
        status=registration.status,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
    )


# ---------------------------------------------------------------------------
# DELETE /events/{event_id}/guests/{user_id} – cancelamento de inscrição
# ---------------------------------------------------------------------------


@router.delete(
    "/events/{event_id}/guests/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancela a inscrição de um convidado em um evento",
    description=(
        "Remove a inscrição do usuário informado no evento especificado. "
        "Só é possível cancelar inscrições em eventos que ainda não ocorreram; "
        "tentativas de cancelamento após a data do evento devem ser rejeitadas com 422. "
        "Retorna 204 No Content em caso de sucesso e 404 caso a inscrição não exista."
    ),
)
def cancel_guest_registration(
    event_id: UUID,
    user_id: UUID,
    auth_user: UserResponse = Depends(get_current_user),
) -> None:
    _ = event_id
    if auth_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authenticated user does not match requested user",
        )

    # TODO: verificar se o evento ainda não ocorreu, localizar a inscrição e removê-la
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
    )


# ---------------------------------------------------------------------------
# GET /events/{event_id}/guests/{user_id}/check-in – validação para check-in
# ---------------------------------------------------------------------------


@router.get(
    "/events/{event_id}/guests/{user_id}/check-in",
    response_model=CheckInStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Valida se um usuário está inscrito em um evento (uso interno: check-in)",
    description=(
        "Endpoint destinado ao microsserviço de check-in. "
        "Verifica se o usuário informado possui uma inscrição ativa no evento especificado "
        "e se essa inscrição foi confirmada. "
        "Retorna sempre 200 com o campo `status` indicando o resultado — "
        "o serviço chamador é responsável por decidir se permite ou nega o acesso físico ao evento."
    ),
    tags=["registration", "check-in"],
)
def validate_check_in(
    event_id: UUID,
    user_id: UUID,
    service: RegistrationService = Depends(get_registration_service),
) -> CheckInStatusResponse:
    registration = service.get_check_in_registration(event_id, user_id)

    if registration is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found.",
        )

    return CheckInStatusResponse(
        event_id=event_id,
        user_id=user_id,
        status=registration.status,
        created_at=registration.created_at,
        updated_at=registration.updated_at,
    )


# ---------------------------------------------------------------------------
# POST /events/confirmation/{confirmation_id} – confirmação de inscrição
# ---------------------------------------------------------------------------


@router.post(
    "/events/confirmation/{confirmation_id}",
    response_model=ConfirmationResponse,
    status_code=status.HTTP_200_OK,
    summary="Confirma a inscrição de um usuário em um evento",
    description=(
        "Valida o token alfanumérico enviado pelo usuário para confirmar sua inscrição. "
        "O `confirmation_id` identifica o registro de token de validação do domínio de registration "
        "armazenado na tabela auxiliar `authentication_tokens`. "
        "O token deve ter exatamente 8 caracteres alfanuméricos (gerado automaticamente pelo backend). "
        "\n\n**Erros tratados:**\n"
        "- `404 Not Found`: `confirmation_id` não existe na tabela.\n"
        "- `400 Bad Request`: token informado está incorreto.\n"
        "- `410 Gone`: o código expirou (`expires_at` ultrapassado).\n"
        "- `409 Conflict`: a inscrição já foi confirmada anteriormente (`status = CONFIRMED`).\n"
        "- `422 Unprocessable Entity`: campo `token` ausente ou fora do formato esperado (validado pelo Pydantic)."
    ),
    responses={
        400: {"description": "Token incorreto"},
        404: {"description": "confirmation_id não encontrado"},
        409: {"description": "Inscrição já confirmada anteriormente"},
        410: {"description": "Token expirado"},
    },
)
def confirm_registration(
    confirmation_id: UUID,
    body: ConfirmationCodeRequest,
    auth_user: UserResponse = Depends(get_current_user),
) -> ConfirmationResponse:
    _ = (confirmation_id, body, auth_user)
    # TODO: buscar o token de validação pelo confirmation_id na tabela authentication_tokens
    #   → 404 se não existir
    # TODO: verificar se expires_at < now()
    #   → 410 Gone se expirado
    # TODO: verificar se a inscrição correspondente já está com status CONFIRMED
    #   → 409 Conflict se já confirmado
    # TODO: comparar body.token com o campo `token` do registro
    #   → 400 Bad Request se divergir
    # TODO: atualizar status = CONFIRMED na tabela registrations
    #   → updated_at deve ser preenchido automaticamente
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
    )
