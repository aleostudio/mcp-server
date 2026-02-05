import logging
import sys
from app.core.config import settings

# Logger init
def setup_logging() -> logging.Logger:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
        force=True
    )

    logger = logging.getLogger("mcp-server")
    logger.setLevel(level)
    
    return logger


logger = setup_logging()
