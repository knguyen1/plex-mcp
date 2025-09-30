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

"""Tests for PlexClient class."""

import os
from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient


class TestPlexClient:
    """Test cases for PlexClient class."""

    def test_init_with_parameters(self):
        """Test PlexClient initialization with explicit parameters."""
        client = PlexClient("http://localhost:32400", "test-token")

        assert client.baseurl == "http://localhost:32400"
        assert client.token == "test-token"
        assert client._server is None

    def test_init_with_environment_variables(self, mock_environment):
        """Test PlexClient initialization with environment variables."""
        client = PlexClient("", "")

        assert client.baseurl == "http://test-server:32400"
        assert client.token == "test-env-token"

    def test_init_missing_parameters(self):
        """Test PlexClient initialization with missing parameters."""
        with pytest.raises(ValueError, match="Base URL and token are required"):
            PlexClient("", "")

    def test_init_missing_baseurl(self):
        """Test PlexClient initialization with missing baseurl."""
        with pytest.raises(ValueError, match="Base URL and token are required"):
            PlexClient("", "test-token")

    def test_init_missing_token(self):
        """Test PlexClient initialization with missing token."""
        with pytest.raises(ValueError, match="Base URL and token are required"):
            PlexClient("http://localhost:32400", "")

    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_success(self, mock_plex_server_class, mock_plex_server):
        """Test successful server initialization."""
        mock_plex_server_class.return_value = mock_plex_server
        client = PlexClient("http://localhost:32400", "test-token")

        server = client.get_server()

        assert server == mock_plex_server
        assert client._server == mock_plex_server
        mock_plex_server_class.assert_called_once_with(
            "http://localhost:32400", "test-token"
        )
        mock_plex_server.library.sections.assert_called_once()

    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_cached(self, mock_plex_server_class, mock_plex_server):
        """Test that server is cached after first call."""
        mock_plex_server_class.return_value = mock_plex_server
        client = PlexClient("http://localhost:32400", "test-token")

        # First call
        server1 = client.get_server()
        # Second call
        server2 = client.get_server()

        assert server1 == server2 == mock_plex_server
        # PlexServer should only be called once
        mock_plex_server_class.assert_called_once()

    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_connection_error(self, mock_plex_server_class):
        """Test server initialization with connection error."""
        mock_plex_server_class.side_effect = Exception("Connection failed")
        client = PlexClient("http://localhost:32400", "test-token")

        with pytest.raises(Exception, match="Connection failed"):
            client.get_server()

    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_validation_error(self, mock_plex_server_class):
        """Test server initialization with validation error."""
        mock_server = MagicMock()
        mock_server.library.sections.side_effect = NotFound("Library not found")
        mock_plex_server_class.return_value = mock_server
        client = PlexClient("http://localhost:32400", "test-token")

        with pytest.raises(NotFound, match="Library not found"):
            client.get_server()

    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_bad_request_error(self, mock_plex_server_class):
        """Test server initialization with bad request error."""
        mock_server = MagicMock()
        mock_server.library.sections.side_effect = BadRequest("Invalid request")
        mock_plex_server_class.return_value = mock_server
        client = PlexClient("http://localhost:32400", "test-token")

        with pytest.raises(BadRequest, match="Invalid request"):
            client.get_server()

    @pytest.mark.parametrize(
        ("baseurl", "token"),
        [
            ("http://localhost:32400", "token123"),
            ("https://plex.example.com:32400", "abc123def456"),
            ("http://192.168.1.100:32400", "xyz789"),
        ],
    )
    def test_init_with_various_parameters(self, baseurl, token):
        """Test PlexClient initialization with various valid parameters."""
        client = PlexClient(baseurl, token)

        assert client.baseurl == baseurl
        assert client.token == token
        assert client._server is None

    def test_init_with_empty_strings(self):
        """Test PlexClient initialization with empty strings."""
        with pytest.raises(ValueError, match="Base URL and token are required"):
            PlexClient("", "test-token")

        with pytest.raises(ValueError, match="Base URL and token are required"):
            PlexClient("http://localhost:32400", "")

    def test_init_with_whitespace_strings(self):
        """Test PlexClient initialization with whitespace-only strings."""
        # The current implementation doesn't strip whitespace, so these should work
        # but the validation should catch empty strings after stripping
        client1 = PlexClient("   ", "test-token")
        assert client1.baseurl == "   "
        assert client1.token == "test-token"

        client2 = PlexClient("http://localhost:32400", "   ")
        assert client2.baseurl == "http://localhost:32400"
        assert client2.token == "   "

    @patch.dict(
        os.environ,
        {"PLEX_BASEURL": "http://env-server:32400", "PLEX_TOKEN": "env-token"},
    )
    def test_init_with_mixed_parameters_and_env(self):
        """Test PlexClient initialization with some parameters and environment variables."""
        # baseurl provided, token from env
        client1 = PlexClient("http://explicit:32400", "")
        assert client1.baseurl == "http://explicit:32400"
        assert client1.token == "env-token"

        # token provided, baseurl from env
        client2 = PlexClient("", "explicit-token")
        assert client2.baseurl == "http://env-server:32400"
        assert client2.token == "explicit-token"

    @patch("plex_mcp.client.plex_client.logger")
    @patch("plex_mcp.client.plex_client.PlexServer")
    def test_get_server_logging(
        self, mock_plex_server_class, mock_logger, mock_plex_server
    ):
        """Test that get_server logs appropriate messages."""
        mock_plex_server_class.return_value = mock_plex_server
        client = PlexClient("http://localhost:32400", "test-token")

        client.get_server()

        # Check that appropriate log messages were called
        mock_logger.info.assert_any_call(
            "Initializing PlexServer with URL: %s", "http://localhost:32400"
        )
        mock_logger.info.assert_any_call("Successfully initialized PlexServer.")
        mock_logger.info.assert_any_call("Plex server connection validated.")

    def test_server_property_access(self, plex_client):
        """Test accessing server properties through the client."""
        server = plex_client.get_server()

        # Test that we can access library sections
        sections = server.library.sections()
        assert len(sections) == 3
        assert sections[0].title == "Movies"
        assert sections[1].title == "Music"
        assert sections[2].title == "TV Shows"
