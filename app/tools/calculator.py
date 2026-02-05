from app.mcp import mcp
from typing import Any

OPERATIONS = {
    "add": lambda x, y: x + y,
    "subtract": lambda x, y: x - y,
    "multiply": lambda x, y: x * y,
    "divide": lambda x, y: x / y if y != 0 else None,
    "power": lambda x, y: x ** y,
}

@mcp.tool()
def calculate(operation: str, a: float, b: float) -> dict[str, Any]:
    """
    Execute basic math operation.

    Args:
        operation: operation to execute (add, subtract, multiply, divide, power)
        a: first operand
        b: second operand

    Returns:
        Operation result with details
    """
    if operation not in OPERATIONS:
        return {
            "success": False,
            "error": f"Operation '{operation}' not supported. Use: {list(OPERATIONS.keys())}"
        }

    if operation == "divide" and b == 0:
        return {"success": False, "error": "Division by zero not allowed"}

    result = OPERATIONS[operation](a, b)
    
    return {
        "success": True,
        "operation": operation,
        "operands": {"a": a, "b": b},
        "result": result
    }
