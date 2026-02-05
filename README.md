# Simple MCP server with tools for AI agents

A fast and lightweight **MCP server** with different tools for AI agents. It supports STDIO (Claude Desktop) and SSE (remote agents).

## Index

- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Run server in STDIO mode](#run-server-in-stdio-mode)
- [Run server in SSE mode](#run-server-in-sse-mode)
- [Configure Claude Desktop](#configure-claude-desktop)
- [Available tools](#available-tools)
- [Debug in VSCode](#debug-in-vscode)

---

## Prerequisites

- Python >= 3.11
- uv and pip installed

[↑ index](#index)

---

## Configuration

Init **virtualenv** and install dependencies with:

```bash
uv venv
source .venv/bin/activate
uv sync
```

Create your ```.env``` file by copying:

```bash
cp env.dist .env
```

Then, customize it if needed.

[↑ index](#index)

---

## Run server in STDIO mode

First of all, to test the server, install and run a MCP inspector with:

```bash
npx @modelcontextprotocol/inspector uv run python server.py
```

At the end, a UI will open in your browser. Connect to the server by clicking **Connect** on the left menu.

Then, from the top bar, click on **Tools** and **List tools**. At this point you can choose you preferred tools and play with it.

If you want to test it without the inspector, simply launch with:

```bash
uv run python server.py
```

[↑ index](#index)

---

## Run server in SSE mode

If you want to use the server through **SSE** from remote agents, launch it with:

```bash
uv run python server.py --sse --port 8000
```

If you want to simulate a tool call from a remote agent, create a simple **STDIO client** in python (e.g. `stdio_test.py`) with this code:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    server_params = StdioServerParameters(command="uv", args=["run", "python", "server.py"], cwd="./")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Tools list
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])
            
            # Call calculate
            result = await session.call_tool("calculate", { "operation": "multiply", "a": 6, "b": 7 })
            print("Result:", result.content)

asyncio.run(test())
```

Then run with:

```bash
python3 stdio_test.py
```

You will see a the **available tools list** and the result of `calculate`.

[↑ index](#index)

---

## Configure Claude Desktop

If you want to use tools on **Claude Desktop**, create the file `claude_desktop_config.json` with this content:

```json
{
  "mcpServers": {
    "mcp-server-tools": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/mcp-server", "python", "server.py"]
    }
  }
}
```

Move this file in:

- macOS: `~/Library/Application Support/Claude`
- Windows: `%APPDATA%\Claude`

[↑ index](#index)

---

## Available tools

| Tool | Descrizione |
| :--- | :--- |
| `calculate` | Math operations (add, subtract, multiply, divide, power) |
| `get_datetime` | Date/hour with timezone and configurable format |
| `process_text` | Text handler (word count, extract email/URL, stats) |
| `fetch_url` | HTTP GET/HEAD requests |
| `convert_data` | JSON, Base64, Hex conversions |

[↑ index](#index)

---

### Debug in VSCode

To debug your Python microservice you need to:

- Install **VSCode**
- Ensure you have **Python extension** installed
- Ensure you have selected the **right interpreter with virtualenv** on VSCode
- Click on **Run and Debug** menu and **create a launch.json file**
- From dropdown, select **Python debugger** and **FastAPI**
- Change the ```.vscode/launch.json``` created in the project root with this (customizing host and port if changed):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "MCP Server (SSE)",
      "type": "debugpy",
      "request": "launch",
      "program": "server.py",
      "args": [
        "--sse"
      ],
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "justMyCode": true
    },
    {
      "name": "MCP Server (STDIO)",
      "type": "debugpy",
      "request": "launch",
      "program": "server.py",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "justMyCode": true
    }
  ]
}
```

- Put some breakpoint in the code, then press the **green play button**
- Call the API to debug

[↑ index](#index)

---

Made with ♥️ by Alessandro Orrù
