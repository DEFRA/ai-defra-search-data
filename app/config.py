
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class MsGraphConfig(BaseSettings):
    model_config = SettingsConfigDict()
    graph_enabled: bool = Field(default=False, alias="MS_GRAPH_ENABLED")
    tenant_id: str | None = Field(default=None, alias="MS_GRAPH_TENANT_ID")
    client_id: str | None = Field(default=None, alias="MS_GRAPH_CLIENT_ID")
    client_secret: str | None = Field(default=None, alias="MS_GRAPH_CLIENT_SECRET")
    scope: str | None = Field(default="https://graph.microsoft.com/.default", alias="MS_GRAPH_SCOPE")


class BedrockEmbeddingConfig(BaseSettings):
    model_config = SettingsConfigDict()
    model_id: str = Field(..., alias="BEDROCK_EMBEDDING_MODEL_ID")
    guardrail_identifier: str | None = Field(default=None, alias="EMBEDDING_MODEL_GUARDRAIL_IDENTIFIER")
    guardrail_version: str | None = Field(default=None, alias="EMBEDDING_MODEL_GUARDRAIL_VERSION")


class PostgresConfig(BaseSettings):
    model_config = SettingsConfigDict()
    host: str = Field(..., alias="POSTGRES_HOST")
    port: int = Field(5432, alias="POSTGRES_PORT")
    database: str = Field(default="ai_defra_search_data", alias="POSTGRES_DB")
    user: str = Field(default="ai_defra_search_data", alias="POSTGRES_USER")
    password: str | None = Field(default=None, alias="POSTGRES_PASSWORD")
    ssl_mode: str = Field(default="require", alias="POSTGRES_SSL_MODE")
    rds_truststore: str | None = Field(default=None, alias="TRUSTSTORE_RDS_ROOT_CA")


class AppConfig(BaseSettings):
    aws_region: str = Field(..., alias="AWS_REGION")
    model_config = SettingsConfigDict()
    python_env: str = "development"
    host: str | None = None
    port: int
    log_config: str | None = None
    mongo_uri: str | None = None
    mongo_database: str = "ai-defra-search-data"
    mongo_truststore: str = "TRUSTSTORE_CDP_ROOT_CA"
    aws_endpoint_url: str | None = None
    http_proxy: HttpUrl | None = None
    enable_metrics: bool = False
    tracing_header: str = "x-cdp-request-id"
    ms_graph: MsGraphConfig = MsGraphConfig()
    postgres: PostgresConfig = PostgresConfig()
    bedrock_embedding_config: BedrockEmbeddingConfig = BedrockEmbeddingConfig()


config = AppConfig()
