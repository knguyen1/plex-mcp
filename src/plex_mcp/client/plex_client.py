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

"""Plex MCP Server Plex Client."""

import logging
import os

from plexapi.server import PlexServer

logger = logging.getLogger(__name__)


class PlexClient:
    """
    Plex Client for interacting with Plex Media Server.

    This client provides a high-level interface for connecting to and
    interacting with a Plex Media Server instance. It handles authentication
    and provides access to the Plex server's library and media content.

    Parameters
    ----------
    baseurl : str
        The base URL of the Plex Media Server (e.g., 'http://localhost:32400')
    token : str
        The authentication token for the Plex Media Server

    Attributes
    ----------
    baseurl : str
        The base URL of the Plex Media Server
    token : str
        The authentication token for the Plex Media Server
    _server : PlexServer, optional
        The underlying PlexServer instance (lazy-loaded)

    Raises
    ------
    ValueError
        If baseurl or token are not provided and not available in environment
        variables PLEX_BASEURL and PLEX_TOKEN

    Examples
    --------
    >>> client = PlexClient(
    ...     "http://localhost:32400",
    ...     "your-token-here",
    ... )
    >>> server = client.get_server()
    >>> sections = server.library.sections()
    """

    def __init__(self, baseurl: str, token: str):
        """
        Initialize the Plex Client.

        Parameters
        ----------
        baseurl : str
            The base URL of the Plex Media Server. If None, will attempt to
            get from PLEX_BASEURL environment variable.
        token : str
            The authentication token for the Plex Media Server. If None, will
            attempt to get from PLEX_TOKEN environment variable.

        Raises
        ------
        ValueError
            If baseurl or token are not provided and not available in
            environment variables.
        """
        self.baseurl = baseurl or os.getenv("PLEX_BASEURL")
        self.token = token or os.getenv("PLEX_TOKEN")

        if not self.baseurl or not self.token:
            msg = "Base URL and token are required"
            raise ValueError(msg)

        self._server = None

    def get_server(self) -> PlexServer:
        """
        Get the Plex server instance.

        Returns a PlexServer instance, initializing it if not already done.
        The connection is validated by attempting to fetch library sections.

        Returns
        -------
        PlexServer
            The initialized and validated PlexServer instance

        Raises
        ------
        Exception
            If the Plex server connection fails or validation fails

        Notes
        -----
        This method uses lazy initialization - the PlexServer is only created
        when first requested. The connection is validated by attempting to
        fetch library sections.
        """
        if self._server is None:
            logger.info("Initializing PlexServer with URL: %s", self.baseurl)
            self._server = PlexServer(self.baseurl, self.token)
            logger.info("Successfully initialized PlexServer.")

            # Validate the connection
            self._server.library.sections()  # Attempt to fetch library sections
            logger.info("Plex server connection validated.")
        return self._server
