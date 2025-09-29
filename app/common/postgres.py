from logging import getLogger

import boto3
from sqlalchemy import URL, text
from sqlalchemy.event import listen
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.common.tls import custom_ca_certs
from app.config import config
from app.snapshot.orm_models import start_mappers

logger = getLogger(__name__)

engine: AsyncEngine = None
async_session_factory: async_sessionmaker[AsyncSession] = None


async def get_sql_engine() -> AsyncEngine:
    global engine

    if engine is not None:
        return engine

    url = URL.create(
        drivername="postgresql+psycopg",
        username=config.postgres.user,
        host=config.postgres.host,
        port=config.postgres.port,
        database=config.postgres.database
    )

    cert = custom_ca_certs.get(config.postgres.rds_truststore)

    if cert:
        logger.info("Creating Postgres SQLAlchemy engine with custom TLS cert %s", config.postgres.rds_truststore)
        engine = create_async_engine(
            url,
            connect_args={
                "sslmode": config.postgres.ssl_mode,
                "sslrootcert": cert
            }
        )
    else:
        logger.info("Creating Postgres SQLAlchemy engine without custom TLS cert")
        engine = create_async_engine(url)

    start_mappers()
    logger.info("SQLAlchemy ORM mappers started")

    listen(engine.sync_engine, "do_connect", get_token)

    logger.info("Testing Postgres SQLAlchemy connection to %s", config.postgres.host)
    await check_connection(engine)

    return engine


async def check_connection(engine: AsyncEngine) -> bool:
    async with engine.connect() as connection:
        await connection.execute(text("SELECT 1 FROM knowledge_vectors"))


def get_token(dialect, conn_rec, cargs, cparams):  # noqa: ARG001
    if config.python_env == "development":
        cparams["password"] = config.postgres.password
    else:
        logger.info("Generating RDS auth token for Postgres connection")

        client = boto3.client("rds")

        token = client.generate_db_auth_token(
            Region=config.aws_region,
            DBHostname=config.postgres.host,
            Port=config.postgres.port,
            DBUsername=config.postgres.user
        )

        logger.info("Generated RDS auth token for Postgres connection")

        cparams["password"] = token


async def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global async_session_factory

    if async_session_factory is None:
        engine = await get_sql_engine()
        async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

    return async_session_factory

