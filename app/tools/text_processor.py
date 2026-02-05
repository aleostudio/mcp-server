from app.mcp import mcp
from app.core import settings
from typing import Any
import re
import json

def _word_count(text: str) -> dict:
    return {"count": len(text.split())}


def _char_count(text: str) -> dict:
    return {"count": len(text), "count_no_spaces": len(text.replace(" ", ""))}


def _reverse(text: str) -> dict:
    return {"result": text[::-1]}


def _uppercase(text: str) -> dict:
    return {"result": text.upper()}


def _lowercase(text: str) -> dict:
    return {"result": text.lower()}


def _title_case(text: str) -> dict:
    return {"result": text.title()}


def _extract_emails(text: str) -> dict:
    return {"emails": re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)}


def _extract_urls(text: str) -> dict:
    return {"urls": re.findall(r'https?://[^\s]+', text)}


def _summarize_stats(text: str) -> dict:
    words = text.split()
    return {
        "total_chars": len(text),
        "total_words": len(words),
        "total_lines": len(text.splitlines()),
        "avg_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 2),
    }


OPERATIONS = {
    "word_count": _word_count,
    "char_count": _char_count,
    "reverse": _reverse,
    "uppercase": _uppercase,
    "lowercase": _lowercase,
    "title_case": _title_case,
    "extract_emails": _extract_emails,
    "extract_urls": _extract_urls,
    "summarize_stats": _summarize_stats,
}


def _normalize_options(options: Any) -> dict:
    if not options or options == "":
        return {}
    if isinstance(options, str):
        try:
            return json.loads(options)
        except json.JSONDecodeError:
            return {}
    if isinstance(options, dict):
        return options
    return {}


@mcp.tool()
def process_text(text: str, operation: str, options: dict[str, Any] | str | None = None) -> dict[str, Any]:
    """
    Handle text with various operations.

    Args:
        text: text to handle
        operation: action to perform (word_count, char_count, reverse, uppercase, 
                   lowercase, title_case, extract_emails, extract_urls, summarize_stats)
        options: additional options for specific operations

    Returns:
        Text process result
    """
    if len(text) > settings.max_text_length:
        return {"success": False, "error": f"Text too long. Max {settings.max_text_length} chars"}

    if operation not in OPERATIONS:
        return {"success": False, "error": f"Operation not supported. Use: {list(OPERATIONS.keys())}"}

    _ = _normalize_options(options)

    try:
        result = OPERATIONS[operation](text)
        return {"success": True, "operation": operation, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}
