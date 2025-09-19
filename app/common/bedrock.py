import json
from abc import ABC, abstractmethod

import boto3

from app.config import config

bedrock_client: boto3.client = None


def get_bedrock_client():
    global bedrock_client

    if bedrock_client is None:
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=config.aws_region
        )

    return bedrock_client


class AbstractEmbeddingService(ABC):
    @abstractmethod
    def generate_embeddings(self, input_text: str):
        pass


class BedrockEmbeddingService(AbstractEmbeddingService):
    def __init__(self, client: boto3.client, model_id: str):
        self.client = client
        self.model_id = model_id


    def generate_embeddings(self, input_text: str):
        request = {
            "inputText": input_text
        }

        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(request)
        )

        response_body = json.loads(response["body"].read().decode("utf-8"))

        return response_body["embedding"]

