"""HTTP client for the Events service."""

from collections.abc import Mapping
import logging
from typing import Any, TypeVar
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
import httpx
from pydantic import BaseModel

from src.config import Settings, get_settings

from .schemas import (
    ActivityResponse,
    CreateEventRequest,
    CreateEventRoleRequest,
    EventListResponse,
    EventResponse,
    EventRoleResponse,
    EventsMetricsResponse,
    UpdateEventRequest,
)

logger = logging.getLogger(__name__)

EVENTS_UNAVAILABLE_DETAIL = "Events service unavailable"
EVENTS_REJECTED_DETAIL = "Events service rejected request"
NOT_FOUND_STATUS = status.HTTP_404_NOT_FOUND

ModelT = TypeVar("ModelT", bound=BaseModel)


class EventsClient:
    """Encapsulates calls to the Events service."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 5.0,
        transport: httpx.BaseTransport | None = None,
        settings: Settings | None = None,
    ) -> None:
        app_settings = settings or get_settings()
        self._base_url = base_url or app_settings.EVENTS_SERVICE_BASE_URL
        self._timeout = timeout
        self._transport = transport

    def create_event(
        self,
        event: CreateEventRequest | Mapping[str, Any],
    ) -> EventResponse:
        response = self._request("POST", "/events", json=self._json_payload(event))
        return self._parse_response(response, EventResponse)

    def list_events(self, page: int = 1, limit: int = 20) -> EventListResponse:
        response = self._request(
            "GET",
            "/events",
            params={"page": page, "limit": limit},
        )
        return self._parse_response(response, EventListResponse)

    def get_all_events(self, limit: int = 100) -> list[EventResponse]:
        """Return all events by following the Events service pagination."""

        events: list[EventResponse] = []
        page = 1

        while True:
            result = self.list_events(page=page, limit=limit)
            events.extend(result.data)

            if len(events) >= result.total or not result.data:
                return events

            page += 1

    def get_event_by_id(self, event_id: str | UUID) -> EventResponse | None:
        response = self._request(
            "GET", self._event_path(event_id), allow_not_found=True
        )
        if response.status_code == NOT_FOUND_STATUS:
            return None
        return self._parse_response(response, EventResponse)

    def replace_event(
        self,
        event_id: str | UUID,
        event: CreateEventRequest | Mapping[str, Any],
    ) -> EventResponse:
        response = self._request(
            "PUT",
            self._event_path(event_id),
            json=self._json_payload(event),
        )
        return self._parse_response(response, EventResponse)

    def update_event(
        self,
        event_id: str | UUID,
        event: UpdateEventRequest | Mapping[str, Any],
    ) -> EventResponse:
        response = self._request(
            "PATCH",
            self._event_path(event_id),
            json=self._json_payload(event),
        )
        return self._parse_response(response, EventResponse)

    def delete_event(self, event_id: str | UUID) -> EventResponse:
        response = self._request("DELETE", self._event_path(event_id))
        return self._parse_response(response, EventResponse)

    def get_events_metrics(self) -> EventsMetricsResponse:
        response = self._request("GET", "/events/metrics")
        return self._parse_response(response, EventsMetricsResponse)

    def list_event_activities(self, event_id: str | UUID) -> list[ActivityResponse]:
        response = self._request("GET", f"{self._event_path(event_id)}/activitys")
        return self._parse_response_list(response, ActivityResponse)

    def list_event_activitys(self, event_id: str | UUID) -> list[ActivityResponse]:
        """Compatibility alias for the Events service route spelling."""

        return self.list_event_activities(event_id)

    def list_event_roles(self, event_id: str | UUID) -> list[EventRoleResponse]:
        response = self._request("GET", f"{self._event_path(event_id)}/roles")
        return self._parse_response_list(response, EventRoleResponse)

    def add_event_role(
        self,
        event_id: str | UUID,
        role: str | CreateEventRoleRequest | Mapping[str, Any],
    ) -> EventRoleResponse:
        payload = role if not isinstance(role, str) else {"role": role}
        response = self._request(
            "POST",
            f"{self._event_path(event_id)}/roles",
            json=self._json_payload(payload),
        )
        return self._parse_response(response, EventRoleResponse)

    def remove_event_role(self, event_id: str | UUID, role: str) -> None:
        self._request("DELETE", f"{self._event_path(event_id)}/roles/{role}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        allow_not_found: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            logger.warning("Events service timeout on %s %s", method, path)
            raise self._service_unavailable() from exc
        except httpx.RequestError as exc:
            logger.warning(
                "Events service request failed on %s %s: %s", method, path, exc
            )
            raise self._service_unavailable() from exc

        self._raise_for_error(response, allow_not_found=allow_not_found)
        return response

    @staticmethod
    def _json_payload(payload: BaseModel | Mapping[str, Any]) -> dict[str, Any]:
        encoded = jsonable_encoder(payload, exclude_none=True)
        if not isinstance(encoded, dict):
            raise TypeError("Events service payload must be a JSON object")
        return encoded

    @staticmethod
    def _parse_response(response: httpx.Response, model: type[ModelT]) -> ModelT:
        return model.model_validate(response.json())

    @staticmethod
    def _parse_response_list(
        response: httpx.Response,
        model: type[ModelT],
    ) -> list[ModelT]:
        return [model.model_validate(item) for item in response.json()]

    @staticmethod
    def _event_path(event_id: str | UUID) -> str:
        return f"/events/{event_id}"

    @staticmethod
    def _raise_for_error(
        response: httpx.Response,
        *,
        allow_not_found: bool,
    ) -> None:
        if allow_not_found and response.status_code == NOT_FOUND_STATUS:
            return

        if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise EventsClient._service_unavailable()

        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            raise HTTPException(
                status_code=response.status_code,
                detail=EVENTS_REJECTED_DETAIL,
            )

    @staticmethod
    def _service_unavailable() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=EVENTS_UNAVAILABLE_DETAIL,
        )


def get_events_client(
    settings: Settings = Depends(get_settings),
) -> EventsClient:
    """Return an Events client instance for FastAPI dependency injection."""

    return EventsClient(settings=settings)
