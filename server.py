import logging
import sys
from datetime import datetime, timezone, timedelta
from typing import Any
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from functools import lru_cache
import re
import json
import base64
import httpx
from mcp.server.fastmcp import FastMCP, Context
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


# Config
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        extra="ignore"
    )
    
    # Server
    server_name: str = Field(default="mcp-server", description="MCP server name")
    host: str = Field(default="0.0.0.0", description="Host binding for SSE")
    port: int = Field(default=8000, ge=1, le=65535, description="Port for SSE")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # HTTP Client
    http_timeout: float = Field(default=30.0, gt=0, description="HTTP requests timeout")
    http_max_connections: int = Field(default=100, ge=1, description="Max pool connections")
    
    # Tool limits
    max_text_length: int = Field(default=100_000, ge=1000, description="Max chars for process_text")
    max_url_content: int = Field(default=2000, ge=100, description="Max chars response fetch_url")
    
    # Feature flags
    enable_fetch_tool: bool = Field(default=True, description="Enable fetch_url tool")
    allowed_fetch_domains: list[str] | None = Field(default=None, description="Allowed domains for fetch (None=all)")


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# App context
@dataclass
class AppContext:
    http_client: httpx.AsyncClient
    startup_time: datetime
    settings: Settings


# Lifecycle
@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    cfg = get_settings()
    logger.info(f"Starting MCP server '{cfg.server_name}'...")
    logger.info(f"Config: debug={cfg.debug}, http_timeout={cfg.http_timeout}s")
    
    http_client = httpx.AsyncClient(
        timeout=cfg.http_timeout,
        limits=httpx.Limits(max_connections=cfg.http_max_connections)
    )
    try:
        yield AppContext(
            http_client=http_client,
            startup_time=datetime.now(timezone.utc),
            settings=cfg
        )
    finally:
        await http_client.aclose()
        logger.info("MCP server shutdown complete")


# Server init
mcp = FastMCP(name=settings.server_name, lifespan=app_lifespan)


# =============================================================================
# Calculator tool
# =============================================================================
@mcp.tool()
def calculate(operation: str, a: float, b: float) -> dict[str, Any]:
    """
    Execute basic math operation.

    Args:
        operation: operation to execute (add, subtract, multiply, divide, power)
        a: first operand
        b: second operand

    Returns:
        Operation result with details
    """
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else None,
        "power": lambda x, y: x ** y,
    }

    if operation not in operations:
        return {
            "success": False,
            "error": f"Operation '{operation}' not supported. Use: {list(operations.keys())}"
        }

    if operation == "divide" and b == 0:
        return {"success": False, "error": "Division by zero not allowed"}

    result = operations[operation](a, b)
    return {
        "success": True,
        "operation": operation,
        "operands": {"a": a, "b": b},
        "result": result
    }


# =============================================================================
# DateTime tool
# =============================================================================
@mcp.tool()
def get_datetime(timezone_offset: int = 0, format_type: str = "iso") -> dict[str, Any]:
    """
    Get current date/time with configurable format.

    Args:
        timezone_offset: UTC offset in hours (-12 +14)
        format_type: output format (iso, human, unix, components)

    Returns:
        Date/time in the required format
    """
    if not -12 <= timezone_offset <= 14:
        return {"success": False, "error": "timezone_offset must be between -12 and +14"}

    now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)

    formats = {
        "iso": now.isoformat(),
        "human": now.strftime("%A, %d %B %Y - %H:%M:%S"),
        "unix": int(now.timestamp()),
        "components": {
            "year": now.year,
            "month": now.month,
            "day": now.day,
            "hour": now.hour,
            "minute": now.minute,
            "second": now.second,
            "weekday": now.strftime("%A"),
        }
    }

    if format_type not in formats:
        return {"success": False, "error": f"format_type must be: {list(formats.keys())}"}

    return {
        "success": True,
        "timezone_offset": timezone_offset,
        "format": format_type,
        "datetime": formats[format_type]
    }


