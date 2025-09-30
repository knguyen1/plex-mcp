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


# Client Control fixtures
@pytest.fixture
def mock_client():
    """Create a mock Plex client."""
    client = MagicMock()
    client.title = "Test Client"
    client.platform = "iOS"
    client.product = "Plex for iOS"
    client.deviceClass = "phone"
    client.machineIdentifier = "test-client-id"
    client.protocolCapabilities = ["navigation", "playback"]
    client.address = "192.168.1.100"
    client.port = 32400
    client.version = "1.0.0"
    client.protocolVersion = "1.0"
    return client


@pytest.fixture
def mock_clients(mock_client):
    """Create a list of mock Plex clients."""
    client1 = MagicMock()
    client1.title = "Test Client 1"
    client1.platform = "iOS"
    client1.product = "Plex for iOS"
    client1.deviceClass = "phone"
    client1.machineIdentifier = "client1-id"
    client1.protocolCapabilities = ["navigation", "playback"]
    client1.address = "192.168.1.100"
    client1.port = 32400

    client2 = MagicMock()
    client2.title = "Test Client 2"
    client2.platform = "Android"
    client2.product = "Plex for Android"
    client2.deviceClass = "phone"
    client2.machineIdentifier = "client2-id"
    client2.protocolCapabilities = ["navigation", "playback"]
    client2.address = "192.168.1.101"
    client2.port = 32400

    return [client1, client2]


@pytest.fixture
def mock_media():
    """Create a mock media item."""
    media = MagicMock()
    media.title = "Test Media"
    media.ratingKey = "12345"
    media.type = "movie"
    return media


@pytest.fixture
def mock_timeline():
    """Create a mock timeline object."""
    timeline = MagicMock()
    timeline.state = "playing"
    timeline.time = 30000
    timeline.duration = 120000
    timeline.volume = 75
    timeline.muted = False
    timeline.repeat = 0
    timeline.shuffle = 0
    return timeline


# Collections fixtures
@pytest.fixture
def mock_collection():
    """Create a mock collection object."""
    collection = MagicMock()
    collection.title = "Action Movies"
    collection.summary = "Collection of action movies"
    collection.ratingKey = "12345"
    collection.childCount = 2
    collection.thumb = "http://example.com/thumb.jpg"
    collection.art = "http://example.com/art.jpg"
    collection.smart = False
    collection.contentRating = "PG-13"
    collection.audienceRating = 8.5
    collection.userRating = 9.0
    collection.librarySectionID = "1"
    collection.librarySectionTitle = "Movies"
    return collection


@pytest.fixture
def mock_collections(mock_collection):
    """Create a list of mock collections."""
    collection1 = MagicMock()
    collection1.title = "Action Movies"
    collection1.summary = "Collection of action movies"
    collection1.ratingKey = "12345"
    collection1.childCount = 2
    collection1.thumb = "http://example.com/thumb1.jpg"
    collection1.art = "http://example.com/art1.jpg"
    collection1.smart = False
    collection1.contentRating = "PG-13"
    collection1.audienceRating = 8.5
    collection1.userRating = 9.0

    collection2 = MagicMock()
    collection2.title = "Comedy Movies"
    collection2.summary = "Collection of comedy movies"
    collection2.ratingKey = "67890"
    collection2.childCount = 3
    collection2.thumb = "http://example.com/thumb2.jpg"
    collection2.art = "http://example.com/art2.jpg"
    collection2.smart = False
    collection2.contentRating = "PG"
    collection2.audienceRating = 7.5
    collection2.userRating = 8.0

    return [collection1, collection2]


@pytest.fixture
def mock_collection_items():
    """Create a list of mock collection items."""
    item1 = MagicMock()
    item1.title = "Movie 1"
    item1.year = 2023
    item1.ratingKey = "movie1"
    item1.type = "movie"
    item1.thumb = "http://example.com/movie1.jpg"

    item2 = MagicMock()
    item2.title = "Movie 2"
    item2.year = 2022
    item2.ratingKey = "movie2"
    item2.type = "movie"
    item2.thumb = "http://example.com/movie2.jpg"

    return [item1, item2]


