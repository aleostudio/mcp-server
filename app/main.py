from app.mcp import mcp
from app.core import settings, logger
from app.server.asgi import create_asgi_app
import sys
import uvicorn
import app.tools

# Run server in STDIO mode
def run_stdio() -> None:
    logger.info("Starting MCP server in STDIO mode")
    mcp.run()


# Run server in SSE mode
def run_sse(port: int | None = None) -> None:
    port = port or settings.port
    app = create_asgi_app()
    logger.info(f"Starting SSE server on {settings.host}:{port}")
    uvicorn.run(app, host=settings.host, port=port)


# Entrypoint
def main() -> None:
    if "--sse" in sys.argv or "--http" in sys.argv:
        port = None
        if "--port" in sys.argv:
            try:
                port = int(sys.argv[sys.argv.index("--port") + 1])
            except (IndexError, ValueError):
                pass
        
        run_sse(port)
    else:
        run_stdio()

if __name__ == "__main__":
    main()
