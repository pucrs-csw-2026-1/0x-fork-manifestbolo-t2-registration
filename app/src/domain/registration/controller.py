"""HTTP controller for the registration endpoint."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from .schemas import (
    AvailableEventResponse,
    CheckInStatusResponse,
    ConfirmationCodeRequest,
    ConfirmationResponse,
    GuestRegistrationRequest,
    GuestRegistrationResponse,
)

router = APIRouter(tags=["registration"])



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
def list_event_registrations(event_id: UUID) -> list[GuestRegistrationResponse]:
    # TODO: buscar inscrições pelo event_id no repositório local
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
    )


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
) -> GuestRegistrationResponse:
    # TODO: validar vagas, consultar evento no microserviço externo e salvar inscrição
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
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
) -> None:
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
        "Retorna sempre 200 com o campo `isRegistered` indicando o resultado — "
        "o serviço chamador é responsável por decidir se permite ou nega o acesso físico ao evento."
    ),
    tags=["registration", "check-in"],
)
def validate_check_in(
    event_id: UUID,
    user_id: UUID,
) -> CheckInStatusResponse:
    # TODO: consultar a inscrição no repositório local pelo par (event_id, user_id)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
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
        "Valida o código alfanumérico enviado pelo usuário para confirmar sua inscrição. "
        "O `confirmation_id` identifica o registro na tabela auxiliar `confirmation_tokens`. "
        "O código deve ter entre 6 e 8 caracteres alfanuméricos (gerado automaticamente pelo backend). "
        "\n\n**Erros tratados:**\n"
        "- `404 Not Found`: `confirmation_id` não existe na tabela.\n"
        "- `400 Bad Request`: código informado está incorreto.\n"
        "- `410 Gone`: o código expirou (`expires_at` ultrapassado).\n"
        "- `409 Conflict`: a inscrição já foi confirmada anteriormente (`updated_at` preenchido).\n"
        "- `422 Unprocessable Entity`: campo `codigo` ausente ou fora do formato esperado (validado pelo Pydantic)."
    ),
    responses={
        400: {"description": "Código incorreto"},
        404: {"description": "confirmation_id não encontrado"},
        409: {"description": "Inscrição já confirmada anteriormente"},
        410: {"description": "Código expirado"},
    },
)
def confirm_registration(
    confirmation_id: UUID,
    body: ConfirmationCodeRequest,
) -> ConfirmationResponse:
    # TODO: buscar o registro pelo confirmation_id na tabela confirmation_tokens
    #   → 404 se não existir
    # TODO: verificar se expires_at < now()
    #   → 410 Gone se expirado
    # TODO: verificar se updated_at já está preenchido
    #   → 409 Conflict se já confirmado
    # TODO: comparar body.codigo com o campo `codigo` do registro
    #   → 400 Bad Request se divergir
    # TODO: preencher updated_at = now() e atualizar confirmation_timestamp na tabela registrations
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Endpoint ainda não implementado.",
    )
