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

"""Tests for UserManagementSection class."""

from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.user_management import UserManagementSection


class TestUserManagementSection:
    """Test cases for UserManagementSection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test UserManagementSection initialization."""
        section = UserManagementSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 8

    def test_get_users_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_users: list[MagicMock],
    ) -> None:
        """Test successful users retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.users.return_value = mock_users

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_users()

        assert result["success"] is True
        assert result["total_users"] == len(mock_users)
        assert "users" in result
        mock_server.myPlexAccount.assert_called_once()
        mock_plex_account.users.assert_called_once()

    def test_get_users_no_account(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test users retrieval with no Plex account."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = None

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_users()

        assert result["success"] is False
        assert "Server is not connected to Plex account" in result["error"]

    def test_get_users_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test users retrieval with error."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.side_effect = BadRequest("Account error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_users()

        assert result["success"] is False
        assert "Error getting users" in result["error"]

    def test_get_user_info_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test successful user info retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_info("testuser")

        assert result["success"] is True
        assert "user" in result
        mock_plex_account.user.assert_called_once_with("testuser")

    def test_get_user_info_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
    ) -> None:
        """Test user info with user not found."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.side_effect = NotFound("User not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_info("testuser")

        assert result["success"] is False
        assert "User not found" in result["error"]

    def test_get_user_permissions_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test successful user permissions retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_permissions("testuser")

        assert result["success"] is True
        assert "permissions" in result
        assert "user_id" in result
        mock_plex_account.user.assert_called_once_with("testuser")

    def test_get_user_activity_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
        mock_activity: list[MagicMock],
    ) -> None:
        """Test successful user activity retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.sessions.return_value = mock_activity

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_activity("testuser", limit=10)

        assert result["success"] is True
        assert "activities" in result
        assert result["total_activities"] == len(mock_activity)
        mock_server.sessions.assert_called_once()

    def test_get_user_activity_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test user activity with error."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.sessions.side_effect = BadRequest("Sessions error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_activity("testuser")

        assert result["success"] is False
        assert "Error getting user activity" in result["error"]

    def test_get_user_watch_history_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
        mock_history: list[MagicMock],
    ) -> None:
        """Test successful user watch history retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.history.return_value = mock_history

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_watch_history("testuser", limit=20)

        assert result["success"] is True
        assert "history" in result
        assert result["total_items"] == len(mock_history)
        mock_server.history.assert_called_once_with(limit=20)

    def test_get_user_recommendations_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
        mock_recommendations: list[MagicMock],
    ) -> None:
        """Test successful user recommendations retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.recommendations.return_value = mock_recommendations

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_recommendations("testuser", limit=15)

        assert result["success"] is True
        assert "recommendations" in result
        assert result["total_recommendations"] == len(mock_recommendations)
        mock_server.recommendations.assert_called_once_with(limit=15)

    def test_get_user_libraries_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
        mock_servers: list[MagicMock],
    ) -> None:
        """Test successful user libraries retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.library.sections.return_value = mock_servers

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_libraries("testuser")

        assert result["success"] is True
        assert "libraries" in result
        assert "total_libraries" in result
        mock_server.library.sections.assert_called_once()

    def test_get_user_settings_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test successful user settings retrieval."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_settings("testuser")

        assert result["success"] is True
        assert "settings" in result
        assert "user_id" in result
        mock_plex_account.user.assert_called_once_with("testuser")

    def test_get_user_settings_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_plex_account: MagicMock,
        mock_user: MagicMock,
    ) -> None:
        """Test user settings with error."""
        mock_server = MagicMock()
        mock_server.myPlexAccount.return_value = mock_plex_account
        mock_plex_account.user.return_value = mock_user
        mock_server.myPlexAccount.side_effect = BadRequest("Account error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = UserManagementSection(mock_fastmcp, plex_client)
            result = section.get_user_settings("testuser")

        assert result["success"] is False
        assert "Error getting user settings" in result["error"]


@pytest.fixture
def mock_users():
    """Create a list of mock users."""
    users = []
    for i in range(3):
        user = MagicMock()
        user.id = f"user{i}"
        user.username = f"user{i}"
        user.email = f"user{i}@example.com"
        user.title = f"User {i}"
        user.thumb = f"thumb{i}"
        user.home = i == 0
        user.protected = i == 1
        user.allowSync = True
        user.allowCameraUpload = False
        user.allowChannels = True
        users.append(user)
    return users


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock()
    user.id = "user123"
    user.username = "testuser"
    user.email = "testuser@example.com"
    user.title = "Test User"
    user.thumb = "thumb123"
    user.home = False
    user.protected = False
    user.allowSync = True
    user.allowCameraUpload = False
    user.allowChannels = True
    user.filterAll = "all"
    user.filterMovies = "all"
    user.filterTelevision = "all"
    user.filterMusic = "all"
    user.filterPhotos = "all"
    return user


@pytest.fixture
def mock_activity():
    """Create a list of mock activity items."""
    activities = []
    for i in range(5):
        activity = MagicMock()
        activity.title = f"Activity {i}"
        activity.ratingKey = f"key{i}"
        activity.type = "movie" if i % 2 == 0 else "episode"
        activity.thumb = f"thumb{i}"
        activity.summary = f"Summary {i}"
        activity.viewedAt = f"2024-01-{i + 1:02d}"
        activity.duration = 7200000
        activity.viewOffset = 3600000
        activity.userID = "testuser"  # Add userID attribute
        activities.append(activity)
    return activities


@pytest.fixture
def mock_history():
    """Create a list of mock history items."""
    history = []
    for i in range(10):
        item = MagicMock()
        item.title = f"History Item {i}"
        item.ratingKey = f"key{i}"
        item.type = "movie" if i % 3 == 0 else "episode"
        item.thumb = f"thumb{i}"
        item.summary = f"Summary {i}"
        item.viewedAt = f"2024-01-{i + 1:02d}"
        item.duration = 7200000
        item.viewOffset = 3600000
        item.librarySectionTitle = "Movies" if i % 3 == 0 else "TV Shows"
        item.userID = "testuser"  # Add userID attribute
        history.append(item)
    return history


@pytest.fixture
def mock_recommendations():
    """Create a list of mock recommendations."""
    recommendations = []
    for i in range(8):
        rec = MagicMock()
        rec.title = f"Recommendation {i}"
        rec.ratingKey = f"key{i}"
        rec.type = "movie" if i % 2 == 0 else "show"
        rec.thumb = f"thumb{i}"
        rec.summary = f"Summary {i}"
        rec.year = 2020 + i
        rec.rating = 8.0 + (i * 0.1)
        rec.librarySectionTitle = "Movies" if i % 2 == 0 else "TV Shows"
        recommendations.append(rec)
    return recommendations


@pytest.fixture
def mock_servers():
    """Create a list of mock servers."""
    servers = []
    for i in range(2):
        server = MagicMock()
        server.name = f"Server {i}"
        server.machineIdentifier = f"server{i}"
        server.owned = i == 0
        server.synced = i == 1
        server.sections = [MagicMock(title=f"Section {j}") for j in range(3)]
        servers.append(server)
    return servers
