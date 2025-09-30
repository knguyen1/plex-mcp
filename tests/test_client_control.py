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

"""Tests for ClientControlSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.client_control import ClientControlSection


class TestClientControlSection:
    """Test cases for ClientControlSection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test ClientControlSection initialization."""
        section = ClientControlSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 7

    def test_list_clients_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_clients: list[MagicMock],
    ) -> None:
        """Test successful client listing."""
        mock_server = MagicMock()
        mock_server.clients.return_value = mock_clients
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.list_clients()

        assert result["success"] is True
        assert result["total_clients"] == 2
        assert len(result["clients"]) == 2
        assert result["clients"][0]["title"] == "Test Client 1"
        assert result["clients"][1]["title"] == "Test Client 2"

    def test_list_clients_bad_request(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client listing with bad request error."""
        mock_server = MagicMock()
        mock_server.clients.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.list_clients()

        assert result["success"] is False
        assert "Error listing clients" in result["error"]

    def test_list_clients_value_error(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client listing with value error."""
        mock_server = MagicMock()
        mock_server.clients.side_effect = ValueError("Invalid value")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.list_clients()

        assert result["success"] is False
        assert "Error listing clients" in result["error"]

    def test_get_client_info_success(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test successful client info retrieval."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_client_info("Test Client")

        assert result["success"] is True
        assert "client" in result
        assert result["client"]["title"] == "Test Client"
        assert result["client"]["platform"] == "iOS"
        assert result["client"]["product"] == "Plex for iOS"

    def test_get_client_info_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client info when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_client_info("Nonexistent Client")

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_get_client_info_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client info with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_client_info("Test Client")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    def test_play_media_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        mock_media: MagicMock,
    ) -> None:
        """Test successful media playback."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        mock_server.fetchItem.return_value = mock_media
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.play_media("Test Client", "12345")

        assert result["success"] is True
        assert "Playing Test Media on Test Client" in result["message"]
        assert result["media_title"] == "Test Media"
        assert result["client_title"] == "Test Client"
        mock_client.playMedia.assert_called_once_with(mock_media)

    def test_play_media_client_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test media playback when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.play_media("Nonexistent Client", "12345")

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_play_media_media_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test media playback when media not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.play_media("Test Client", "99999")

        assert result["success"] is False
        assert "Media with rating key 99999 not found" in result["error"]

    def test_play_media_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test media playback with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.play_media("Test Client", "12345")

        assert result["success"] is False
        assert "Client or media not found" in result["error"]

    @pytest.mark.parametrize(
        ("action", "expected_method"),
        [
            ("play", "play"),
            ("pause", "pause"),
            ("stop", "stop"),
            ("stepForward", "stepForward"),
            ("stepBack", "stepBack"),
            ("skipNext", "skipNext"),
            ("skipPrevious", "skipPrevious"),
        ],
    )
    def test_control_playback_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        action: str,
        expected_method: str,
    ) -> None:
        """Test successful playback control."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Test Client", action)

        assert result["success"] is True
        assert f"Executed '{action}' on Test Client" in result["message"]
        assert result["action"] == action
        assert result["client_title"] == "Test Client"
        getattr(mock_client, expected_method).assert_called_once()

    def test_control_playback_seek_success(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test successful seek operation."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Test Client", "seek", seek_to=30000)

        assert result["success"] is True
        assert "Executed 'seek' on Test Client" in result["message"]
        mock_client.seekTo.assert_called_once_with(30000)

    def test_control_playback_seek_missing_parameter(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test seek operation without seek_to parameter."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Test Client", "seek")

        assert result["success"] is False
        assert "seek_to parameter is required for seek action" in result["error"]

    def test_control_playback_invalid_action(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test playback control with invalid action."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Test Client", "invalid_action")

        assert result["success"] is False
        assert "Invalid action 'invalid_action'" in result["error"]
        assert "Valid actions:" in result["error"]

    def test_control_playback_client_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test playback control when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Nonexistent Client", "play")

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_control_playback_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test playback control with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.control_playback("Test Client", "play")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @pytest.mark.parametrize("volume", [0, 25, 50, 75, 100])
    def test_set_volume_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        volume: int,
    ) -> None:
        """Test successful volume setting."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.set_volume("Test Client", volume)

        assert result["success"] is True
        assert f"Set volume to {volume}% on Test Client" in result["message"]
        assert result["volume"] == volume
        assert result["client_title"] == "Test Client"
        mock_client.setVolume.assert_called_once_with(volume)

    @pytest.mark.parametrize("volume", [-1, 101, 150])
    def test_set_volume_invalid_range(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        volume: int,
    ) -> None:
        """Test volume setting with invalid range."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.set_volume("Test Client", volume)

        assert result["success"] is False
        assert "Volume must be between 0 and 100" in result["error"]

    def test_set_volume_client_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test volume setting when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.set_volume("Nonexistent Client", 50)

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_set_volume_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test volume setting with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.set_volume("Test Client", 50)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    @pytest.mark.parametrize(
        ("direction", "expected_method"),
        [
            ("up", "moveUp"),
            ("down", "moveDown"),
            ("left", "moveLeft"),
            ("right", "moveRight"),
            ("select", "select"),
            ("back", "goBack"),
            ("home", "goToHome"),
            ("menu", "contextMenu"),
        ],
    )
    def test_navigate_client_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        direction: str,
        expected_method: str,
    ) -> None:
        """Test successful client navigation."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.navigate_client("Test Client", direction)

        assert result["success"] is True
        assert f"Navigated '{direction}' on Test Client" in result["message"]
        assert result["direction"] == direction
        assert result["client_title"] == "Test Client"
        getattr(mock_client, expected_method).assert_called_once()

    def test_navigate_client_invalid_direction(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test client navigation with invalid direction."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.navigate_client("Test Client", "invalid_direction")

        assert result["success"] is False
        assert "Invalid direction 'invalid_direction'" in result["error"]
        assert "Valid directions:" in result["error"]

    def test_navigate_client_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client navigation when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.navigate_client("Nonexistent Client", "up")

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_navigate_client_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test client navigation with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.navigate_client("Test Client", "up")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    def test_get_playback_state_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_client: MagicMock,
        mock_timeline: MagicMock,
    ) -> None:
        """Test successful playback state retrieval."""
        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        mock_client.timeline = mock_timeline
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_playback_state("Test Client")

        assert result["success"] is True
        assert result["client_title"] == "Test Client"
        assert "playback_state" in result
        assert result["playback_state"]["state"] == "playing"
        assert result["playback_state"]["time"] == 30000
        assert result["playback_state"]["duration"] == 120000
        assert result["playback_state"]["volume"] == 75
        assert result["playback_state"]["muted"] is False

    def test_get_playback_state_client_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test playback state when client not found."""
        mock_server = MagicMock()
        mock_server.client.return_value = None
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_playback_state("Nonexistent Client")

        assert result["success"] is False
        assert "Client 'Nonexistent Client' not found" in result["error"]

    def test_get_playback_state_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test playback state with Plex exception."""
        mock_server = MagicMock()
        mock_server.client.side_effect = NotFound("Client not found")
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_playback_state("Test Client")

        assert result["success"] is False
        assert "Client not found" in result["error"]

    def test_client_attributes_handling(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_clients: list[MagicMock],
    ) -> None:
        """Test that client attributes are handled correctly when missing."""
        # Create a client with minimal attributes
        minimal_client = MagicMock()
        minimal_client.title = "Minimal Client"
        minimal_client.ratingKey = "minimal123"
        # Explicitly set platform, product, etc. to None
        minimal_client.platform = None
        minimal_client.product = None
        minimal_client.deviceClass = None
        minimal_client.machineIdentifier = None
        minimal_client.protocolCapabilities = []
        minimal_client.address = None
        minimal_client.port = None

        mock_server = MagicMock()
        mock_server.clients.return_value = [minimal_client]
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.list_clients()

        assert result["success"] is True
        assert result["clients"][0]["title"] == "Minimal Client"
        assert result["clients"][0]["platform"] is None
        assert result["clients"][0]["product"] is None
        assert result["clients"][0]["device_class"] is None

    def test_playback_state_attributes_handling(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock, mock_client: MagicMock
    ) -> None:
        """Test that playback state attributes are handled correctly when missing."""
        # Create a timeline with minimal attributes
        minimal_timeline = MagicMock()
        minimal_timeline.state = "paused"
        # Explicitly set time, duration, volume, etc. to 0/False
        minimal_timeline.time = 0
        minimal_timeline.duration = 0
        minimal_timeline.volume = 0
        minimal_timeline.muted = False
        minimal_timeline.repeat = 0
        minimal_timeline.shuffle = 0

        mock_server = MagicMock()
        mock_server.client.return_value = mock_client
        mock_client.timeline = minimal_timeline
        plex_client._server = mock_server

        section = ClientControlSection(mock_fastmcp, plex_client)

        result = section.get_playback_state("Test Client")

        assert result["success"] is True
        assert result["playback_state"]["state"] == "paused"
        assert result["playback_state"]["time"] == 0
        assert result["playback_state"]["duration"] == 0
        assert result["playback_state"]["volume"] == 0
        assert result["playback_state"]["muted"] is False
