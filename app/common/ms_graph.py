from azure.identity.aio import ClientSecretCredential
from httpx import AsyncClient
from kiota_authentication_azure.azure_identity_authentication_provider import (
    AzureIdentityAuthenticationProvider,
)
from msgraph import GraphRequestAdapter, GraphServiceClient
from msgraph_core import GraphClientFactory

from app.config import config

proxies = {
    "http": str(config.http_proxy),
    "https": str(config.http_proxy)
}


def create_graph_client(
        http_client: AsyncClient,
        scopes: list[str] = None
    ) -> GraphServiceClient:
    """
    Create a Graph Service client with configurable timeouts.

    Args:
        request_timeout_connect: Connection timeout in seconds
        scopes: Optional list of scopes for authentication

    Returns:
        Configured GraphServiceClient instance
    """
    if not config.ms_graph.graph_enabled:
        msg = "The MS Graph integration feature flag is disabled"
        raise ValueError(msg)


    credential = ClientSecretCredential(
        tenant_id=config.ms_graph.tenant_id,
        client_id=config.ms_graph.client_id,
        client_secret=config.ms_graph.client_secret,
        proxies=proxies if config.http_proxy else None
    )

    auth_provider = AzureIdentityAuthenticationProvider(
        credentials=credential,
        scopes=scopes or [config.ms_graph.scope]
    )

    graph_client = GraphClientFactory.create_with_default_middleware(
        client=http_client
    )

    request_adapter = GraphRequestAdapter(auth_provider, graph_client)

    return GraphServiceClient(request_adapter=request_adapter)

