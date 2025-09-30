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

"""User Management section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class UserManagementSection:
    """User Management section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the User Management section.

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
        """Register all user management-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(
            self.get_users,
            name="get_users",
            description="Get list of all users with access to the server",
        )
        self.mcp.tool(
            self.get_user_info,
            name="get_user_info",
            description="Get detailed information about a specific user",
        )
        self.mcp.tool(
            self.get_user_permissions,
            name="get_user_permissions",
            description="Get permissions for a specific user",
        )
        self.mcp.tool(
            self.get_user_activity,
            name="get_user_activity",
            description="Get recent activity for a specific user",
        )
        self.mcp.tool(
            self.get_user_watch_history,
            name="get_user_watch_history",
            description="Get watch history for a specific user",
        )
        self.mcp.tool(
            self.get_user_recommendations,
            name="get_user_recommendations",
            description="Get content recommendations for a specific user",
        )
        self.mcp.tool(
            self.get_user_libraries,
            name="get_user_libraries",
            description="Get accessible libraries for a specific user",
        )
        self.mcp.tool(
            self.get_user_settings,
            name="get_user_settings",
            description="Get user-specific settings and preferences",
        )

    def get_users(self) -> dict[str, Any]:
        """
        Get list of all users with access to the server.

        Returns
        -------
        dict[str, Any]
            Dictionary containing list of users
        """
        try:
            server = self.plex_client.get_server()

            # Get server info to check if it's a managed server
            server_info = server.myPlexAccount()

            if not server_info:
                return {
                    "success": False,
                    "error": "Server is not connected to Plex account or user management not available",
                }

            # Get users from Plex account
            users = server_info.users()

            results = [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": getattr(user, "email", None),
                    "title": getattr(user, "title", None),
                    "thumb": getattr(user, "thumb", None),
                    "restricted": getattr(user, "restricted", False),
                    "admin": getattr(user, "admin", False),
                    "guest": getattr(user, "guest", False),
                    "home": getattr(user, "home", False),
                    "protected": getattr(user, "protected", False),
                }
                for user in users
            ]

            result = {
                "success": True,
                "total_users": len(results),
                "users": results,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting users: %s")
            return {"success": False, "error": f"Error getting users: {e}"}
        else:
            return result

    def get_user_info(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed user information
        """
        try:
            server = self.plex_client.get_server()
            server_info = server.myPlexAccount()

            if not server_info:
                return {
                    "success": False,
                    "error": "Server is not connected to Plex account",
                }

            # Get specific user
            user = server_info.user(user_id)

            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found",
                }

            result = {
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": getattr(user, "email", None),
                    "title": getattr(user, "title", None),
                    "thumb": getattr(user, "thumb", None),
                    "restricted": getattr(user, "restricted", False),
                    "admin": getattr(user, "admin", False),
                    "guest": getattr(user, "guest", False),
                    "home": getattr(user, "home", False),
                    "protected": getattr(user, "protected", False),
                    "created_at": getattr(user, "createdAt", None),
                    "last_seen": getattr(user, "lastSeenAt", None),
                },
            }

        except NotFound as e:
            logger.exception("User not found: %s")
            return {"success": False, "error": f"User not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user info: %s")
            return {"success": False, "error": f"Error getting user info: {e}"}
        else:
            return result

    def get_user_permissions(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Get permissions for a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user

        Returns
        -------
        dict[str, Any]
            Dictionary containing user permissions
        """
        try:
            server = self.plex_client.get_server()
            server_info = server.myPlexAccount()

            if not server_info:
                return {
                    "success": False,
                    "error": "Server is not connected to Plex account",
                }

            user = server_info.user(user_id)

            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found",
                }

            # Get user's server access
            server_access = user.server(user.machineIdentifier)

            result = {
                "success": True,
                "user_id": user_id,
                "permissions": {
                    "admin": getattr(user, "admin", False),
                    "restricted": getattr(user, "restricted", False),
                    "home": getattr(user, "home", False),
                    "guest": getattr(user, "guest", False),
                    "protected": getattr(user, "protected", False),
                    "server_access": {
                        "all_libraries": getattr(server_access, "allLibraries", True),
                        "libraries": getattr(server_access, "libraries", []),
                        "allow_sync": getattr(server_access, "allowSync", False),
                        "allow_camera_upload": getattr(
                            server_access, "allowCameraUpload", False
                        ),
                        "allow_channel_access": getattr(
                            server_access, "allowChannelAccess", False
                        ),
                        "allow_media_deletion": getattr(
                            server_access, "allowMediaDeletion", False
                        ),
                        "allow_sharing": getattr(server_access, "allowSharing", False),
                    },
                },
            }

        except NotFound as e:
            logger.exception("User not found: %s")
            return {"success": False, "error": f"User not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user permissions: %s")
            return {"success": False, "error": f"Error getting user permissions: {e}"}
        else:
            return result

    def get_user_activity(
        self,
        user_id: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get recent activity for a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user
        limit : int, default=20
            Maximum number of activities to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing user activity
        """
        try:
            server = self.plex_client.get_server()

            # Get sessions (active users)
            sessions = server.sessions()

            # Filter sessions for specific user
            user_sessions = [
                session
                for session in sessions
                if getattr(session, "userID", None) == user_id
            ]

            activities = [
                {
                    "session_id": getattr(session, "sessionKey", None),
                    "client": getattr(session, "player", {}).get("title", "Unknown"),
                    "state": getattr(session, "state", None),
                    "media_title": getattr(session, "title", None),
                    "media_type": getattr(session, "type", None),
                    "progress": getattr(session, "viewOffset", 0),
                    "duration": getattr(session, "duration", 0),
                    "started_at": getattr(session, "viewOffset", None),
                }
                for session in user_sessions[:limit]
            ]

            result = {
                "success": True,
                "user_id": user_id,
                "total_activities": len(activities),
                "activities": activities,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user activity: %s")
            return {"success": False, "error": f"Error getting user activity: {e}"}
        else:
            return result

    def get_user_watch_history(
        self,
        user_id: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get watch history for a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user
        limit : int, default=50
            Maximum number of history items to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing user watch history
        """
        try:
            server = self.plex_client.get_server()

            # Get watch history
            history = server.history(limit=limit)

            # Filter history for specific user
            user_history = [
                item for item in history if getattr(item, "userID", None) == user_id
            ]

            history_items = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "type": getattr(item, "type", None),
                    "viewed_at": getattr(item, "viewedAt", None),
                    "duration": getattr(item, "duration", None),
                    "view_offset": getattr(item, "viewOffset", None),
                    "library_section": getattr(item, "librarySectionTitle", None),
                }
                for item in user_history
            ]

            result = {
                "success": True,
                "user_id": user_id,
                "total_items": len(history_items),
                "history": history_items,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user watch history: %s")
            return {"success": False, "error": f"Error getting user watch history: {e}"}
        else:
            return result

    def get_user_recommendations(
        self,
        user_id: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get content recommendations for a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user
        limit : int, default=20
            Maximum number of recommendations to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing user recommendations
        """
        try:
            server = self.plex_client.get_server()

            # Get recommendations (this is a simplified implementation)
            # In a real implementation, you might need to use Plex's recommendation API
            recommendations = server.recommendations(limit=limit)

            rec_items = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "summary": getattr(item, "summary", None),
                    "type": getattr(item, "type", None),
                    "year": getattr(item, "year", None),
                    "library_section": getattr(item, "librarySectionTitle", None),
                }
                for item in recommendations
            ]

            result = {
                "success": True,
                "user_id": user_id,
                "total_recommendations": len(rec_items),
                "recommendations": rec_items,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user recommendations: %s")
            return {
                "success": False,
                "error": f"Error getting user recommendations: {e}",
            }
        else:
            return result

    def get_user_libraries(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Get accessible libraries for a specific user.

        Parameters
        ----------
        user_id : str
            The ID of the user

        Returns
        -------
        dict[str, Any]
            Dictionary containing user's accessible libraries
        """
        try:
            server = self.plex_client.get_server()
            server_info = server.myPlexAccount()

            if not server_info:
                return {
                    "success": False,
                    "error": "Server is not connected to Plex account",
                }

            user = server_info.user(user_id)

            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found",
                }

            # Get user's server access
            server_access = user.server(user.machineIdentifier)

            # Get all libraries
            all_libraries = server.library.sections()

            # Filter based on user permissions
            accessible_libraries = []
            if getattr(server_access, "allLibraries", True):
                accessible_libraries = [
                    {
                        "title": lib.title,
                        "type": lib.TYPE,
                        "key": lib.key,
                        "agent": getattr(lib, "agent", None),
                    }
                    for lib in all_libraries
                ]
            else:
                allowed_library_ids = getattr(server_access, "libraries", [])
                accessible_libraries = [
                    {
                        "title": lib.title,
                        "type": lib.TYPE,
                        "key": lib.key,
                        "agent": getattr(lib, "agent", None),
                    }
                    for lib in all_libraries
                    if lib.key in allowed_library_ids
                ]

            result = {
                "success": True,
                "user_id": user_id,
                "all_libraries": getattr(server_access, "allLibraries", True),
                "total_libraries": len(accessible_libraries),
                "libraries": accessible_libraries,
            }

        except NotFound as e:
            logger.exception("User not found: %s")
            return {"success": False, "error": f"User not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user libraries: %s")
            return {"success": False, "error": f"Error getting user libraries: {e}"}
        else:
            return result

    def get_user_settings(
        self,
        user_id: str,
    ) -> dict[str, Any]:
        """
        Get user-specific settings and preferences.

        Parameters
        ----------
        user_id : str
            The ID of the user

        Returns
        -------
        dict[str, Any]
            Dictionary containing user settings
        """
        try:
            server = self.plex_client.get_server()
            server_info = server.myPlexAccount()

            if not server_info:
                return {
                    "success": False,
                    "error": "Server is not connected to Plex account",
                }

            user = server_info.user(user_id)

            if not user:
                return {
                    "success": False,
                    "error": f"User with ID {user_id} not found",
                }

            # Get user's server access for settings
            server_access = user.server(user.machineIdentifier)

            result = {
                "success": True,
                "user_id": user_id,
                "settings": {
                    "admin": getattr(user, "admin", False),
                    "restricted": getattr(user, "restricted", False),
                    "home": getattr(user, "home", False),
                    "guest": getattr(user, "guest", False),
                    "protected": getattr(user, "protected", False),
                    "server_permissions": {
                        "allow_sync": getattr(server_access, "allowSync", False),
                        "allow_camera_upload": getattr(
                            server_access, "allowCameraUpload", False
                        ),
                        "allow_channel_access": getattr(
                            server_access, "allowChannelAccess", False
                        ),
                        "allow_media_deletion": getattr(
                            server_access, "allowMediaDeletion", False
                        ),
                        "allow_sharing": getattr(server_access, "allowSharing", False),
                    },
                    "library_access": {
                        "all_libraries": getattr(server_access, "allLibraries", True),
                        "libraries": getattr(server_access, "libraries", []),
                    },
                },
            }

        except NotFound as e:
            logger.exception("User not found: %s")
            return {"success": False, "error": f"User not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting user settings: %s")
            return {"success": False, "error": f"Error getting user settings: {e}"}
        else:
            return result
