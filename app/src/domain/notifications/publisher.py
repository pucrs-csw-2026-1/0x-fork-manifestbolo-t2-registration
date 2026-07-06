"""SNS publisher for registration domain events."""

import logging
import time
from typing import Any

from fastapi import Depends

from src.aws import get_boto3_client
from src.config import Settings, get_settings

from .schemas import DomainEvent

logger = logging.getLogger(__name__)

_RETRY_DELAYS_SECONDS: tuple[float, ...] = (0.2, 0.4)


class SnsEventPublisher:
    """Publishes domain events to the registration SNS topic.

    Best-effort delivery: retries with short backoff, never raises to the
    caller. A publish failure must never break the HTTP response of the
    operation that triggered the event.
    """

    def __init__(
        self,
        sns_client: Any = None,
        settings: Settings | None = None,
        retry_delays: tuple[float, ...] = _RETRY_DELAYS_SECONDS,
    ) -> None:
        self._settings = settings or get_settings()
        self._sns_client = sns_client or get_boto3_client("sns")
        self._retry_delays = retry_delays
        self._topic_arn: str | None = None

    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event, retrying on failure. Never raises."""

        payload = event.model_dump_json()
        attempts = len(self._retry_delays) + 1

        for attempt, delay in enumerate((0.0, *self._retry_delays), start=1):
            if delay:
                time.sleep(delay)
            try:
                topic_arn = self._get_topic_arn()
                self._sns_client.publish(
                    TopicArn=topic_arn,
                    Message=payload,
                    MessageAttributes={
                        "event_type": {
                            "DataType": "String",
                            "StringValue": event.event_type.value,
                        }
                    },
                )
                return
            except Exception as exc:
                logger.warning(
                    "Failed to publish %s for event_id=%s (attempt %d/%d): %s",
                    event.event_type.value,
                    event.event_id,
                    attempt,
                    attempts,
                    exc,
                )

        logger.error(
            "Giving up publishing %s for event_id=%s resource_ref=%s after %d attempts",
            event.event_type.value,
            event.event_id,
            event.resource_ref,
            attempts,
        )

    def _get_topic_arn(self) -> str:
        if self._topic_arn is None:
            topic_name = self._settings.SNS_REGISTRATION_TOPIC_NAME
            response = self._sns_client.create_topic(Name=topic_name)
            self._topic_arn = response["TopicArn"]
        return self._topic_arn


def get_sns_event_publisher(
    settings: Settings = Depends(get_settings),
) -> SnsEventPublisher:
    """Return an SNS publisher instance for FastAPI dependency injection."""

    return SnsEventPublisher(settings=settings)
