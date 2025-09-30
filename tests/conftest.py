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

"""Test fixtures for plex-mcp package."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient


@pytest.fixture
def mock_plex_server(mock_movies_section, mock_music_section, mock_tv_shows_section):
    """Create a mock PlexServer instance."""
    server = MagicMock()
    server.library.sections.return_value = [
        mock_movies_section,
        mock_music_section,
        mock_tv_shows_section,
    ]
    return server


@pytest.fixture
def mock_movies_section():
    """Create a mock movies library section."""
    return _create_mock_section("Movies", "movie", "1")


@pytest.fixture
def mock_music_section():
    """Create a mock music library section."""
    return _create_mock_section("Music", "artist", "2")


@pytest.fixture
def mock_tv_shows_section():
    """Create a mock TV shows library section."""
    return _create_mock_section("TV Shows", "show", "3")


@pytest.fixture
def mock_movie():
    """Create a mock movie object."""
    movie = MagicMock()
    movie.title = "Test Movie"
    movie.year = 2023
    movie.summary = "A test movie"
    movie.rating = 8.5
    movie.duration = 7200000  # 2 hours in milliseconds
    movie.ratingKey = "12345"
    movie.thumb = "http://example.com/thumb.jpg"
    movie.viewedAt = None
    movie.addedAt = "2023-01-01T00:00:00Z"
    movie.studio = "Test Studio"
    movie.contentRating = "PG-13"

    # Mock genres
    genre1 = MagicMock()
    genre1.tag = "Action"
    genre2 = MagicMock()
    genre2.tag = "Drama"
    movie.genres = [genre1, genre2]

    # Mock directors
    director1 = MagicMock()
    director1.tag = "John Director"
    movie.directors = [director1]

    # Mock actors
    actor1 = MagicMock()
    actor1.tag = "Jane Actor"
    actor2 = MagicMock()
    actor2.tag = "Bob Actor"
    movie.actors = [actor1, actor2]

    return movie


@pytest.fixture
def mock_track():
    """Create a mock music track object."""
    track = MagicMock()
    track.title = "Test Song"
    track.grandparentTitle = "Test Artist"
    track.parentTitle = "Test Album"
    track.year = 2023
    track.duration = 180000  # 3 minutes in milliseconds
    track.ratingKey = "67890"
    return track


@pytest.fixture
def mock_tv_show():
    """Create a mock TV show object."""
    show = MagicMock()
    show.title = "Test Show"
    show.year = 2023
    show.summary = "A test TV show"
    show.rating = 9.0
    show.ratingKey = "11111"
    show.thumb = "http://example.com/show_thumb.jpg"
    show.addedAt = "2023-01-01T00:00:00Z"

    # Mock seasons
    season1 = MagicMock()
    season1.seasonNumber = 1
    season1.episodes.return_value = [_create_mock_episode("Episode 1", 1, 1)]
    season2 = MagicMock()
    season2.seasonNumber = 2
    season2.episodes.return_value = [_create_mock_episode("Episode 2", 2, 1)]
    show.seasons.return_value = [season1, season2]
    show.season.return_value = season1

    return show


@pytest.fixture
def mock_episode():
    """Create a mock episode object."""
    return _create_mock_episode("Test Episode", 1, 1)


@pytest.fixture
def mock_playlist():
    """Create a mock playlist object."""
    playlist = MagicMock()
    playlist.title = "Test Playlist"
    playlist.ratingKey = "playlist123"
    playlist.items.return_value = [
        _create_mock_track("Song 1"),
        _create_mock_track("Song 2"),
    ]
    playlist._getWebURL.return_value = "http://example.com/playlist"
    return playlist


@pytest.fixture
def plex_client(mock_plex_server):
    """Create a PlexClient instance with mocked server."""
    client = PlexClient("http://localhost:32400", "test-token")
    client._server = mock_plex_server
    return client


@pytest.fixture
def mock_fastmcp():
    """Create a mock FastMCP instance."""
    return MagicMock()


@pytest.fixture
def sample_movies():
    """Sample movie data for testing."""
    return [
        {
            "title": "The Matrix",
            "year": 1999,
            "summary": "A computer hacker learns about the true nature of reality.",
            "rating": 8.7,
            "rating_key": "12345",
        },
        {
            "title": "Inception",
            "year": 2010,
            "summary": "A thief who steals corporate secrets through dream-sharing.",
            "rating": 8.8,
            "rating_key": "12346",
        },
    ]


@pytest.fixture
def sample_tracks():
    """Sample track data for testing."""
    return [
        {
            "title": "Bohemian Rhapsody",
            "artist": "Queen",
            "album": "A Night at the Opera",
            "year": 1975,
            "rating_key": "67890",
        },
        {
            "title": "Hotel California",
            "artist": "Eagles",
            "album": "Hotel California",
            "year": 1976,
            "rating_key": "67891",
        },
    ]


@pytest.fixture
def sample_tv_shows():
    """Sample TV show data for testing."""
    return [
        {
            "title": "Breaking Bad",
            "year": 2008,
            "summary": "A high school chemistry teacher turned methamphetamine manufacturer.",
            "rating": 9.5,
            "rating_key": "11111",
        },
        {
            "title": "The Office",
            "year": 2005,
            "summary": "A mockumentary about office workers.",
            "rating": 8.9,
            "rating_key": "11112",
        },
    ]


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        "not_found": NotFound("Resource not found"),
        "bad_request": BadRequest("Invalid request"),
        "value_error": ValueError("Invalid value"),
    }


def _create_mock_section(title: str, section_type: str, key: str) -> MagicMock:
    """Create a mock library section."""
    section = MagicMock()
    section.title = title
    section.TYPE = section_type
    section.key = key
    section.refreshing = False
    return section


def _create_mock_episode(title: str, season: int, episode: int) -> MagicMock:
    """Create a mock episode object."""
    episode_obj = MagicMock()
    episode_obj.title = title
    episode_obj.seasonNumber = season
    episode_obj.episodeNumber = episode
    episode_obj.summary = f"Summary for {title}"
    episode_obj.duration = 1800000  # 30 minutes
    episode_obj.ratingKey = f"episode_{season}_{episode}"
    episode_obj.viewedAt = None
    episode_obj.thumb = f"http://example.com/episode_{season}_{episode}.jpg"
    return episode_obj


def _create_mock_track(title: str) -> MagicMock:
    """Create a mock track object."""
    track = MagicMock()
    track.title = title
    track.grandparentTitle = "Test Artist"
    track.parentTitle = "Test Album"
    track.ratingKey = f"track_{title.replace(' ', '_')}"
    return track


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setenv("PLEX_BASEURL", "http://test-server:32400")
        m.setenv("PLEX_TOKEN", "test-env-token")
        yield


@pytest.fixture
def parametrized_search_queries():
    """Parametrized search queries for testing."""
    return [
        "action",
        "comedy",
        "drama",
        "sci-fi",
        "thriller",
    ]


@pytest.fixture
def parametrized_years():
    """Parametrized years for testing."""
    return [1990, 2000, 2010, 2020, 2023]


@pytest.fixture
def parametrized_ratings():
    """Parametrized ratings for testing."""
    return [6.0, 7.0, 8.0, 9.0, 10.0]


@pytest.fixture
def parametrized_limits():
    """Parametrized limits for testing."""
    return [1, 5, 10, 20, 50]
