"""
Minimal local MCP client for ScholarAI.
"""
from mcp.server import mcp_server


class LocalMcpClient:
    async def call_tool(self, tool_name: str, **kwargs) -> dict:
        return await mcp_server.call_tool(tool_name, **kwargs)


mcp_client = LocalMcpClient()
