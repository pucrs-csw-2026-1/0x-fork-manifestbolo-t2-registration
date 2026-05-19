"""HTTP controller for event slots."""

from uuid import UUID

from fastapi import APIRouter, Depends, status

from .schemas import EventSlotCreate, EventSlotResponse, RegistrationSlotCreate, RegistrationSlotResponse
from .service import EventSlotService, RegistrationSlotService, get_event_slot_service, get_registration_slot_service

router = APIRouter(tags=["slots"])


# ---------------------------------------------------------------------------
# GET /events/{event_id}/slots — lista slots de um evento
# ---------------------------------------------------------------------------

@router.get(
    "/events/{event_id}/slots",
    response_model=list[EventSlotResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista os slots de um evento",
    description="Retorna todos os slots (palestras, workshops etc.) cadastrados para o evento.",
)
def list_event_slots(
    event_id: UUID,
    service: EventSlotService = Depends(get_event_slot_service),
) -> list[EventSlotResponse]:
    return service.list_slots(event_id)


# ---------------------------------------------------------------------------
# POST /events/{event_id}/slots — cria um slot
# ---------------------------------------------------------------------------

@router.post(
    "/events/{event_id}/slots",
    response_model=EventSlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cria um slot em um evento",
    description="Cadastra um novo slot (palestra, workshop etc.) vinculado ao evento.",
)
def create_event_slot(
    event_id: UUID,
    body: EventSlotCreate,
    service: EventSlotService = Depends(get_event_slot_service),
) -> EventSlotResponse:
    return service.create_slot(event_id, body)


# ---------------------------------------------------------------------------
# DELETE /events/{event_id}/slots/{slot_id} — remove um slot
# ---------------------------------------------------------------------------

@router.delete(
    "/events/{event_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um slot de um evento",
    description=(
        "Remove o slot especificado. Todas as inscrições vinculadas ao slot "
        "são removidas em cascata (ON DELETE CASCADE)."
    ),
)
def delete_event_slot(
    event_id: UUID,
    slot_id: UUID,
    service: EventSlotService = Depends(get_event_slot_service),
) -> None:
    service.delete_slot(event_id, slot_id)


# ---------------------------------------------------------------------------
# GET /events/{event_id}/guests/{user_id}/slots — slots de um inscrito
# ---------------------------------------------------------------------------

@router.get(
    "/events/{event_id}/guests/{user_id}/slots",
    response_model=list[RegistrationSlotResponse],
    status_code=status.HTTP_200_OK,
    summary="Lista os slots nos quais um convidado está inscrito",
    description="Retorna todos os slots do evento aos quais o usuário se inscreveu.",
)
def list_user_slots(
    event_id: UUID,
    user_id: UUID,
    service: RegistrationSlotService = Depends(get_registration_slot_service),
) -> list[RegistrationSlotResponse]:
    return service.list_user_slots(event_id, user_id)


# ---------------------------------------------------------------------------
# POST /events/{event_id}/guests/{user_id}/slots — inscreve em um slot
# ---------------------------------------------------------------------------

@router.post(
    "/events/{event_id}/guests/{user_id}/slots",
    response_model=RegistrationSlotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Inscreve um convidado em um slot",
    description=(
        "Vincula o usuário ao slot especificado dentro do evento. "
        "O usuário precisa já estar inscrito no evento (registrations). "
        "Retorna 409 se o slot estiver cheio ou se o usuário já estiver inscrito nele."
    ),
    responses={
        404: {"description": "Slot não encontrado"},
        409: {"description": "Slot cheio ou usuário já inscrito no slot"},
    },
)
def register_user_slot(
    event_id: UUID,
    user_id: UUID,
    body: RegistrationSlotCreate,
    service: RegistrationSlotService = Depends(get_registration_slot_service),
) -> RegistrationSlotResponse:
    return service.register_slot(event_id, user_id, body.slot_id)


# ---------------------------------------------------------------------------
# DELETE /events/{event_id}/guests/{user_id}/slots/{slot_id} — remove inscrição no slot
# ---------------------------------------------------------------------------

@router.delete(
    "/events/{event_id}/guests/{user_id}/slots/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a inscrição de um convidado em um slot",
    description="Cancela o vínculo do usuário com o slot. Não afeta a inscrição no evento.",
    responses={
        404: {"description": "Inscrição no slot não encontrada"},
    },
)
def unregister_user_slot(
    event_id: UUID,
    user_id: UUID,
    slot_id: UUID,
    service: RegistrationSlotService = Depends(get_registration_slot_service),
) -> None:
    service.unregister_slot(event_id, user_id, slot_id)
