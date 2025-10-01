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

"""Integration tests for MusicSection with Strategy Pattern."""

from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.music import MusicSection


class TestMusicSectionStrategyIntegration:
    """Test cases for MusicSection integration with Strategy Pattern."""

    def test_search_tracks_by_artist_with_strategy_pattern_success(
        self, mock_fastmcp, plex_client, mock_track
    ):
        """Test successful artist search using Strategy Pattern."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Mock the search context to return successful result
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": True,
                "tracks": [mock_track],
                "matched_artists": ["Queen"],
            }
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Queen", 10)

            assert result["success"] is True
            assert result["artist"] == "Queen"
            assert result["total_results"] == 1
            assert result["matched_artists"] == ["Queen"]
            assert len(result["tracks"]) == 1
            assert result["tracks"][0]["title"] == "Test Song"
            assert result["tracks"][0]["artist"] == "Test Artist"

    def test_search_tracks_by_artist_with_strategy_pattern_failure(
        self, mock_fastmcp, plex_client
    ):
        """Test artist search failure using Strategy Pattern."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Mock the search context to return failure
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": False,
                "tracks": [],
                "matched_artists": [],
            }
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Unknown Artist", 10)

            assert result["success"] is False
            assert "No artists found matching 'Unknown Artist'" in result["error"]

    def test_search_tracks_by_artist_unicode_character_handling(
        self, mock_fastmcp, plex_client, mock_track
    ):
        """Test Unicode character handling in artist search."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Mock track with Unicode character
        mock_track.grandparentTitle = "Static‐X"  # With en-dash

        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": True,
                "tracks": [mock_track],
                "matched_artists": ["Static‐X"],
            }
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Static-X", 10)

            assert result["success"] is True
            assert result["artist"] == "Static-X"
            assert result["matched_artists"] == ["Static‐X"]

    def test_search_tracks_by_artist_case_insensitive(
        self, mock_fastmcp, plex_client, mock_track
    ):
        """Test case-insensitive artist search."""
        section = MusicSection(mock_fastmcp, plex_client)

        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": True,
                "tracks": [mock_track],
                "matched_artists": ["Queen"],
            }
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("queen", 10)

            assert result["success"] is True
            assert result["artist"] == "queen"
            assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_by_artist_music_section_not_found(
        self, mock_fastmcp, plex_client
    ):
        """Test artist search when music section is not found."""
        # Mock server with no music section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MusicSection(mock_fastmcp, plex_client)

        result = section.search_tracks_by_artist("Queen", 10)

        assert result["success"] is False
        assert "Music library not found" in result["error"]

    def test_search_tracks_by_artist_bad_request_error(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test artist search with bad request error."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Mock the search context to raise BadRequest
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.side_effect = BadRequest(
                "Invalid request"
            )
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Invalid", 10)

            assert result["success"] is False
            assert "Error searching tracks" in result["error"]

    def test_search_tracks_by_artist_value_error(
        self, mock_fastmcp, plex_client, mock_music_section
    ):
        """Test artist search with value error."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Mock the search context to raise ValueError
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.side_effect = ValueError(
                "Invalid value"
            )
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Invalid", 10)

            assert result["success"] is False
            assert "Error searching tracks" in result["error"]

    def test_format_track_results(self, mock_fastmcp, plex_client, mock_track):
        """Test the _format_track_results helper method."""
        section = MusicSection(mock_fastmcp, plex_client)

        result = section._format_track_results("Queen", [mock_track], ["Queen"])

        assert result["success"] is True
        assert result["artist"] == "Queen"
        assert result["matched_artists"] == ["Queen"]
        assert result["total_results"] == 1
        assert len(result["tracks"]) == 1
        assert result["tracks"][0]["title"] == "Test Song"
        assert result["tracks"][0]["artist"] == "Test Artist"
        assert result["tracks"][0]["album"] == "Test Album"
        assert result["tracks"][0]["rating_key"] == "67890"

    def test_format_track_results_multiple_tracks(self, mock_fastmcp, plex_client):
        """Test formatting multiple track results."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Create multiple mock tracks
        track1 = MagicMock()
        track1.title = "Song 1"
        track1.grandparentTitle = "Queen"
        track1.parentTitle = "Album 1"
        track1.year = 1975
        track1.ratingKey = "track1"

        track2 = MagicMock()
        track2.title = "Song 2"
        track2.grandparentTitle = "Queen"
        track2.parentTitle = "Album 2"
        track2.year = 1976
        track2.ratingKey = "track2"

        result = section._format_track_results("Queen", [track1, track2], ["Queen"])

        assert result["success"] is True
        assert result["artist"] == "Queen"
        assert result["total_results"] == 2
        assert len(result["tracks"]) == 2
        assert result["tracks"][0]["title"] == "Song 1"
        assert result["tracks"][1]["title"] == "Song 2"

    def test_normalize_artist_name_functionality(self, mock_fastmcp, plex_client):
        """Test the normalize_artist_name standalone function."""
        from plex_mcp.sections.artist_search_strategies import normalize_artist_name

        # Test en-dash to hyphen conversion
        result = normalize_artist_name("Static‐X")
        assert result == "Static-X"

        # Test em-dash to hyphen conversion
        result = normalize_artist_name("Static—X")
        assert result == "Static-X"

        # Test minus sign to hyphen conversion
        result = normalize_artist_name("Static−X")
        assert result == "Static-X"

        # Test figure dash to hyphen conversion
        result = normalize_artist_name("Static‒X")
        assert result == "Static-X"

        # Test no change needed
        result = normalize_artist_name("Static-X")
        assert result == "Static-X"

        # Test space normalization
        result = normalize_artist_name("Static  X")  # Multiple spaces
        assert result == "Static X"

        # Test Unicode normalization
        result = normalize_artist_name("Café")  # With accent
        # NFKD normalization decomposes the character
        import unicodedata

        expected = unicodedata.normalize("NFKD", "Café")
        assert result == expected

    @pytest.mark.parametrize(
        ("input_name", "expected_output"),
        [
            ("Static‐X", "Static-X"),  # en-dash
            ("Static—X", "Static-X"),  # em-dash
            ("Static−X", "Static-X"),  # minus sign
            ("Static‒X", "Static-X"),  # figure dash
            ("Static―X", "Static-X"),  # horizontal bar
            ("Static  X", "Static X"),  # multiple spaces
            ("Static\u00a0X", "Static X"),  # non-breaking space
            ("Static-X", "Static-X"),  # already correct
            ("Queen", "Queen"),  # no change needed
        ],
    )
    def test_normalize_artist_name_parametrized(
        self, mock_fastmcp, plex_client, input_name, expected_output
    ):
        """Test artist name normalization with various inputs."""
        from plex_mcp.sections.artist_search_strategies import normalize_artist_name

        result = normalize_artist_name(input_name)
        assert result == expected_output

    def test_strategy_context_initialization(self, mock_fastmcp, plex_client):
        """Test that ArtistSearchContext is properly initialized."""
        section = MusicSection(mock_fastmcp, plex_client)

        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": True,
                "tracks": [],
                "matched_artists": [],
            }
            mock_context_class.return_value = mock_context

            section.search_tracks_by_artist("Test", 10)

            # Verify ArtistSearchContext was called with correct parameters
            mock_context_class.assert_called_once()
            call_args = mock_context_class.call_args
            assert call_args[0][0] == plex_client.get_server()  # server

    def test_backward_compatibility(self, mock_fastmcp, plex_client, mock_track):
        """Test that the new implementation maintains backward compatibility."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Test that the method signature hasn't changed
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.return_value = {
                "success": True,
                "tracks": [mock_track],
                "matched_artists": ["Queen"],
            }
            mock_context_class.return_value = mock_context

            # Test with default limit
            result1 = section.search_tracks_by_artist("Queen")
            assert result1["success"] is True

            # Test with custom limit
            result2 = section.search_tracks_by_artist("Queen", 5)
            assert result2["success"] is True

            # Test with custom limit and different artist
            result3 = section.search_tracks_by_artist("Beatles", 15)
            assert result3["success"] is True

    def test_error_handling_consistency(self, mock_fastmcp, plex_client):
        """Test that error handling is consistent with the old implementation."""
        section = MusicSection(mock_fastmcp, plex_client)

        # Test NotFound error
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.side_effect = NotFound("Not found")
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Missing", 10)
            assert result["success"] is False
            assert "Music library not found" in result["error"]

        # Test BadRequest error
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.side_effect = BadRequest("Bad request")
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Invalid", 10)
            assert result["success"] is False
            assert "Error searching tracks" in result["error"]

        # Test ValueError
        with patch("plex_mcp.sections.music.ArtistSearchContext") as mock_context_class:
            mock_context = MagicMock()
            mock_context.search_tracks_by_artist.side_effect = ValueError(
                "Invalid value"
            )
            mock_context_class.return_value = mock_context

            result = section.search_tracks_by_artist("Invalid", 10)
            assert result["success"] is False
            assert "Error searching tracks" in result["error"]
