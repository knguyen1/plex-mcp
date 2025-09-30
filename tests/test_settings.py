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

"""Tests for SettingsSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.settings import SettingsSection


class TestSettingsSection:
    """Test cases for SettingsSection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test SettingsSection initialization."""
        section = SettingsSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 8

    def test_get_server_settings_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_settings: list[MagicMock],
    ) -> None:
        """Test successful server settings retrieval."""
        mock_server = MagicMock()
        mock_server.settings.all.return_value = mock_settings
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_server_settings()

        assert result["success"] is True
        assert result["total_settings"] == 2
        assert "settings" in result
        assert "setting1" in result["settings"]
        assert "setting2" in result["settings"]
        assert result["settings"]["setting1"]["id"] == "setting1"
        assert result["settings"]["setting1"]["label"] == "Setting 1"
        assert result["settings"]["setting1"]["value"] == "value1"

    def test_get_server_settings_bad_request(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test server settings retrieval with bad request error."""
        mock_server = MagicMock()
        mock_server.settings.all.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_server_settings()

        assert result["success"] is False
        assert "Error getting server settings" in result["error"]

    def test_get_server_settings_value_error(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test server settings retrieval with value error."""
        mock_server = MagicMock()
        mock_server.settings.all.side_effect = ValueError("Invalid value")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_server_settings()

        assert result["success"] is False
        assert "Error getting server settings" in result["error"]

    def test_get_setting_success(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_setting: MagicMock
    ) -> None:
        """Test successful setting retrieval."""
        mock_server = MagicMock()
        mock_server.settings.get.return_value = mock_setting
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_setting("test_setting")

        assert result["success"] is True
        assert "setting" in result
        assert result["setting"]["id"] == "test_setting"
        assert result["setting"]["label"] == "Test Setting"
        assert result["setting"]["value"] == "test_value"
        assert result["setting"]["default"] == "default_value"
        assert result["setting"]["type"] == "string"
        assert result["setting"]["hidden"] is False
        assert result["setting"]["advanced"] is False

    def test_get_setting_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test setting retrieval when setting not found."""
        mock_server = MagicMock()
        mock_server.settings.get.side_effect = NotFound("Setting not found")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_setting("nonexistent_setting")

        assert result["success"] is False
        assert "Setting 'nonexistent_setting' not found" in result["error"]

    def test_get_setting_bad_request(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test setting retrieval with bad request error."""
        mock_server = MagicMock()
        mock_server.settings.get.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_setting("test_setting")

        assert result["success"] is False
        assert "Error getting setting" in result["error"]

    @pytest.mark.parametrize(
        ("setting_id", "value", "value_type"),
        [
            ("string_setting", "new_value", str),
            ("int_setting", 42, int),
            ("bool_setting", True, bool),
        ],
    )
    def test_set_setting_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_setting: MagicMock,
        setting_id: str,
        value: str | int | bool,
        value_type: type,
    ) -> None:
        """Test successful setting update."""
        mock_setting.value = "old_value"
        mock_server = MagicMock()
        mock_server.settings.get.return_value = mock_setting
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.set_setting(setting_id, value)

        assert result["success"] is True
        assert (
            f"Updated setting '{setting_id}' from 'old_value' to '{value}'"
            in result["message"]
        )
        assert result["setting_id"] == setting_id
        assert result["old_value"] == "old_value"
        assert result["new_value"] == value
        mock_setting.set.assert_called_once_with(value)
        mock_server.settings.save.assert_called_once()

    def test_set_setting_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test setting update when setting not found."""
        mock_server = MagicMock()
        mock_server.settings.get.side_effect = NotFound("Setting not found")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.set_setting("nonexistent_setting", "new_value")

        assert result["success"] is False
        assert "Setting 'nonexistent_setting' not found" in result["error"]

    def test_set_setting_bad_request(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test setting update with bad request error."""
        mock_server = MagicMock()
        mock_server.settings.get.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.set_setting("test_setting", "new_value")

        assert result["success"] is False
        assert "Error setting setting" in result["error"]

    def test_get_library_sections_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_sections: list[MagicMock],
    ) -> None:
        """Test successful library sections retrieval."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = mock_library_sections
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_library_sections()

        assert result["success"] is True
        assert result["total_sections"] == 3
        assert len(result["sections"]) == 3
        assert result["sections"][0]["title"] == "Movies"
        assert result["sections"][0]["type"] == "movie"
        assert result["sections"][1]["title"] == "Music"
        assert result["sections"][1]["type"] == "artist"
        assert result["sections"][2]["title"] == "TV Shows"
        assert result["sections"][2]["type"] == "show"

    def test_get_library_sections_bad_request(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test library sections retrieval with bad request error."""
        mock_server = MagicMock()
        mock_server.library.sections.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_library_sections()

        assert result["success"] is False
        assert "Error getting library sections" in result["error"]

    def test_scan_library_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test successful library scan."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.scan_library("Movies")

        assert result["success"] is True
        assert "Started scan for library section 'Movies'" in result["message"]
        assert result["section_title"] == "Movies"
        assert result["section_type"] == "movie"
        mock_library_section.update.assert_called_once()

    def test_scan_library_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test library scan when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.scan_library("Nonexistent Section")

        assert result["success"] is False
        assert "Library section 'Nonexistent Section' not found" in result["error"]

    def test_scan_library_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test library scan with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        mock_library_section.update.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.scan_library("Movies")

        assert result["success"] is False
        assert "Error scanning library" in result["error"]

    def test_empty_trash_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test successful trash emptying."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.empty_trash("Movies")

        assert result["success"] is True
        assert "Emptied trash for library section 'Movies'" in result["message"]
        assert result["section_title"] == "Movies"
        assert result["section_type"] == "movie"
        mock_library_section.emptyTrash.assert_called_once()

    def test_empty_trash_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test trash emptying when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.empty_trash("Nonexistent Section")

        assert result["success"] is False
        assert "Library section 'Nonexistent Section' not found" in result["error"]

    def test_empty_trash_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test trash emptying with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        mock_library_section.emptyTrash.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.empty_trash("Movies")

        assert result["success"] is False
        assert "Error emptying trash" in result["error"]

    def test_analyze_library_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test successful library analysis."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.analyze_library("Movies")

        assert result["success"] is True
        assert "Started analysis for library section 'Movies'" in result["message"]
        assert result["section_title"] == "Movies"
        assert result["section_type"] == "movie"
        mock_library_section.analyze.assert_called_once()

    def test_analyze_library_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test library analysis when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.analyze_library("Nonexistent Section")

        assert result["success"] is False
        assert "Library section 'Nonexistent Section' not found" in result["error"]

    def test_analyze_library_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_library_section: MagicMock,
    ) -> None:
        """Test library analysis with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_library_section
        mock_library_section.analyze.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.analyze_library("Movies")

        assert result["success"] is False
        assert "Error analyzing library" in result["error"]

    def test_get_server_info_success(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_server_info: dict
    ) -> None:
        """Test successful server info retrieval."""
        mock_server = MagicMock()
        # Set server attributes
        for key, value in mock_server_info.items():
            setattr(mock_server, key, value)
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_server_info()

        assert result["success"] is True
        assert "server_info" in result
        server_info = result["server_info"]
        assert server_info["friendly_name"] == "Test Server"
        assert server_info["machine_identifier"] == "test-machine-id"
        assert server_info["version"] == "1.32.0"
        assert server_info["platform"] == "Linux"
        assert server_info["myplex"] is True
        assert server_info["allow_sync"] is True
        assert server_info["transcoder_active_video_sessions"] == 0

    def test_setting_attributes_handling(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test that setting attributes are handled correctly when missing."""
        # Create a setting with minimal attributes
        minimal_setting = MagicMock()
        minimal_setting.id = "minimal_setting"
        minimal_setting.value = "minimal_value"
        # Explicitly set label, summary, default, type, etc. to None/False
        minimal_setting.label = None
        minimal_setting.summary = None
        minimal_setting.default = None
        minimal_setting.type = None
        minimal_setting.hidden = False
        minimal_setting.advanced = False

        mock_server = MagicMock()
        mock_server.settings.get.return_value = minimal_setting
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_setting("minimal_setting")

        assert result["success"] is True
        setting_info = result["setting"]
        assert setting_info["id"] == "minimal_setting"
        assert setting_info["value"] == "minimal_value"
        assert setting_info["label"] is None
        assert setting_info["summary"] is None
        assert setting_info["default"] is None
        assert setting_info["type"] is None
        assert setting_info["hidden"] is False
        assert setting_info["advanced"] is False

    def test_library_section_attributes_handling(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test that library section attributes are handled correctly when missing."""
        # Create a section with minimal attributes
        minimal_section = MagicMock()
        minimal_section.title = "Minimal Section"
        minimal_section.TYPE = "movie"
        minimal_section.key = "1"
        # Explicitly set refreshing, agent, scanner, etc. to None/False
        minimal_section.refreshing = False
        minimal_section.agent = None
        minimal_section.scanner = None
        minimal_section.language = None
        minimal_section.location = None

        mock_server = MagicMock()
        mock_server.library.sections.return_value = [minimal_section]
        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_library_sections()

        assert result["success"] is True
        section_info = result["sections"][0]
        assert section_info["title"] == "Minimal Section"
        assert section_info["type"] == "movie"
        assert section_info["key"] == "1"
        assert section_info["refreshing"] is False
        assert section_info["agent"] is None
        assert section_info["scanner"] is None
        assert section_info["language"] is None
        assert section_info["location"] is None

    def test_server_info_attributes_handling(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test that server info attributes are handled correctly when missing."""
        # Create a server with minimal attributes
        mock_server = MagicMock()
        # Set only basic attributes
        mock_server.friendlyName = "Minimal Server"
        mock_server.machineIdentifier = "minimal-id"
        mock_server.version = "1.0.0"
        # Explicitly set other attributes to None/False
        mock_server.platform = None
        mock_server.platformVersion = None
        mock_server.myPlex = False
        mock_server.myPlexUsername = None
        mock_server.allowSync = False
        mock_server.allowCameraUpload = False
        mock_server.allowChannelAccess = False
        mock_server.allowMediaDeletion = False
        mock_server.allowSharing = False
        mock_server.multiuser = False
        mock_server.transcoderActiveVideoSessions = 0
        mock_server.transcoderVideo = False
        mock_server.transcoderAudio = False
        mock_server.transcoderPhoto = False
        mock_server.transcoderSubtitles = False
        mock_server.transcoderLyrics = False
        mock_server.updatedAt = None

        plex_client._server = mock_server

        section = SettingsSection(mock_fastmcp, plex_client)

        result = section.get_server_info()

        assert result["success"] is True
        server_info = result["server_info"]
        assert server_info["friendly_name"] == "Minimal Server"
        assert server_info["machine_identifier"] == "minimal-id"
        assert server_info["version"] == "1.0.0"
        assert server_info["platform"] is None
        assert server_info["platform_version"] is None
        assert server_info["myplex"] is False
        assert server_info["myplex_username"] is None
        assert server_info["allow_sync"] is False
        assert server_info["transcoder_active_video_sessions"] == 0
