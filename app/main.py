from app.core import settings, logger
from app.mcp import mcp
from app.server.asgi import create_asgi_app
import sys
import uvicorn

# Entrypoint
def main() -> None:
    if "--sse" in sys.argv or "--http" in sys.argv:

        # Run server in SSE mode
        port = None
        if "--port" in sys.argv:
            try:
                port = int(sys.argv[sys.argv.index("--port") + 1])
            except (IndexError, ValueError):
                pass
        
        port = port or settings.port
        app = create_asgi_app()
        logger.info(f"Starting SSE server on {settings.host}:{port}")
        uvicorn.run(app, host=settings.host, port=port)

    else:
        # Run server in STDIO mode
        logger.info("Starting MCP server in STDIO mode")
        mcp.run()


# Entrypoint if invoked directly
if __name__ == "__main__":
    main()
