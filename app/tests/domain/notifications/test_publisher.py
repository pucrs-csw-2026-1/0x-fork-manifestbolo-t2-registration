"""Unit tests for the SNS event publisher."""

from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import boto3
from moto import mock_aws
import pytest

from src.config import get_settings
from src.domain.notifications.publisher import SnsEventPublisher
from src.domain.notifications.schemas import DomainEvent, DomainEventType


@pytest.fixture(autouse=True)
def _clear_aws_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure @mock_aws clients hit moto in-memory, not a real endpoint.

    The Tests workflow injects ``AWS_ENDPOINT_URL=http://localhost:4566`` and
    boto3 honors it globally, but moto does not intercept calls carrying an
    explicit endpoint_url pointing at a real host, so the clients would try to
    reach an absent LocalStack. Clearing it here mirrors the ``client`` fixture
    in ``conftest.py``.
    """
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)


def _sample_event() -> DomainEvent:
    return DomainEvent(
        event_id=uuid4(),
        event_type=DomainEventType.REGISTRATION_CONFIRMED,
        source="registration-events",
        occurred_at=datetime.now(UTC),
        resource_ref=f"{uuid4()}:{uuid4()}",
    )


@mock_aws
def test_publish_succeeds_on_first_attempt() -> None:
    sns_client = boto3.client("sns", region_name="us-east-1")
    publisher = SnsEventPublisher(sns_client=sns_client, settings=get_settings())
    event = _sample_event()

    publisher.publish(event)

    assert len(sns_client.list_topics()["Topics"]) == 1


@mock_aws
def test_publish_succeeds_after_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    sns_client = boto3.client("sns", region_name="us-east-1")
    publisher = SnsEventPublisher(
        sns_client=sns_client, settings=get_settings(), retry_delays=(0, 0)
    )
    real_publish = publisher._sns_client.publish
    calls = {"count": 0}

    def flaky_publish(*args: object, **kwargs: object) -> object:
        calls["count"] += 1
        if calls["count"] < 2:
            raise RuntimeError("simulated transient failure")
        return real_publish(*args, **kwargs)

    monkeypatch.setattr(publisher._sns_client, "publish", flaky_publish)

    publisher.publish(_sample_event())

    assert calls["count"] == 2


def test_publish_logs_and_swallows_error_after_all_retries_fail(
    caplog: pytest.LogCaptureFixture,
) -> None:
    failing_client = MagicMock()
    failing_client.create_topic.side_effect = RuntimeError("sns down")
    publisher = SnsEventPublisher(sns_client=failing_client, retry_delays=(0, 0))

    with caplog.at_level("ERROR"):
        publisher.publish(_sample_event())  # must not raise

    assert any("Giving up publishing" in record.message for record in caplog.records)
    assert failing_client.create_topic.call_count == 3