# =============================================================================
# Text processor tool
# =============================================================================
@mcp.tool()
def process_text(text: str, operation: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Handle text with various operations.

    Args:
        text: text to handle
        operation: action to perform (word_count, char_count, reverse, uppercase, lowercase, title_case, extract_emails, extract_urls, summarize_stats)
        options: additional options for specific operations

    Returns:
        Operation result
    """
    cfg = get_settings()
    
    if len(text) > cfg.max_text_length:
        return {"success": False, "error": f"Text too long. Max {cfg.max_text_length} chars"}

    options = options or {}

    operations = {
        "word_count": lambda t: {"count": len(t.split())},
        "char_count": lambda t: {"count": len(t), "count_no_spaces": len(t.replace(" ", ""))},
        "reverse": lambda t: {"result": t[::-1]},
        "uppercase": lambda t: {"result": t.upper()},
        "lowercase": lambda t: {"result": t.lower()},
        "title_case": lambda t: {"result": t.title()},
        "extract_emails": lambda t: {"emails": re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', t)},
        "extract_urls": lambda t: {"urls": re.findall(r'https?://[^\s]+', t)},
        "summarize_stats": lambda t: {
            "total_chars": len(t),
            "total_words": len(t.split()),
            "total_lines": len(t.splitlines()),
            "avg_word_length": round(sum(len(w) for w in t.split()) / max(len(t.split()), 1), 2),
        }
    }

    if operation not in operations:
        return {"success": False, "error": f"Operation not supported. Use: {list(operations.keys())}"}

    try:
        result = operations[operation](text)
        return {"success": True, "operation": operation, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# =============================================================================
# HTTP fetch tool
# =============================================================================
@mcp.tool()
async def fetch_url(url: str, method: str = "GET", ctx: Context = None) -> dict[str, Any]:
    """
    Execute HTTP requests to external URLs.

    Args:
        url: URL to fetch
        method: HTTP method (GET, HEAD)

    Returns:
        Status code, headers and content (truncated if too long)
    """
    cfg = get_settings()
    
    if not cfg.enable_fetch_tool:
        return {"success": False, "error": "Tool fetch_url disabled"}
    
    if method.upper() not in ["GET", "HEAD"]:
        return {"success": False, "error": "Only GET and HEAD are supported"}

    if not url.startswith(("http://", "https://")):
        return {"success": False, "error": "URL must start with http:// or https://"}
    
    if cfg.allowed_fetch_domains:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        if not any(domain.endswith(allowed) for allowed in cfg.allowed_fetch_domains):
            return {"success": False, "error": f"Domain not allowed. Allowed: {cfg.allowed_fetch_domains}"}

    client: httpx.AsyncClient | None = None
    should_close = False

    try:
        if ctx and hasattr(ctx, 'request_context') and ctx.request_context.lifespan_context:
            client = ctx.request_context.lifespan_context.http_client
        else:
            client = httpx.AsyncClient(timeout=cfg.http_timeout)
            should_close = True

        response = await client.request(method.upper(), url)
        content = response.text[:cfg.max_url_content] if method.upper() == "GET" else None

        return {
            "success": True,
            "url": url,
            "method": method.upper(),
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_preview": content,
            "content_length": len(response.text) if method.upper() == "GET" else None
        }
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}
    finally:
        if should_close and client:
            await client.aclose()


# =============================================================================
# Data converter tool
# =============================================================================
@mcp.tool()
def convert_data(data: str, from_format: str, to_format: str) -> dict[str, Any]:
    """
    Convert data in different formats.

    Args:
        data: data to convert
        from_format: source format (json, base64, hex)
        to_format: destination format (json, base64, hex)

    Returns:
        Converted data
    """
    supported = ["json", "base64", "hex"]

    if from_format not in supported or to_format not in supported:
        return {"success": False, "error": f"Supported formats: {supported}"}

    try:
        if from_format == "json":
            parsed = json.loads(data)
        elif from_format == "base64":
            parsed = base64.b64decode(data).decode('utf-8')
        elif from_format == "hex":
            parsed = bytes.fromhex(data).decode('utf-8')
        else:
            parsed = data

        if to_format == "json":
            result = json.dumps(parsed, indent=2, ensure_ascii=False)
        elif to_format == "base64":
            text = parsed if isinstance(parsed, str) else json.dumps(parsed)
            result = base64.b64encode(text.encode('utf-8')).decode('utf-8')
        elif to_format == "hex":
            text = parsed if isinstance(parsed, str) else json.dumps(parsed)
            result = text.encode('utf-8').hex()
        else:
            result = str(parsed)

        return {
            "success": True,
            "from_format": from_format,
            "to_format": to_format,
            "result": result
        }
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Server status tool
@mcp.resource("status://server")
def get_server_status() -> str:
    cfg = get_settings()
    return f"""
MCP Server Status
=================
Name: {cfg.server_name}
Status: Running
Debug: {cfg.debug}
Timestamp: {datetime.now(timezone.utc).isoformat()}

Configuration:
- HTTP Timeout: {cfg.http_timeout}s
- Max Text Length: {cfg.max_text_length}
- Max URL Content: {cfg.max_url_content}
- Fetch Enabled: {cfg.enable_fetch_tool}
- Allowed Domains: {cfg.allowed_fetch_domains or 'All'}

Available Tools: calculate, get_datetime, process_text, fetch_url, convert_data
"""


# Entry point
def main():
    cfg = get_settings()
    
    if "--sse" in sys.argv or "--http" in sys.argv:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route

        sse = SseServerTransport("/messages/")

        async def handle_post(request):
            return await sse.handle_post_message(request.scope, request.receive, request._send)

        async def handle_sse(request):
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await mcp._mcp_server.run(
                    streams[0], streams[1], mcp._mcp_server.create_initialization_options()
                )

        app = Starlette(
            debug=cfg.debug,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Route("/messages/", endpoint=handle_post, methods=["POST"]),
            ],
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["GET", "POST", "OPTIONS"],
                    allow_headers=["*"],
                )
            ]
        )

        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else cfg.port
        logger.info(f"Starting SSE server on {cfg.host}:{port}")
        uvicorn.run(app, host=cfg.host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()