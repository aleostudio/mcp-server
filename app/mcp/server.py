from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from mcp.server.fastmcp import FastMCP
from app.core import settings, logger
from app.mcp.context import AppContext
import httpx

# Lifecycle management
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    logger.info(f"Starting MCP server '{settings.server_name}'...")

    http_client = httpx.AsyncClient(
        timeout=settings.http_timeout,
        limits=httpx.Limits(max_connections=settings.http_max_connections)
    )
    
    try:
        yield AppContext(
            http_client=http_client,
            startup_time=datetime.now(timezone.utc),
            settings=settings
        )
    finally:
        await http_client.aclose()
        logger.info("MCP server shutdown complete")


# Server instance
mcp = FastMCP(
    name=settings.server_name,
    lifespan=app_lifespan
)
