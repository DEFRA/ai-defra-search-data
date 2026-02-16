# ai-defra-search-data

A agentic workflow that demonstrates client-side Model Context Protocol (MCP) usage within a FastAPI application.

## Prerequisites
- [Python](https://docs.python.org/3/using/index.html) `>= 3.13` - We recommend using [uv](https://docs.astral.sh/uv/getting-started/installation/) to manage your Python environment.
- [pipx](https://pipxproject.github.io/pipx/installation/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 
- [Docker and Docker Compose](https://docs.docker.com/get-docker/)
- [MCP Inspector](https://github.com/modelcontextprotocol/inspector) - Optional, but recommended for developing against MCP server.

## Requirements

### Python

Please install Python `>= 3.13` and `pipx` in your environment. This template uses [uv](https://github.com/astral-sh/uv) to manage the environment and dependencies.

```python
# install uv via pipx
pipx install uv

# sync dependencies
uv sync
```

This opinionated template uses the [`Fast API`](https://fastapi.tiangolo.com/) Python API framework.

### Environment Variable Configuration

The application uses Pydantic's `BaseSettings` for configuration management in `app/config.py`, automatically mapping environment variables to configuration fields.

In CDP, environment variables and secrets need to be set using CDP conventions.  See links below:
- [CDP App Config](https://github.com/DEFRA/cdp-documentation/blob/main/how-to/config.md)
- [CDP Secrets](https://github.com/DEFRA/cdp-documentation/blob/main/how-to/secrets.md)

For local development - see [instructions below](#local-development).

### Linting and Formatting

This project uses [Ruff](https://github.com/astral-sh/ruff) for linting and formatting Python code.

#### Running Ruff

To run Ruff from the command line:

```bash
# Run linting with auto-fix
uv run ruff check . --fix

# Run formatting
uv run ruff format .
```

## Local development

### Setup & Configuration

Follow the convention below for environment variables and secrets in local development.

**Note** that it does not use `.env` or `python-dotenv` as this is not the convention in the CDP environment.

**Environment variables:** `compose/aws.env`.

**Secrets:** `compose/secrets.env`. You need to create this, as it's excluded from version control.

**Libraries:** Ensure the python virtual environment is configured and libraries are installed using `uv sync`, [as above](#python)

### Development

This app can be run locally by either using the Docker Compose project or via the provided script `scripts/start_dev_server.sh`.

#### Using Docker Compose

To run the application using Docker Compose, you can use the following command:

```bash
docker compose --profile service up --build
```

If you want to enable hot-reloading, you can press the `w` key once the compose project is running to enable `watch` mode.

#### Debugging

This project is also configured for debugging with `debugpy`. You should follow the instructions below (for your IDE) to set up the debugging environment.

**Visual Studio Code**

1. Install the [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [Python Debugger](https://marketplace.visualstudio.com/items?itemName=ms-python.debugpy) extensions for Visual Studio Code.
2. Open the command palette (Ctrl+Shift+P) and select "Debug: Add Configuration".
3. In the dropdown, select "Python Debugger" -> "Python: Remote Attach".
4. Enter the following configuration:
* host => localhost
* port => 5678
* localRoot => ${workspaceFolder}
* remoteRoot => /home/nonroot

You can now start the service in debug mode by running the following command:
```bash
docker compose --profile -f compose.yml -f compose.debug.yml up --build
```

You should now be able to attach the debugger to the running service.

### Testing

Ensure the python virtual environment is configured and libraries are installed using `uv sync`, [as above](#python)

Testing follows the [FastApi documented approach](https://fastapi.tiangolo.com/tutorial/testing/); using pytest & starlette.

To test the application run:

```bash
uv run pytest
```

## Python client

Install the package and use the sync or async client:

```python
from app.client import DefraDataClient, AsyncDefraDataClient
from app.client import CreateKnowledgeGroupRequest, KnowledgeSourceInput, SourceType

# Sync
with DefraDataClient(base_url="http://data.localhost") as client:
    groups = client.list_groups()
    group = client.create_group(CreateKnowledgeGroupRequest(
        name="My Group",
        description="Description",
        owner="me",
        sources=[KnowledgeSourceInput(name="doc", type=SourceType.BLOB, location="s3://bucket/file.pdf")],
    ))
    client.ingest_group(group.group_id)
    results = client.query(group.group_id, "search query", max_results=10)

# Async
async with AsyncDefraDataClient(base_url="http://data.localhost") as client:
    groups = await client.list_groups()
    group_id = groups[0].group_id
    snapshots = await client.list_group_snapshots(group_id)
    await client.activate_snapshot(snapshots[0].snapshot_id)
```

## CLI

After `uv sync`, use the `knowledge-cli` entry point. Options: `--base-url` / `-u`, `--timeout` / `-t`, `--json` / `-j`. Base URL can be set via `DEFRA_DATA_URL`.

```bash
# Groups
uv run knowledge-cli groups list
uv run knowledge-cli groups get <group_id>
uv run knowledge-cli groups create --name "My Group" --description "..." --owner "me" [-s name:BLOB:s3://bucket/file.pdf]
uv run knowledge-cli groups add-source <group_id> --name "doc" --type BLOB --location "s3://bucket/file.pdf"
uv run knowledge-cli groups ingest <group_id>
uv run knowledge-cli groups snapshots <group_id>

# Snapshots
uv run knowledge-cli snapshots get <snapshot_id>
uv run knowledge-cli snapshots activate <snapshot_id>

# Vector search
uv run knowledge-cli query <group_id> "search query" [--max-results 10]
```

## API endpoints

| Method | Endpoint | Description |
| :----- | :------- | :----------- |
| GET | `/health` | Health check |
| GET | `/knowledge/groups` | List knowledge groups |
| POST | `/knowledge/groups` | Create knowledge group |
| GET | `/knowledge/groups/{group_id}` | Get knowledge group |
| GET | `/knowledge/groups/{group_id}/snapshots` | List snapshots for group |
| POST | `/knowledge/groups/{group_id}/ingest` | Trigger ingestion (202) |
| PATCH | `/knowledge/groups/{group_id}/sources` | Add source to group |
| GET | `/snapshots/{snapshot_id}` | Get snapshot |
| POST | `/snapshots/query` | Vector search |
| PATCH | `/snapshots/{snapshot_id}/activate` | Activate snapshot |

## Custom Cloudwatch Metrics

Uses the [aws embedded metrics library](https://github.com/awslabs/aws-embedded-metrics-python). An example can be found in `metrics.py`

In order to make this library work in the environments, the environment variable `AWS_EMF_ENVIRONMENT=local` is set in the app config. This tells the library to use the local cloudwatch agent that has been configured in CDP, and uses the environment variables set up in CDP `AWS_EMF_AGENT_ENDPOINT`, `AWS_EMF_LOG_GROUP_NAME`, `AWS_EMF_LOG_STREAM_NAME`, `AWS_EMF_NAMESPACE`, `AWS_EMF_SERVICE_NAME`

## Licence

THIS INFORMATION IS LICENSED UNDER THE CONDITIONS OF THE OPEN GOVERNMENT LICENCE found at:

<http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3>

The following attribution statement MUST be cited in your products and applications when using this information.

> Contains public sector information licensed under the Open Government license v3

### About the licence

The Open Government Licence (OGL) was developed by the Controller of Her Majesty's Stationery Office (HMSO) to enable
information providers in the public sector to license the use and re-use of their information under a common open
licence.

It is designed to encourage use and re-use of information freely and flexibly, with only a few conditions.
