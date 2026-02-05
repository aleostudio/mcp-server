from app.mcp import mcp
from app.core import settings
from datetime import datetime, timezone

@mcp.resource("status://server")
def get_server_status() -> str:
    """Return MCP server status."""
    
    tools = ["calculate", "get_datetime", "process_text", "fetch_url", "convert_data"]
    
    return f"""MCP Server Status
=================
Name: {settings.server_name}
Status: Running
Debug: {settings.debug}
Timestamp: {datetime.now(timezone.utc).isoformat()}

Configuration:
- HTTP Timeout: {settings.http_timeout}s
- Max Text Length: {settings.max_text_length}
- Max URL Content: {settings.max_url_content}
- Fetch Enabled: {settings.enable_fetch_tool}
- Allowed Domains: {settings.allowed_fetch_domains or 'All'}

Available Tools: {', '.join(tools)}
"""
