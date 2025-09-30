# Copyright (c) 2025 knguyen1
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Plex MCP Server."""

import asyncio
import logging
import sys
from importlib.metadata import PackageNotFoundError, version

import click
from fastmcp import FastMCP

from plex_mcp.client.plex_client import PlexClient
from plex_mcp.sections import (
    AdvancedSearchSection,
    ClientControlSection,
    CollectionsSection,
    MoviesSection,
    MusicSection,
    PhotoLibrarySection,
    SettingsSection,
    TVShowsSection,
    UserManagementSection,
)

try:
    __version__ = version("plex-mcp")
except PackageNotFoundError:
    # not installed via setuptools
    __version__ = "0.0.0"

logger = logging.getLogger(__name__)


@click.version_option(__version__, prog_name="plex-mcp")
@click.command()
@click.option("--baseurl", help="The base URL of the Plex server", required=True)
@click.option("--token", help="The token for the Plex server", required=True)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="Transport type (stdio, sse, or streamable-http)",
)
@click.option(
    "--port",
    default=8000,
    help="Port to listen on for SSE or Streamable HTTP transport",
)
@click.option(
    "--host",
    default="0.0.0.0",  # noqa: S104
    help="Host to bind to for SSE or Streamable HTTP transport (default: 0.0.0.0)",
)
@click.option(
    "--path",
    default="/mcp",
    help="Path for Streamable HTTP transport (e.g., /mcp).",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Increase verbosity (can be used multiple times)",
)
def main(
    baseurl: str,
    token: str,
    transport: str,
    port: int,
    host: str,
    path: str,
    verbose: int,
) -> None:
    """Run the Plex MCP server."""
    # Set up logging
    if verbose == 1:
        logging_level = logging.INFO
    elif verbose >= 2:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.WARNING

    logging.basicConfig(
        level=logging_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    logger.info("Running Plex MCP server on %s with token %s", baseurl, token)

    # Initialize Plex client
    plex_client = PlexClient(baseurl, token)

    # Create FastMCP server
    mcp = FastMCP("Plex MCP Server")

    # Register all section tools
    AdvancedSearchSection(mcp, plex_client)
    ClientControlSection(mcp, plex_client)
    CollectionsSection(mcp, plex_client)
    MusicSection(mcp, plex_client)
    MoviesSection(mcp, plex_client)
    PhotoLibrarySection(mcp, plex_client)
    SettingsSection(mcp, plex_client)
    TVShowsSection(mcp, plex_client)
    UserManagementSection(mcp, plex_client)

    # Prepare run arguments
    run_kwargs = {
        "transport": transport,
    }

    if transport == "stdio":
        logger.info("Starting server with STDIO transport.")
    elif transport in ["sse", "streamable-http"]:
        run_kwargs["host"] = host
        run_kwargs["port"] = port
        run_kwargs["log_level"] = logging.getLevelName(logging_level).lower()

        if path is not None:
            run_kwargs["path"] = path

        log_display_path = path
        if log_display_path is None:
            if transport == "sse":
                log_display_path = mcp.settings.sse_path or "/sse"
            else:
                log_display_path = mcp.settings.streamable_http_path or "/mcp"

        logger.info(
            "Starting server with %s transport on http://%s:%s%s",
            transport.upper(),
            host,
            port,
            log_display_path,
        )
    else:
        logger.error("Invalid transport type '%s'. Cannot start server.", transport)
        sys.exit(1)

    try:
        logger.debug("Starting asyncio event loop...")
        asyncio.run(mcp.run_async(**run_kwargs))
    except (KeyboardInterrupt, SystemExit) as e:
        logger.info("Server shutdown initiated: %s", type(e).__name__)
    except Exception:
        logger.exception("Server encountered an error")
        sys.exit(1)


__all__ = ["__version__", "main"]

if __name__ == "__main__":
    main()
