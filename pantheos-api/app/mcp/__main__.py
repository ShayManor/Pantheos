"""Run the Pantheos MCP server: ``python -m app.mcp [stdio|http]``."""
import sys  # pragma: no cover

from .server import serve  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    arg = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    serve("streamable-http" if arg in ("http", "streamable-http") else "stdio")