@pytest.fixture
def mock_media_items():
    """Create a list of mock media items for collections."""
    item1 = MagicMock()
    item1.title = "Test Movie 1"
    item1.ratingKey = "12345"

    item2 = MagicMock()
    item2.title = "Test Movie 2"
    item2.ratingKey = "67890"

    return [item1, item2]


@pytest.fixture
def mock_media_item():
    """Create a single mock media item."""
    item = MagicMock()
    item.title = "Test Movie"
    item.ratingKey = "12345"
    return item


# Settings fixtures
@pytest.fixture
def mock_setting():
    """Create a mock setting object."""
    setting = MagicMock()
    setting.id = "test_setting"
    setting.label = "Test Setting"
    setting.summary = "A test setting"
    setting.value = "test_value"
    setting.default = "default_value"
    setting.type = "string"
    setting.hidden = False
    setting.advanced = False
    setting.group = "general"
    return setting


@pytest.fixture
def mock_settings(mock_setting):
    """Create a list of mock settings."""
    setting1 = MagicMock()
    setting1.id = "setting1"
    setting1.label = "Setting 1"
    setting1.summary = "First setting"
    setting1.value = "value1"
    setting1.default = "default1"
    setting1.type = "string"
    setting1.hidden = False
    setting1.advanced = False
    setting1.group = "general"

    setting2 = MagicMock()
    setting2.id = "setting2"
    setting2.label = "Setting 2"
    setting2.summary = "Second setting"
    setting2.value = "value2"
    setting2.default = "default2"
    setting2.type = "boolean"
    setting2.hidden = False
    setting2.advanced = True
    setting2.group = "advanced"

    return [setting1, setting2]


@pytest.fixture
def mock_library_sections():
    """Create a list of mock library sections."""
    movies_section = MagicMock()
    movies_section.title = "Movies"
    movies_section.TYPE = "movie"
    movies_section.key = "1"
    movies_section.refreshing = False
    movies_section.agent = "com.plexapp.agents.imdb"
    movies_section.scanner = "Plex Movie Scanner"
    movies_section.language = "en"
    movies_section.location = "/movies"

    music_section = MagicMock()
    music_section.title = "Music"
    music_section.TYPE = "artist"
    music_section.key = "2"
    music_section.refreshing = False
    music_section.agent = "com.plexapp.agents.lastfm"
    music_section.scanner = "Plex Music Scanner"
    music_section.language = "en"
    music_section.location = "/music"

    tv_section = MagicMock()
    tv_section.title = "TV Shows"
    tv_section.TYPE = "show"
    tv_section.key = "3"
    tv_section.refreshing = False
    tv_section.agent = "com.plexapp.agents.thetvdb"
    tv_section.scanner = "Plex Series Scanner"
    tv_section.language = "en"
    tv_section.location = "/tv"

    return [movies_section, music_section, tv_section]


@pytest.fixture
def mock_library_section():
    """Create a single mock library section."""
    section = MagicMock()
    section.title = "Movies"
    section.TYPE = "movie"
    section.key = "1"
    section.refreshing = False
    section.agent = "com.plexapp.agents.imdb"
    section.scanner = "Plex Movie Scanner"
    section.language = "en"
    section.location = "/movies"
    return section


@pytest.fixture
def mock_server_info():
    """Create mock server info data."""
    return {
        "friendlyName": "Test Server",
        "machineIdentifier": "test-machine-id",
        "version": "1.32.0",
        "platform": "Linux",
        "platformVersion": "Ubuntu 20.04",
        "myPlex": True,
        "myPlexUsername": "testuser",
        "myPlexSubscription": True,
        "allowSync": True,
        "allowCameraUpload": True,
        "allowChannelAccess": True,
        "allowMediaDeletion": True,
        "allowSharing": True,
        "multiuser": True,
        "transcoderActiveVideoSessions": 0,
        "transcoderVideo": True,
        "transcoderAudio": True,
        "transcoderPhoto": True,
        "transcoderSubtitles": True,
        "transcoderLyrics": True,
        "updatedAt": "2023-01-01T00:00:00Z",
    }
