"""HTTP controller for the registration endpoint."""

from fastapi import APIRouter, Depends, status

from .schemas import RegistrationCreateRequest, RegistrationResponse
from .service import RegistrationService, get_registration_service

router = APIRouter(tags=["registration"])


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegistrationCreateRequest,
    service: RegistrationService = Depends(get_registration_service),
) -> RegistrationResponse:
    registration = service.register(body.eventId, body.userId)
    return RegistrationResponse(
        eventId=registration.event_id,
        userId=registration.user_id,
        registrationTimestamp=registration.registration_timestamp,
        confirmationTimestamp=registration.confirmation_timestamp,
    )