import boto3

from src.config import get_settings


def get_boto3_client(service_name: str):
    settings = get_settings()

    client_kwargs = {
        "service_name": service_name,
        "region_name": settings.AWS_REGION,
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
    }

    if settings.AWS_ENDPOINT_URL:
        client_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

    return boto3.client(**client_kwargs)
