from logging import getLogger

import uvicorn

from app.config import config

logger = getLogger(__name__)


def main() -> None:
    uvicorn.run(
        "app.infra.fastapi_app:app",
        host=config.host,
        port=config.port,
        log_config=config.log_config,
        reload=config.python_env == "development"
    )


if __name__ == "__main__":
    main()
