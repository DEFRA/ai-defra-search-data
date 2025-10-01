from contextlib import asynccontextmanager
from logging import getLogger

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.common.mongo import get_mongo_client
from app.common.postgres import get_sql_engine
from app.common.tracing import TraceIdMiddleware
from app.health.router import router as health_router
from app.infra.mcp_server import data_mcp_server
from app.knowledge_management.router import router as knowledge_management_router

logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    client = await get_mongo_client()
    logger.info("MongoDB client connected")

    engine = await get_sql_engine()
    logger.info("Postgres SQLAlchemy engine created")

    yield

    # Shutdown
    if client:
        await client.close()
        logger.info("MongoDB client closed")

    if engine:
        await engine.dispose()
        logger.info("Postgres SQLAlchemy engine disposed")

mcp_app = data_mcp_server.http_app(path="/mcp")


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with lifespan(app), mcp_app.lifespan(app):
        yield


app = FastAPI(lifespan=combined_lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):  # noqa: ARG001
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


# Setup middleware
app.add_middleware(TraceIdMiddleware)

# Setup Routes
app.include_router(health_router)
app.include_router(knowledge_management_router)

app.mount("/", mcp_app)
