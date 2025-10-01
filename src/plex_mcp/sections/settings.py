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

"""Settings section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class SettingsSection:
    """Settings section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Settings section.

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
        """Register all settings-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(self.get_server_settings)
        self.mcp.tool(self.get_setting)
        self.mcp.tool(self.set_setting)
        self.mcp.tool(self.get_library_sections)
        self.mcp.tool(self.scan_library)
        self.mcp.tool(self.empty_trash)
        self.mcp.tool(self.analyze_library)
        self.mcp.tool(self.get_server_info)

    def get_server_settings(self) -> dict[str, Any]:
        """
        Get all server settings.

        Returns
        -------
        dict[str, Any]
            Dictionary containing all server settings
        """
        try:
            server = self.plex_client.get_server()
            settings = server.settings

            # Get all settings
            all_settings = settings.all()

            settings_dict = {}
            for setting in all_settings:
                settings_dict[setting.id] = {
                    "id": setting.id,
                    "label": getattr(setting, "label", None),
                    "summary": getattr(setting, "summary", None),
                    "value": getattr(setting, "value", None),
                    "default": getattr(setting, "default", None),
                    "type": getattr(setting, "type", None),
                    "hidden": getattr(setting, "hidden", False),
                    "advanced": getattr(setting, "advanced", False),
                    "group": getattr(setting, "group", None),
                }

            result = {
                "success": True,
                "total_settings": len(settings_dict),
                "settings": settings_dict,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting server settings: %s")
            return {"success": False, "error": f"Error getting server settings: {e}"}
        else:
            return result

    def get_setting(
        self,
        setting_id: str,
    ) -> dict[str, Any]:
        """
        Get a specific server setting value.

        Parameters
        ----------
        setting_id : str
            The ID of the setting to get

        Returns
        -------
        dict[str, Any]
            Dictionary containing the setting information
        """
        try:
            server = self.plex_client.get_server()
            settings = server.settings

            setting = settings.get(setting_id)

            result = {
                "success": True,
                "setting": {
                    "id": setting.id,
                    "label": getattr(setting, "label", None),
                    "summary": getattr(setting, "summary", None),
                    "value": getattr(setting, "value", None),
                    "default": getattr(setting, "default", None),
                    "type": getattr(setting, "type", None),
                    "hidden": getattr(setting, "hidden", False),
                    "advanced": getattr(setting, "advanced", False),
                },
            }

        except NotFound as e:
            logger.exception("Setting not found: %s")
            return {"success": False, "error": f"Setting '{setting_id}' not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting setting: %s")
            return {"success": False, "error": f"Error getting setting: {e}"}
        else:
            return result

    def set_setting(
        self,
        setting_id: str,
        value: str | int | bool,
    ) -> dict[str, Any]:
        """
        Set a server setting value.

        Parameters
        ----------
        setting_id : str
            The ID of the setting to set
        value : str | int | bool
            The new value for the setting

        Returns
        -------
        dict[str, Any]
            Dictionary containing the setting update results
        """
        try:
            server = self.plex_client.get_server()
            settings = server.settings

            setting = settings.get(setting_id)
            old_value = getattr(setting, "value", None)
            setting.set(value)
            settings.save()
            result = {
                "success": True,
                "message": f"Updated setting '{setting_id}' from '{old_value}' to '{value}'",
                "setting_id": setting_id,
                "old_value": old_value,
                "new_value": value,
            }
        except NotFound as e:
            logger.exception("Setting not found: %s")
            return {"success": False, "error": f"Setting '{setting_id}' not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error setting setting: %s")
            return {"success": False, "error": f"Error setting setting: {e}"}
        else:
            return result

    def get_library_sections(self) -> dict[str, Any]:
        """
        Get all library sections and their settings.

        Returns
        -------
        dict[str, Any]
            Dictionary containing all library sections
        """
        try:
            server = self.plex_client.get_server()
            sections = server.library.sections()

            results = [
                {
                    "title": section.title,
                    "type": section.TYPE,
                    "key": section.key,
                    "refreshing": getattr(section, "refreshing", False),
                    "agent": getattr(section, "agent", None),
                    "scanner": getattr(section, "scanner", None),
                    "language": getattr(section, "language", None),
                    "location": getattr(section, "location", None),
                }
                for section in sections
            ]
            result = {
                "success": True,
                "total_sections": len(results),
                "sections": results,
            }
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting library sections: %s")
            return {"success": False, "error": f"Error getting library sections: {e}"}
        else:
            return result

    def scan_library(
        self,
        section_title: str,
    ) -> dict[str, Any]:
        """
        Scan a library section for new media.

        Parameters
        ----------
        section_title : str
            The title of the library section to scan

        Returns
        -------
        dict[str, Any]
            Dictionary containing scan results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Start the scan
            section.update()
            result = {
                "success": True,
                "message": f"Started scan for library section '{section_title}'",
                "section_title": section_title,
                "section_type": section.TYPE,
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {
                "success": False,
                "error": f"Library section '{section_title}' not found: {e}",
            }
        except (BadRequest, ValueError) as e:
            logger.exception("Error scanning library: %s")
            return {"success": False, "error": f"Error scanning library: {e}"}
        else:
            return result

    def empty_trash(
        self,
        section_title: str,
    ) -> dict[str, Any]:
        """
        Empty trash for a library section.

        Parameters
        ----------
        section_title : str
            The title of the library section

        Returns
        -------
        dict[str, Any]
            Dictionary containing trash emptying results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Empty trash
            section.emptyTrash()
            result = {
                "success": True,
                "message": f"Emptied trash for library section '{section_title}'",
                "section_title": section_title,
                "section_type": section.TYPE,
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {
                "success": False,
                "error": f"Library section '{section_title}' not found: {e}",
            }
        except (BadRequest, ValueError) as e:
            logger.exception("Error emptying trash: %s")
            return {"success": False, "error": f"Error emptying trash: {e}"}
        else:
            return result

    def analyze_library(
        self,
        section_title: str,
    ) -> dict[str, Any]:
        """
        Analyze library section for metadata.

        Parameters
        ----------
        section_title : str
            The title of the library section

        Returns
        -------
        dict[str, Any]
            Dictionary containing analysis results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Start analysis
            section.analyze()
            result = {
                "success": True,
                "message": f"Started analysis for library section '{section_title}'",
                "section_title": section_title,
                "section_type": section.TYPE,
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {
                "success": False,
                "error": f"Library section '{section_title}' not found: {e}",
            }
        except (BadRequest, ValueError) as e:
            logger.exception("Error analyzing library: %s")
            return {"success": False, "error": f"Error analyzing library: {e}"}
        else:
            return result

    def get_server_info(self) -> dict[str, Any]:
        """
        Get detailed server information.

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed server information
        """
        try:
            server = self.plex_client.get_server()

            result = {
                "success": True,
                "server_info": {
                    "friendly_name": server.friendlyName,
                    "machine_identifier": server.machineIdentifier,
                    "version": server.version,
                    "platform": getattr(server, "platform", None),
                    "platform_version": getattr(server, "platformVersion", None),
                    "myplex": getattr(server, "myPlex", False),
                    "myplex_username": getattr(server, "myPlexUsername", None),
                    "myplex_subscription": getattr(server, "myPlexSubscription", False),
                    "allow_sync": getattr(server, "allowSync", False),
                    "allow_camera_upload": getattr(server, "allowCameraUpload", False),
                    "allow_channel_access": getattr(
                        server, "allowChannelAccess", False
                    ),
                    "allow_media_deletion": getattr(
                        server, "allowMediaDeletion", False
                    ),
                    "allow_sharing": getattr(server, "allowSharing", False),
                    "multiuser": getattr(server, "multiuser", False),
                    "transcoder_active_video_sessions": getattr(
                        server, "transcoderActiveVideoSessions", 0
                    ),
                    "transcoder_video": getattr(server, "transcoderVideo", False),
                    "transcoder_audio": getattr(server, "transcoderAudio", False),
                    "transcoder_photo": getattr(server, "transcoderPhoto", False),
                    "transcoder_subtitles": getattr(
                        server, "transcoderSubtitles", False
                    ),
                    "transcoder_lyrics": getattr(server, "transcoderLyrics", False),
                    "updated_at": getattr(server, "updatedAt", None),
                },
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting server info: %s")
            return {"success": False, "error": f"Error getting server info: {e}"}
        else:
            return result
