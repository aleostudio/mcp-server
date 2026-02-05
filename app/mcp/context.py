from dataclasses import dataclass
from datetime import datetime
from app.core.config import Settings
import httpx

# Application context with shared resources
@dataclass
class AppContext:    
    http_client: httpx.AsyncClient
    startup_time: datetime
    settings: Settings
