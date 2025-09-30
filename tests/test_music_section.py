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

"""Tests for MusicSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.music import MusicSection


class TestMusicSection:
    """Test cases for MusicSection class."""

    def test_init(self, mock_fastmcp, plex_client):
        """Test MusicSection initialization."""
        section = MusicSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 7

    def test_get_music_section_success(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test successful retrieval of music section."""
        section = MusicSection(mock_fastmcp, plex_client)

        result = section._get_music_section()

        assert result == mock_music_section

    def test_get_music_section_not_found(self, mock_fastmcp, plex_client):
        """Test music section not found."""
        # Mock server with no music section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = [
            MagicMock(TYPE="movie"),  # Movies section
            MagicMock(TYPE="show"),  # TV section
        ]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        with pytest.raises(NotFound, match="No music library found on this server"):
            section._get_music_section()

    @pytest.mark.parametrize(
        ("query", "limit"),
        [
            ("rock", 10),
            ("jazz", 20),
            ("classical", 5),
            ("pop", 50),
        ],
    )
    def test_search_music_tracks_success(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track, query, limit
    ):
        """Test successful music track search with various parameters."""
        mock_music_section.searchTracks.return_value = [mock_track]
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_music_tracks(query, limit)

        assert result["success"] is True
        assert result["query"] == query
        assert result["total_results"] == 1
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["title"] == "Test Song"
        assert result["tracks"][0]["artist"] == "Test Artist"
        assert result["tracks"][0]["album"] == "Test Album"
        mock_music_section.searchTracks.assert_called_once_with(
            title=query, limit=limit
        )

    def test_search_music_tracks_not_found(self, mock_fastmcp, plex_client):
        """Test music track search when music section is not found."""
        # Mock server with no music section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_music_tracks("test")

        assert result["success"] is False
        assert "Music library not found" in result["error"]

    def test_search_music_tracks_bad_request(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test music track search with bad request error."""
        mock_music_section.searchTracks.side_effect = BadRequest("Invalid query")
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_music_tracks("invalid")

        assert result["success"] is False
        assert "Error searching tracks" in result["error"]

    def test_get_music_library_success(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test successful retrieval of music library info."""
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_music_library()

        assert result["success"] is True
        assert "library_info" in result
        assert result["library_info"]["title"] == "Music"
        assert result["library_info"]["type"] == "artist"

    def test_get_music_library_not_found(self, mock_fastmcp, plex_client):
        """Test music library info when section not found."""
        # Mock server with no music section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_music_library()

        assert result["success"] is False
        assert "Music library not found" in result["error"]

    def test_create_music_playlist_success(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track, mock_playlist
    ):
        """Test successful playlist creation."""
        mock_music_section.fetchItem.return_value = mock_track
        mock_server = MagicMock()
        mock_server.playlists.return_value = []  # No existing playlists
        mock_server.createPlaylist.return_value = mock_playlist
        # Ensure the server has the music section
        mock_server.library.sections.return_value = [mock_music_section]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.create_music_playlist(
            "Test Playlist", ["67890"], "Test description"
        )

        assert result["success"] is True
        assert "playlist" in result
        assert result["playlist"]["title"] == "Test Playlist"
        assert result["playlist"]["track_count"] == 2
        mock_server.createPlaylist.assert_called_once()

    def test_create_music_playlist_no_valid_tracks(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test playlist creation with no valid tracks."""
        mock_music_section.fetchItem.side_effect = NotFound("Track not found")
        mock_server = MagicMock()
        # Ensure the server has the music section
        mock_server.library.sections.return_value = [mock_music_section]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.create_music_playlist(
            "Test Playlist", ["99999"], "Test description"
        )

        assert result["success"] is False
        assert "No valid tracks found for the playlist" in result["error"]

    def test_create_music_playlist_replace_existing(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track, mock_playlist
    ):
        """Test playlist creation that replaces existing playlist."""
        mock_music_section.fetchItem.return_value = mock_track
        existing_playlist = MagicMock()
        existing_playlist.title = "Test Playlist"
        existing_playlist.delete = MagicMock()

        mock_server = MagicMock()
        mock_server.playlists.return_value = [existing_playlist]
        mock_server.createPlaylist.return_value = mock_playlist
        # Ensure the server has the music section
        mock_server.library.sections.return_value = [mock_music_section]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.create_music_playlist("Test Playlist", ["67890"])

        assert result["success"] is True
        existing_playlist.delete.assert_called_once()
        mock_server.createPlaylist.assert_called_once()

    def test_create_music_playlist_bad_request(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track
    ):
        """Test playlist creation with bad request error."""
        mock_music_section.fetchItem.return_value = mock_track
        mock_server = MagicMock()
        mock_server.playlists.return_value = []
        mock_server.createPlaylist.side_effect = BadRequest("Invalid request")
        # Ensure the server has the music section
        mock_server.library.sections.return_value = [mock_music_section]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.create_music_playlist("Test Playlist", ["67890"])

        assert result["success"] is False
        assert "Bad request" in result["error"]

    @pytest.mark.parametrize(
        ("decade", "count", "limit"),
        [
            (1990, 3, 50),
            (2000, 5, 100),
            (2010, 1, 25),
        ],
    )
    def test_get_random_tracks_by_decade_success(
        self,
        mock_fastmcp,
        plex_client,
        mock_music_section,
        mock_track,
        decade,
        count,
        limit,
    ):
        """Test successful random tracks by decade."""
        mock_music_section.searchTracks.return_value = [
            mock_track
        ] * 10  # Multiple tracks
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_random_tracks_by_decade(decade, count, limit)

        assert result["success"] is True
        assert result["decade"] == decade
        assert result["requested_count"] == count
        assert result["actual_count"] == min(count, 10)  # Limited by available tracks
        mock_music_section.searchTracks.assert_called_once_with(
            decade=decade, limit=limit
        )

    def test_get_random_tracks_by_decade_no_tracks(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test random tracks by decade when no tracks found."""
        mock_music_section.searchTracks.return_value = []
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_random_tracks_by_decade(1990, 3, 50)

        assert result["success"] is False
        assert "No tracks found from the 1990s" in result["error"]

    def test_get_random_tracks_by_decade_not_found(self, mock_fastmcp, plex_client):
        """Test random tracks by decade when music section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_random_tracks_by_decade(1990, 3, 50)

        assert result["success"] is False
        assert "Music library not found" in result["error"]

    @pytest.mark.parametrize(
        ("artist", "limit"),
        [
            ("Queen", 10),
            ("The Beatles", 20),
            ("Led Zeppelin", 5),
        ],
    )
    def test_search_tracks_by_artist_success(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track, artist, limit
    ):
        """Test successful track search by artist."""
        mock_music_section.searchTracks.return_value = [mock_track]
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_tracks_by_artist(artist, limit)

        assert result["success"] is True
        assert result["artist"] == artist
        assert result["total_results"] == 1
        mock_music_section.searchTracks.assert_called_once_with(
            filters={"artist.title": artist}, limit=limit
        )

    def test_search_tracks_by_artist_not_found(self, mock_fastmcp, plex_client):
        """Test track search by artist when music section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_tracks_by_artist("Queen")

        assert result["success"] is False
        assert "Music library not found" in result["error"]

    def test_get_playlist_info_success(self, mock_fastmcp, plex_client, mock_playlist):
        """Test successful playlist info retrieval."""
        mock_server = MagicMock()
        mock_server.playlists.return_value = [mock_playlist]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_playlist_info("Test Playlist")

        assert result["success"] is True
        assert "playlist" in result
        assert result["playlist"]["title"] == "Test Playlist"
        assert result["playlist"]["track_count"] == 2
        assert len(result["playlist"]["tracks"]) == 2

    def test_get_playlist_info_not_found(self, mock_fastmcp, plex_client):
        """Test playlist info when playlist not found."""
        mock_server = MagicMock()
        mock_server.playlists.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_playlist_info("Nonexistent Playlist")

        assert result["success"] is False
        assert "Playlist 'Nonexistent Playlist' not found" in result["error"]

    def test_get_playlist_info_error(self, mock_fastmcp, plex_client):
        """Test playlist info with error."""
        mock_server = MagicMock()
        mock_server.playlists.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_playlist_info("Test Playlist")

        assert result["success"] is False
        assert "Error getting playlist info" in result["error"]

    def test_delete_playlist_success(self, mock_fastmcp, plex_client):
        """Test successful playlist deletion."""
        mock_playlist = MagicMock()
        mock_playlist.delete = MagicMock()

        mock_server = MagicMock()
        mock_server.playlists.return_value = [mock_playlist]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.delete_playlist("Test Playlist")

        assert result["success"] is True
        assert "Deleted 1 playlist(s)" in result["message"]
        mock_playlist.delete.assert_called_once()

    def test_delete_playlist_multiple_matches(self, mock_fastmcp, plex_client):
        """Test playlist deletion with multiple matching playlists."""
        mock_playlist1 = MagicMock()
        mock_playlist1.delete = MagicMock()
        mock_playlist2 = MagicMock()
        mock_playlist2.delete = MagicMock()

        mock_server = MagicMock()
        mock_server.playlists.return_value = [mock_playlist1, mock_playlist2]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.delete_playlist("Test Playlist")

        assert result["success"] is True
        assert "Deleted 2 playlist(s)" in result["message"]
        mock_playlist1.delete.assert_called_once()
        mock_playlist2.delete.assert_called_once()

    def test_delete_playlist_not_found(self, mock_fastmcp, plex_client):
        """Test playlist deletion when playlist not found."""
        mock_server = MagicMock()
        mock_server.playlists.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.delete_playlist("Nonexistent Playlist")

        assert result["success"] is False
        assert "Playlist 'Nonexistent Playlist' not found" in result["error"]

    def test_delete_playlist_error(self, mock_fastmcp, plex_client):
        """Test playlist deletion with error."""
        mock_server = MagicMock()
        mock_server.playlists.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.delete_playlist("Test Playlist")

        assert result["success"] is False
        assert "Error deleting playlist" in result["error"]

    def test_track_attributes_handling(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test that track attributes are handled correctly when missing."""
        # Create a track with minimal attributes
        minimal_track = MagicMock()
        minimal_track.title = "Minimal Track"
        minimal_track.grandparentTitle = "Minimal Artist"
        minimal_track.parentTitle = "Minimal Album"
        minimal_track.ratingKey = "minimal123"
        # Set year and duration to None explicitly
        minimal_track.year = None
        minimal_track.duration = None

        mock_music_section.searchTracks.return_value = [minimal_track]
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_music_tracks("minimal")

        assert result["success"] is True
        assert result["tracks"][0]["title"] == "Minimal Track"
        assert result["tracks"][0]["year"] is None
        assert result["tracks"][0]["duration"] is None

    def test_playlist_track_info(self, mock_fastmcp, plex_client, mock_playlist):
        """Test playlist track information extraction."""
        mock_server = MagicMock()
        mock_server.playlists.return_value = [mock_playlist]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_playlist_info("Test Playlist")

        assert result["success"] is True
        tracks = result["playlist"]["tracks"]
        assert len(tracks) == 2
        assert tracks[0]["title"] == "Song 1"
        assert tracks[0]["artist"] == "Test Artist"
        assert tracks[0]["album"] == "Test Album"
        assert tracks[1]["title"] == "Song 2"

    def test_random_tracks_sampling(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test that random tracks are properly sampled."""
        # Create multiple tracks
        tracks = []
        for i in range(10):
            track = MagicMock()
            track.title = f"Track {i}"
            track.grandparentTitle = "Test Artist"
            track.parentTitle = "Test Album"
            track.ratingKey = f"track{i}"
            tracks.append(track)

        mock_music_section.searchTracks.return_value = tracks
        section = MusicSection(mock_fastmcp, plex_client)

        result = section.get_random_tracks_by_decade(1990, 3, 50)

        assert result["success"] is True
        assert result["actual_count"] == 3
        assert len(result["tracks"]) == 3
        # Verify that we got 3 different tracks
        track_titles = [track["title"] for track in result["tracks"]]
        assert len(set(track_titles)) == 3

    def test_create_playlist_with_mixed_valid_invalid_tracks(
        self, mock_fastmcp, plex_client, mock_music_section, mock_track
    ):
        """Test playlist creation with some valid and some invalid tracks."""

        # Mock fetchItem to return track for valid key, raise NotFound for invalid
        def mock_fetch_item(rating_key):
            if rating_key == 12345:
                return mock_track
            msg = "Track not found"
            raise NotFound(msg)

        mock_music_section.fetchItem.side_effect = mock_fetch_item
        mock_server = MagicMock()
        mock_server.playlists.return_value = []
        mock_server.createPlaylist.return_value = MagicMock()
        # Ensure the server has the music section
        mock_server.library.sections.return_value = [mock_music_section]
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.create_music_playlist("Test Playlist", ["12345", "67890"])

        assert result["success"] is True
        # Should create playlist with only the valid track
        mock_server.createPlaylist.assert_called_once()
        call_args = mock_server.createPlaylist.call_args
        assert call_args[1]["title"] == "Test Playlist"
        assert len(call_args[1]["items"]) == 1  # Only one valid track
