import json
import base64
from typing import Any, Protocol

class Codec(Protocol):    
    def decode(self, data: str) -> str | dict | list:
        ...

    def encode(self, data: str | dict | list) -> str:
        ...


class JsonCodec:    
    def decode(self, data: str) -> dict | list:
        return json.loads(data)

    def encode(self, data: str | dict | list) -> str:
        return json.dumps(data, indent=2, ensure_ascii=False)


class Base64Codec:
    def decode(self, data: str) -> str:
        return base64.b64decode(data).decode('utf-8')

    def encode(self, data: str | dict | list) -> str:
        text = data if isinstance(data, str) else json.dumps(data)
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')


class HexCodec:    
    def decode(self, data: str) -> str:
        return bytes.fromhex(data).decode('utf-8')

    def encode(self, data: str | dict | list) -> str:
        text = data if isinstance(data, str) else json.dumps(data)
        return text.encode('utf-8').hex()


CODECS: dict[str, Codec] = {
    "json": JsonCodec(),
    "base64": Base64Codec(),
    "hex": HexCodec(),
}


# Import here to avoid circular import
from app.mcp import mcp

@mcp.tool()
def convert_data(data: str, from_format: str, to_format: str) -> dict[str, Any]:
    """
    Convert data between formats.

    Args:
        data: data to convert
        from_format: source format (json, base64, hex)
        to_format: destination format (json, base64, hex)

    Returns:
        Converted data
    """
    if from_format not in CODECS or to_format not in CODECS:
        return {"success": False, "error": f"Supported formats: {list(CODECS.keys())}"}

    try:
        parsed = CODECS[from_format].decode(data)
        result = CODECS[to_format].encode(parsed)

        return {
            "success": True,
            "from_format": from_format,
            "to_format": to_format,
            "result": result
        }

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}
    except ValueError as e:
        return {"success": False, "error": f"Decode error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
