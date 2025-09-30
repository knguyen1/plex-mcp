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

"""Tests for TVShowsSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.tv_shows import TVShowsSection


class TestTVShowsSection:
    """Test cases for TVShowsSection class."""

    def test_init(self, mock_fastmcp, plex_client):
        """Test TVShowsSection initialization."""
        section = TVShowsSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 6

    def test_get_tv_shows_section_success(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test successful retrieval of TV shows section."""
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section._get_tv_shows_section()

        assert result == mock_tv_shows_section

    def test_get_tv_shows_section_not_found(self, mock_fastmcp, plex_client):
        """Test TV shows section not found."""
        # Mock server with no TV shows section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = [
            MagicMock(TYPE="movie"),  # Movies section
            MagicMock(TYPE="artist"),  # Music section
        ]
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        with pytest.raises(NotFound, match="No TV shows library found on this server"):
            section._get_tv_shows_section()

    @pytest.mark.parametrize(
        ("query", "limit"),
        [
            ("drama", 10),
            ("comedy", 20),
            ("action", 5),
            ("sci-fi", 50),
        ],
    )
    def test_search_tv_shows_success(
        self,
        mock_fastmcp,
        plex_client,
        mock_tv_shows_section,
        mock_tv_show,
        query,
        limit,
    ):
        """Test successful TV show search with various parameters."""
        mock_tv_shows_section.searchShows.return_value = [mock_tv_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_tv_shows(query, limit)

        assert result["success"] is True
        assert result["query"] == query
        assert result["total_results"] == 1
        assert len(result["shows"]) == 1
        assert result["shows"][0]["title"] == "Test Show"
        mock_tv_shows_section.searchShows.assert_called_once_with(
            title=query, limit=limit
        )

    def test_search_tv_shows_not_found(self, mock_fastmcp, plex_client):
        """Test TV show search when TV shows section is not found."""
        # Mock server with no TV shows section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_tv_shows("test")

        assert result["success"] is False
        assert "TV shows library not found" in result["error"]

    def test_search_tv_shows_bad_request(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test TV show search with bad request error."""
        mock_tv_shows_section.searchShows.side_effect = BadRequest("Invalid query")
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_tv_shows("invalid")

        assert result["success"] is False
        assert "Error searching shows" in result["error"]

    def test_get_tv_shows_library_success(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test successful retrieval of TV shows library info."""
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_tv_shows_library()

        assert result["success"] is True
        assert "library_info" in result
        assert result["library_info"]["title"] == "TV Shows"
        assert result["library_info"]["type"] == "show"

    def test_get_tv_shows_library_not_found(self, mock_fastmcp, plex_client):
        """Test TV shows library info when section not found."""
        # Mock server with no TV shows section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_tv_shows_library()

        assert result["success"] is False
        assert "TV shows library not found" in result["error"]

    def test_get_show_episodes_success_all_seasons(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test successful retrieval of all episodes for a show."""
        mock_tv_shows_section.fetchItem.return_value = mock_tv_show
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("11111")

        assert result["success"] is True
        assert result["show_title"] == "Test Show"
        assert result["season"] is None
        assert result["total_episodes"] == 2  # 1 episode from each season
        assert len(result["episodes"]) == 2

    def test_get_show_episodes_success_specific_season(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test successful retrieval of episodes for a specific season."""
        mock_tv_shows_section.fetchItem.return_value = mock_tv_show
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("11111", season=1)

        assert result["success"] is True
        assert result["show_title"] == "Test Show"
        assert result["season"] == 1
        assert result["total_episodes"] == 1
        assert len(result["episodes"]) == 1
        assert result["episodes"][0]["season"] == 1

    def test_get_show_episodes_show_not_found(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test show episodes when show not found."""
        mock_tv_shows_section.fetchItem.return_value = None
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("12345")  # Use numeric string

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_show_episodes_season_not_found(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test show episodes when specific season not found."""
        mock_tv_shows_section.fetchItem.return_value = mock_tv_show
        # Mock season method to raise NotFound
        mock_tv_show.season.side_effect = NotFound("Season not found")
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("11111", season=99)

        assert result["success"] is False
        assert "Season 99 not found for show Test Show" in result["error"]

    def test_get_show_episodes_plex_exception(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test show episodes with Plex exception."""
        mock_tv_shows_section.fetchItem.side_effect = NotFound("Show not found")
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("11111")

        assert result["success"] is False
        assert "TV show not found" in result["error"]

    def test_get_episode_info_success(self, mock_fastmcp, plex_client, mock_episode):
        """Test successful retrieval of episode info."""
        # Set the grandparentTitle explicitly
        mock_episode.grandparentTitle = "Test Show"

        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_episode
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_episode_info("10001")

        assert result["success"] is True
        assert "episode" in result
        assert result["episode"]["title"] == "Test Episode"
        assert result["episode"]["season"] == 1
        assert result["episode"]["episode"] == 1
        assert result["episode"]["show_title"] == "Test Show"

    def test_get_episode_info_not_found(self, mock_fastmcp, plex_client):
        """Test episode info when episode not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_episode_info("99999")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_episode_info_plex_exception(self, mock_fastmcp, plex_client):
        """Test episode info with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Episode not found")
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_episode_info("10001")

        assert result["success"] is False
        assert "Episode not found" in result["error"]

    def test_search_episodes_by_show_success(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test successful episode search within a show."""
        mock_tv_shows_section.searchShows.return_value = [mock_tv_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Test Show", "episode", 10)

        assert result["success"] is True
        assert result["show_title"] == "Test Show"
        assert result["query"] == "episode"
        assert result["total_results"] == 2  # 2 episodes total
        assert len(result["episodes"]) == 2

    def test_search_episodes_by_show_no_query(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test episode search within a show without query."""
        mock_tv_shows_section.searchShows.return_value = [mock_tv_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Test Show", "", 10)

        assert result["success"] is True
        assert result["show_title"] == "Test Show"
        assert result["query"] == ""
        assert result["total_results"] == 2
        assert len(result["episodes"]) == 2

    def test_search_episodes_by_show_show_not_found(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test episode search when show not found."""
        mock_tv_shows_section.searchShows.return_value = []
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Nonexistent Show", "episode")

        assert result["success"] is False
        assert "TV show 'Nonexistent Show' not found" in result["error"]

    def test_search_episodes_by_show_with_query_filtering(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test episode search with query filtering."""
        # Create a show with episodes that match and don't match the query
        show = MagicMock()
        show.title = "Test Show"

        # Create episodes with different titles
        episode1 = MagicMock()
        episode1.title = "Episode One"
        episode1.seasonNumber = 1
        episode1.episodeNumber = 1
        episode1.summary = "First episode"
        episode1.ratingKey = "ep1"
        episode1.viewedAt = None

        episode2 = MagicMock()
        episode2.title = "Episode Two"
        episode2.seasonNumber = 1
        episode2.episodeNumber = 2
        episode2.summary = "Second episode"
        episode2.ratingKey = "ep2"
        episode2.viewedAt = None

        season = MagicMock()
        season.episodes.return_value = [episode1, episode2]
        show.seasons.return_value = [season]

        mock_tv_shows_section.searchShows.return_value = [show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Test Show", "One", 10)

        assert result["success"] is True
        assert result["total_results"] == 1  # Only episode with "One" in title
        assert result["episodes"][0]["title"] == "Episode One"

    def test_search_episodes_by_show_limit(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show
    ):
        """Test episode search with limit."""
        mock_tv_shows_section.searchShows.return_value = [mock_tv_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Test Show", "", 1)

        assert result["success"] is True
        assert result["total_results"] == 1
        assert len(result["episodes"]) == 1

    def test_search_episodes_by_show_plex_exception(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test episode search with Plex exception."""
        mock_tv_shows_section.searchShows.side_effect = NotFound("Show not found")
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_episodes_by_show("Test Show", "episode")

        assert result["success"] is False
        assert "TV show not found" in result["error"]

    @pytest.mark.parametrize("limit", [5, 10, 20, 50])
    def test_get_recently_added_shows_success(
        self, mock_fastmcp, plex_client, mock_tv_shows_section, mock_tv_show, limit
    ):
        """Test successful retrieval of recently added shows."""
        mock_tv_shows_section.recentlyAdded.return_value = [mock_tv_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_recently_added_shows(limit)

        assert result["success"] is True
        assert result["total_results"] == 1
        assert len(result["shows"]) == 1
        assert result["shows"][0]["title"] == "Test Show"
        mock_tv_shows_section.recentlyAdded.assert_called_once_with(maxresults=limit)

    def test_get_recently_added_shows_not_found(self, mock_fastmcp, plex_client):
        """Test recently added shows when section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_recently_added_shows()

        assert result["success"] is False
        assert "TV shows library not found" in result["error"]

    def test_show_attributes_handling(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test that show attributes are handled correctly when missing."""
        # Create a show with minimal attributes
        minimal_show = MagicMock()
        minimal_show.title = "Minimal Show"
        minimal_show.ratingKey = "minimal123"
        # Set year, summary, rating to None explicitly
        minimal_show.year = None
        minimal_show.summary = None
        minimal_show.rating = None

        mock_tv_shows_section.searchShows.return_value = [minimal_show]
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.search_tv_shows("minimal")

        assert result["success"] is True
        assert result["shows"][0]["title"] == "Minimal Show"
        assert result["shows"][0]["year"] is None
        assert result["shows"][0]["summary"] is None
        assert result["shows"][0]["rating"] is None

    def test_episode_attributes_handling(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test that episode attributes are handled correctly when missing."""
        # Create an episode with minimal attributes
        minimal_episode = MagicMock()
        minimal_episode.title = "Minimal Episode"
        minimal_episode.seasonNumber = 1
        minimal_episode.episodeNumber = 1
        minimal_episode.ratingKey = "10004"
        minimal_episode.viewedAt = None
        # Set summary, duration to None explicitly
        minimal_episode.summary = None
        minimal_episode.duration = None
        minimal_episode.rating = None

        mock_server = MagicMock()
        mock_server.fetchItem.return_value = minimal_episode
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_episode_info("10004")

        assert result["success"] is True
        episode_info = result["episode"]
        assert episode_info["title"] == "Minimal Episode"
        assert episode_info["summary"] is None
        assert episode_info["duration"] is None
        assert episode_info["rating"] is None

    def test_episode_viewed_status(self, mock_fastmcp, plex_client):
        """Test episode viewed status handling."""
        # Create an episode that has been viewed
        viewed_episode = MagicMock()
        viewed_episode.title = "Viewed Episode"
        viewed_episode.seasonNumber = 1
        viewed_episode.episodeNumber = 1
        viewed_episode.ratingKey = "10003"
        viewed_episode.viewedAt = "2023-01-01T00:00:00Z"

        mock_server = MagicMock()
        mock_server.fetchItem.return_value = viewed_episode
        plex_client._server = mock_server

        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_episode_info("10003")

        assert result["success"] is True
        episode_info = result["episode"]
        assert episode_info["viewed"] is True
        assert episode_info["viewed_at"] == "2023-01-01T00:00:00Z"

    def test_show_with_multiple_seasons(
        self, mock_fastmcp, plex_client, mock_tv_shows_section
    ):
        """Test show with multiple seasons and episodes."""
        # Create a show with multiple seasons
        show = MagicMock()
        show.title = "Multi-Season Show"
        show.ratingKey = "multiseason123"

        # Create seasons
        season1 = MagicMock()
        season1.seasonNumber = 1
        episode1 = MagicMock()
        episode1.title = "S1E1"
        episode1.seasonNumber = 1
        episode1.episodeNumber = 1
        episode1.summary = "Season 1 Episode 1"
        episode1.duration = 1800000
        episode1.ratingKey = "s1e1"
        episode1.viewedAt = None
        season1.episodes.return_value = [episode1]

        season2 = MagicMock()
        season2.seasonNumber = 2
        episode2 = MagicMock()
        episode2.title = "S2E1"
        episode2.seasonNumber = 2
        episode2.episodeNumber = 1
        episode2.summary = "Season 2 Episode 1"
        episode2.duration = 1800000
        episode2.ratingKey = "s2e1"
        episode2.viewedAt = None
        season2.episodes.return_value = [episode2]

        show.seasons.return_value = [season1, season2]
        show.season.return_value = season1

        mock_tv_shows_section.fetchItem.return_value = show
        section = TVShowsSection(mock_fastmcp, plex_client)

        result = section.get_show_episodes("12345")  # Use numeric string

        assert result["success"] is True
        assert result["total_episodes"] == 2
        assert len(result["episodes"]) == 2
        assert result["episodes"][0]["title"] == "S1E1"
        assert result["episodes"][1]["title"] == "S2E1"
