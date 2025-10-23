from fastmcp import FastMCP

data_mcp_server = FastMCP("ai-defra-search-data MCP Server")

from app.snapshot import mcp_tools  # noqa: F401, E402
