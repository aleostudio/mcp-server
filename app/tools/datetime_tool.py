from app.mcp import mcp
from datetime import datetime, timezone, timedelta
from typing import Any

FORMATS = {
    "iso": lambda dt: dt.isoformat(),
    "human": lambda dt: dt.strftime("%A, %d %B %Y - %H:%M:%S"),
    "unix": lambda dt: int(dt.timestamp()),
    "components": lambda dt: {
        "year": dt.year,
        "month": dt.month,
        "day": dt.day,
        "hour": dt.hour,
        "minute": dt.minute,
        "second": dt.second,
        "weekday": dt.strftime("%A"),
    }
}


@mcp.tool()
def get_datetime(timezone_offset: int = 0, format_type: str = "iso") -> dict[str, Any]:
    """
    Get current date/time with configurable format.

    Args:
        timezone_offset: UTC offset in hours (-12 to +14)
        format_type: output format (iso, human, unix, components)

    Returns:
        Date/time in the required format
    """
    if not -12 <= timezone_offset <= 14:
        return {"success": False, "error": "timezone_offset must be between -12 and +14"}

    if format_type not in FORMATS:
        return {"success": False, "error": f"format_type must be: {list(FORMATS.keys())}"}

    now = datetime.now(timezone.utc) + timedelta(hours=timezone_offset)

    return {
        "success": True,
        "timezone_offset": timezone_offset,
        "format": format_type,
        "datetime": FORMATS[format_type](now)
    }
