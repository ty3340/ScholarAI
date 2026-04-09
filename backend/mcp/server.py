"""
Minimal local MCP server for ScholarAI.

This keeps MCP simple: tools are registered in-process and can be shared by
multiple agents through a small client wrapper.
"""
from collections.abc import Awaitable, Callable


McpTool = Callable[..., Awaitable[dict]]


class LocalMcpServer:
    def __init__(self) -> None:
        self._tools: dict[str, McpTool] = {}

    def register_tool(self, name: str, tool: McpTool) -> None:
        self._tools[name] = tool

    async def call_tool(self, name: str, **kwargs) -> dict:
        if name not in self._tools:
            return {"status": "error", "message": f"MCP tool '{name}' is not registered."}
        return await self._tools[name](**kwargs)


mcp_server = LocalMcpServer()
