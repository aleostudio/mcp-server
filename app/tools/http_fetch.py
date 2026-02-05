from app.mcp import mcp
from app.core import settings
from mcp.server.fastmcp import Context
from typing import Any
from urllib.parse import urlparse
import httpx

ALLOWED_METHODS = {"GET", "HEAD"}


def _is_domain_allowed(url: str) -> bool:
    if not settings.allowed_fetch_domains:
        return True
    
    domain = urlparse(url).netloc
    return any(domain.endswith(allowed) for allowed in settings.allowed_fetch_domains)


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
    if not settings.enable_fetch_tool:
        return {"success": False, "error": "Tool fetch_url disabled"}

    method = method.upper()
    if method not in ALLOWED_METHODS:
        return {"success": False, "error": f"Only {ALLOWED_METHODS} are supported"}

    if not url.startswith(("http://", "https://")):
        return {"success": False, "error": "URL must start with http:// or https://"}

    if not _is_domain_allowed(url):
        return {"success": False, "error": f"Domain not allowed. Allowed: {settings.allowed_fetch_domains}"}

    client: httpx.AsyncClient | None = None
    should_close = False

    try:
        if ctx and hasattr(ctx, 'request_context') and ctx.request_context.lifespan_context:
            client = ctx.request_context.lifespan_context.http_client
        else:
            client = httpx.AsyncClient(timeout=settings.http_timeout)
            should_close = True

        response = await client.request(method, url)
        
        content = None
        content_length = None
        if method == "GET":
            content = response.text[:settings.max_url_content]
            content_length = len(response.text)

        return {
            "success": True,
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "content_preview": content,
            "content_length": content_length
        }

    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except httpx.RequestError as e:
        return {"success": False, "error": f"Request failed: {e}"}
    finally:
        if should_close and client:
            await client.aclose()
