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

"""Client Control section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class ClientControlSection:
    """Client Control section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Client Control section.

        Parameters
        ----------
        mcp : FastMCP
            The FastMCP instance to register tools with
        plex_client : PlexClient
            The Plex client for server interactions
        """
        self.mcp = mcp
        self.plex_client = plex_client
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all client control-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(self.list_clients)
        self.mcp.tool(self.get_client_info)
        self.mcp.tool(self.play_media)
        self.mcp.tool(self.control_playback)
        self.mcp.tool(self.set_volume)
        self.mcp.tool(self.navigate_client)
        self.mcp.tool(self.get_playback_state)

    def list_clients(self) -> dict[str, Any]:
        """
        List all connected Plex clients.

        Returns
        -------
        dict[str, Any]
            Dictionary containing list of connected clients
        """
        try:
            server = self.plex_client.get_server()
            clients = server.clients()

            results = [
                {
                    "title": client.title,
                    "platform": getattr(client, "platform", None),
                    "product": getattr(client, "product", None),
                    "device_class": getattr(client, "deviceClass", None),
                    "machine_identifier": getattr(client, "machineIdentifier", None),
                    "protocol_capabilities": getattr(
                        client, "protocolCapabilities", []
                    ),
                    "address": getattr(client, "address", None),
                    "port": getattr(client, "port", None),
                }
                for client in clients
            ]
            result = {
                "success": True,
                "total_clients": len(results),
                "clients": results,
            }
        except (BadRequest, ValueError) as e:
            logger.exception("Error listing clients: %s")
            return {"success": False, "error": f"Error listing clients: {e}"}
        else:
            return result

    def get_client_info(
        self,
        client_title: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific client.

        Parameters
        ----------
        client_title : str
            The title/name of the client

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed client information
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }
            result = {
                "success": True,
                "client": {
                    "title": client.title,
                    "platform": getattr(client, "platform", None),
                    "product": getattr(client, "product", None),
                    "device_class": getattr(client, "deviceClass", None),
                    "machine_identifier": getattr(client, "machineIdentifier", None),
                    "protocol_capabilities": getattr(
                        client, "protocolCapabilities", []
                    ),
                    "address": getattr(client, "address", None),
                    "port": getattr(client, "port", None),
                    "version": getattr(client, "version", None),
                    "protocol_version": getattr(client, "protocolVersion", None),
                },
            }
        except NotFound as e:
            logger.exception("Client not found: %s")
            return {"success": False, "error": f"Client not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting client info: %s")
            return {"success": False, "error": f"Error getting client info: {e}"}
        else:
            return result

    def play_media(
        self,
        client_title: str,
        media_rating_key: str,
    ) -> dict[str, Any]:
        """
        Play media on a specific client.

        Parameters
        ----------
        client_title : str
            The title/name of the client
        media_rating_key : str
            The rating key of the media to play

        Returns
        -------
        dict[str, Any]
            Dictionary containing playback results
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }

            # Get the media item
            media_item = server.fetchItem(int(media_rating_key))
            if not media_item:
                return {
                    "success": False,
                    "error": f"Media with rating key {media_rating_key} not found",
                }

            # Play the media
            client.playMedia(media_item)
            result = {
                "success": True,
                "message": f"Playing {media_item.title} on {client.title}",
                "media_title": media_item.title,
                "client_title": client.title,
            }
        except NotFound as e:
            logger.exception("Client or media not found: %s")
            return {"success": False, "error": f"Client or media not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error playing media: %s")
            return {"success": False, "error": f"Error playing media: {e}"}
        else:
            return result

    def control_playback(
        self,
        client_title: str,
        action: str,
        seek_to: int | None = None,
    ) -> dict[str, Any]:
        """
        Control playback on a client.

        Parameters
        ----------
        client_title : str
            The title/name of the client
        action : str
            The action to perform (play, pause, stop, stepForward, stepBack, skipNext, skipPrevious)
        seek_to : int, optional
            Position in milliseconds to seek to (for seek action)

        Returns
        -------
        dict[str, Any]
            Dictionary containing control results
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }

            # Define playback actions mapping
            playback_actions = {
                "play": lambda: client.play(),
                "pause": lambda: client.pause(),
                "stop": lambda: client.stop(),
                "stepForward": lambda: client.stepForward(),
                "stepBack": lambda: client.stepBack(),
                "skipNext": lambda: client.skipNext(),
                "skipPrevious": lambda: client.skipPrevious(),
            }

            # Validate action
            if action not in playback_actions and action != "seek":
                valid_actions = [*list(playback_actions.keys()), "seek"]
                return {
                    "success": False,
                    "error": f"Invalid action '{action}'. Valid actions: {', '.join(valid_actions)}",
                }

            # Perform the action
            if action == "seek":
                if seek_to is None:
                    return {
                        "success": False,
                        "error": "seek_to parameter is required for seek action",
                    }
                client.seekTo(seek_to)
            else:
                playback_actions[action]()
            result = {
                "success": True,
                "message": f"Executed '{action}' on {client.title}",
                "action": action,
                "client_title": client.title,
            }
        except NotFound as e:
            logger.exception("Client not found: %s")
            return {"success": False, "error": f"Client not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error controlling playback: %s")
            return {"success": False, "error": f"Error controlling playback: {e}"}
        else:
            return result

    def set_volume(
        self,
        client_title: str,
        volume: int,
    ) -> dict[str, Any]:
        """
        Set volume on a client.

        Parameters
        ----------
        client_title : str
            The title/name of the client
        volume : int
            Volume level (0-100)

        Returns
        -------
        dict[str, Any]
            Dictionary containing volume setting results
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }

            # Validate volume
            if not 0 <= volume <= 100:
                return {
                    "success": False,
                    "error": "Volume must be between 0 and 100",
                }

            # Set volume
            client.setVolume(volume)
            result = {
                "success": True,
                "message": f"Set volume to {volume}% on {client.title}",
                "volume": volume,
                "client_title": client.title,
            }
        except NotFound as e:
            logger.exception("Client not found: %s")
            return {"success": False, "error": f"Client not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error setting volume: %s")
            return {"success": False, "error": f"Error setting volume: {e}"}
        else:
            return result

    def navigate_client(
        self,
        client_title: str,
        direction: str,
    ) -> dict[str, Any]:
        """
        Navigate client interface.

        Parameters
        ----------
        client_title : str
            The title/name of the client
        direction : str
            Navigation direction (up, down, left, right, select, back, home, menu)

        Returns
        -------
        dict[str, Any]
            Dictionary containing navigation results
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }

            # Define navigation actions mapping
            navigation_actions = {
                "up": lambda: client.moveUp(),
                "down": lambda: client.moveDown(),
                "left": lambda: client.moveLeft(),
                "right": lambda: client.moveRight(),
                "select": lambda: client.select(),
                "back": lambda: client.goBack(),
                "home": lambda: client.goToHome(),
                "menu": lambda: client.contextMenu(),
            }

            # Validate direction
            if direction not in navigation_actions:
                valid_directions = list(navigation_actions.keys())
                return {
                    "success": False,
                    "error": f"Invalid direction '{direction}'. Valid directions: {', '.join(valid_directions)}",
                }

            # Perform navigation
            navigation_actions[direction]()
            result = {
                "success": True,
                "message": f"Navigated '{direction}' on {client.title}",
                "direction": direction,
                "client_title": client.title,
            }
        except NotFound as e:
            logger.exception("Client not found: %s")
            return {"success": False, "error": f"Client not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error navigating client: %s")
            return {"success": False, "error": f"Error navigating client: {e}"}
        else:
            return result

    def get_playback_state(
        self,
        client_title: str,
    ) -> dict[str, Any]:
        """
        Get current playback state of a client.

        Parameters
        ----------
        client_title : str
            The title/name of the client

        Returns
        -------
        dict[str, Any]
            Dictionary containing playback state information
        """
        try:
            server = self.plex_client.get_server()
            client = server.client(client_title)

            if not client:
                return {
                    "success": False,
                    "error": f"Client '{client_title}' not found",
                }

            # Get timeline information
            timeline = client.timeline
            result = {
                "success": True,
                "client_title": client.title,
                "playback_state": {
                    "state": getattr(timeline, "state", "unknown"),
                    "time": getattr(timeline, "time", 0),
                    "duration": getattr(timeline, "duration", 0),
                    "volume": getattr(timeline, "volume", 0),
                    "muted": getattr(timeline, "muted", False),
                    "repeat": getattr(timeline, "repeat", 0),
                    "shuffle": getattr(timeline, "shuffle", 0),
                },
            }
        except NotFound as e:
            logger.exception("Client not found: %s")
            return {"success": False, "error": f"Client not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting playback state: %s")
            return {"success": False, "error": f"Error getting playback state: {e}"}
        else:
            return result
