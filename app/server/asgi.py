from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from mcp.server.sse import SseServerTransport
from app.core import settings, logger
from app.mcp import mcp

# CORS middleware
def _create_cors_middleware() -> Middleware:
    return Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )


# SSE connections handler
def _create_sse_handler(sse: SseServerTransport):
    async def handle_sse(request):
        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await mcp._mcp_server.run(
                    streams[0],
                    streams[1],
                    mcp._mcp_server.create_initialization_options()
                )
        except Exception as e:
            logger.debug(f"SSE connection closed: {e}")
    
    return handle_sse


# Message handler for /messages
async def _handle_messages(sse: SseServerTransport, scope, receive, send) -> None:
    try:
        await sse.handle_post_message(scope, receive, send)
    except Exception:
        pass


# Starlette handler
async def _handle_starlette(starlette_app: Starlette, scope, receive, send) -> None:
    try:
        await starlette_app(scope, receive, send)
    except TypeError as e:
        if "NoneType" not in str(e):
            raise
        logger.debug(f"Client disconnected: {e}")


# ASGI application with SSE support
def create_asgi_app():    
    sse = SseServerTransport("/messages/")
    
    starlette_app = Starlette(
        debug=settings.debug,
        routes=[Route("/sse", endpoint=_create_sse_handler(sse))],
        middleware=[_create_cors_middleware()]
    )

    async def app(scope, receive, send):
        is_messages_route = scope["type"] == "http" and scope["path"].startswith("/messages")
        if is_messages_route:
            await _handle_messages(sse, scope, receive, send)
        else:
            await _handle_starlette(starlette_app, scope, receive, send)

    return app
