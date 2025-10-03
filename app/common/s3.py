import boto3

from app.config import config

s3_client: boto3.client = None


def get_s3_client():
    global s3_client

    if s3_client is None:
        s3_client = boto3.client(
            "s3",
            region_name=config.aws_region,
            endpoint_url=config.localstack_url
        )

    return s3_client
