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

"""Tests for artist search strategies using the Strategy Pattern."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.artist_search_strategies import (
    ArtistSearchContext,
    ExactMatchStrategy,
    FuzzySearchStrategy,
    GlobalSearchStrategy,
    NormalizedMatchStrategy,
)


class TestExactMatchStrategy:
    """Test cases for ExactMatchStrategy."""

    def test_search_tracks_success(self, mock_track):
        """Test successful exact match search."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        strategy = ExactMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]
        mock_music_section.searchTracks.assert_called_once_with(
            filters={"artist.title": "Queen"}, limit=10
        )

    def test_search_tracks_no_results(self):
        """Test exact match search with no results."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = []

        strategy = ExactMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Unknown Artist", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_bad_request(self):
        """Test exact match search with bad request error."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.side_effect = BadRequest("Invalid query")

        strategy = ExactMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Invalid", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_not_found(self):
        """Test exact match search with not found error."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.side_effect = NotFound("Artist not found")

        strategy = ExactMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Missing", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []


class TestNormalizedMatchStrategy:
    """Test cases for NormalizedMatchStrategy."""

    def test_search_tracks_success_with_normalization(self, mock_track):
        """Test successful normalized match search."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        # Mock normalizer function
        def mock_normalizer(name):
            return name.replace("‐", "-")  # Replace en-dash with hyphen

        strategy = NormalizedMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Static‐X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static-X"]
        mock_music_section.searchTracks.assert_called_once_with(
            filters={"artist.title": "Static-X"}, limit=10
        )

    def test_search_tracks_no_normalization_needed(self, mock_track):
        """Test normalized match when no normalization is needed."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        def mock_normalizer(name):
            return name  # No change

        strategy = NormalizedMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Queen", 10)

        assert result["success"] is False  # Should not try normalized search
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_no_results(self):
        """Test normalized match search with no results."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = []

        def mock_normalizer(name):
            return name.replace("‐", "-")

        strategy = NormalizedMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Static‐X", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_bad_request(self):
        """Test normalized match search with bad request error."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.side_effect = BadRequest("Invalid query")

        def mock_normalizer(name):
            return name.replace("‐", "-")

        strategy = NormalizedMatchStrategy()
        result = strategy.search_tracks(mock_music_section, "Static‐X", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []


class TestGlobalSearchStrategy:
    """Test cases for GlobalSearchStrategy."""

    def test_search_tracks_success(self, mock_track):
        """Test successful global search strategy."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        # Mock server with global search results
        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Static‐X"  # Artist with en-dash
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name.replace("‐", "-")

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "Static-X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static‐X"]
        mock_server.search.assert_called_once_with("Static-X", limit=50)
        mock_music_section.searchTracks.assert_called_once_with(
            filters={"artist.title": "Static‐X"}, limit=10
        )

    def test_search_tracks_no_matching_artists(self):
        """Test global search with no matching artists."""
        mock_music_section = MagicMock()

        mock_server = MagicMock()
        mock_album = MagicMock()
        mock_album.type = "album"  # Not an artist
        mock_album.title = "Some Album"
        mock_server.search.return_value = [mock_album]

        def mock_normalizer(name):
            return name

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "Unknown", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_no_global_results(self):
        """Test global search with no results."""
        mock_music_section = MagicMock()

        mock_server = MagicMock()
        mock_server.search.return_value = []

        def mock_normalizer(name):
            return name

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "Unknown", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_bad_request(self):
        """Test global search with bad request error."""
        mock_music_section = MagicMock()

        mock_server = MagicMock()
        mock_server.search.side_effect = BadRequest("Invalid query")

        def mock_normalizer(name):
            return name

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "Invalid", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_case_insensitive_match(self, mock_track):
        """Test global search with case-insensitive matching."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Queen"  # Exact case match
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_normalized_match(self, mock_track):
        """Test global search with normalized matching."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Static‐X"  # With en-dash
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name.replace("‐", "-")

        strategy = GlobalSearchStrategy(mock_server)
        result = strategy.search_tracks(mock_music_section, "Static-X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static‐X"]


class TestFuzzySearchStrategy:
    """Test cases for FuzzySearchStrategy."""

    def test_search_tracks_success(self, mock_track):
        """Test successful fuzzy search."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Queen"
        mock_music_section.searchTracks.return_value = [mock_track]

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]
        mock_music_section.searchTracks.assert_called_once_with(title="Queen", limit=10)

    def test_search_tracks_no_matching_artists(self, mock_track):
        """Test fuzzy search with no matching artists."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Different Artist"
        mock_music_section.searchTracks.return_value = [mock_track]

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Queen", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_no_tracks(self):
        """Test fuzzy search with no tracks."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = []

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Unknown", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_search_tracks_case_insensitive_match(self, mock_track):
        """Test fuzzy search with case-insensitive matching."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Queen"
        mock_music_section.searchTracks.return_value = [mock_track]

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_normalized_match(self, mock_track):
        """Test fuzzy search with normalized matching."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Static‐X"  # With en-dash
        mock_music_section.searchTracks.return_value = [mock_track]

        def mock_normalizer(name):
            return name.replace("‐", "-")

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Static-X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static‐X"]

    def test_search_tracks_multiple_artists(self, mock_track):
        """Test fuzzy search with multiple matching artists."""
        mock_music_section = MagicMock()

        # Create multiple tracks with different artists
        track1 = MagicMock()
        track1.grandparentTitle = "Queen"
        track1.title = "Song 1"

        track2 = MagicMock()
        track2.grandparentTitle = "Queen"
        track2.title = "Song 2"

        track3 = MagicMock()
        track3.grandparentTitle = "Different Artist"
        track3.title = "Song 3"

        mock_music_section.searchTracks.return_value = [track1, track2, track3]

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert len(result["tracks"]) == 2  # Only Queen tracks
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_bad_request(self):
        """Test fuzzy search with bad request error."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.side_effect = BadRequest("Invalid query")

        def mock_normalizer(name):
            return name

        strategy = FuzzySearchStrategy()
        result = strategy.search_tracks(mock_music_section, "Invalid", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []


class TestArtistSearchContext:
    """Test cases for ArtistSearchContext."""

    def test_init(self):
        """Test ArtistSearchContext initialization."""
        mock_server = MagicMock()

        context = ArtistSearchContext(mock_server)

        assert context.server == mock_server
        assert len(context.strategies) == 4
        assert isinstance(context.strategies[0], ExactMatchStrategy)
        assert isinstance(context.strategies[1], NormalizedMatchStrategy)
        assert isinstance(context.strategies[2], GlobalSearchStrategy)
        assert isinstance(context.strategies[3], FuzzySearchStrategy)

    def test_search_tracks_by_artist_first_strategy_succeeds(self, mock_track):
        """Test search when first strategy succeeds."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        MagicMock()

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_by_artist_second_strategy_succeeds(self, mock_track):
        """Test search when second strategy succeeds."""
        mock_music_section = MagicMock()
        # First call returns empty, second call returns tracks
        mock_music_section.searchTracks.side_effect = [[], [mock_track]]

        mock_server = MagicMock()

        def mock_normalizer(name):
            return name.replace("‐", "-")

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Static‐X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static-X"]

    def test_search_tracks_by_artist_third_strategy_succeeds(self, mock_track):
        """Test search when third strategy succeeds."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Queen"
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_by_artist_fourth_strategy_succeeds(self, mock_track):
        """Test search when fourth strategy succeeds."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Queen"
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_server.search.return_value = []

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Queen"]

    def test_search_tracks_by_artist_all_strategies_fail(self):
        """Test search when all strategies fail."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.return_value = []

        mock_server = MagicMock()
        mock_server.search.return_value = []

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Unknown", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    @pytest.mark.parametrize(
        ("artist", "expected_success"),
        [
            ("Queen", True),
            ("Static‐X", True),  # With en-dash
            ("static-x", True),  # Lowercase
            ("Unknown Artist", False),
        ],
    )
    def test_search_tracks_by_artist_parametrized(
        self, mock_track, artist, expected_success
    ):
        """Test search with various artist names."""
        mock_music_section = MagicMock()

        if expected_success:
            # For successful cases, set up mocks to return results
            mock_track.grandparentTitle = "Queen" if "Queen" in artist else "Static‐X"
            mock_music_section.searchTracks.return_value = [mock_track]

            mock_server = MagicMock()
            mock_artist = MagicMock()
            mock_artist.type = "artist"
            mock_artist.title = "Queen" if "Queen" in artist else "Static‐X"
            mock_server.search.return_value = [mock_artist]
        else:
            # For failure cases, set up mocks to return no results
            mock_music_section.searchTracks.return_value = []
            mock_server = MagicMock()
            mock_server.search.return_value = []

        def mock_normalizer(name):
            return name.replace("‐", "-")

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, artist, 10)

        assert result["success"] == expected_success
        if expected_success:
            assert len(result["tracks"]) > 0
            assert len(result["matched_artists"]) > 0
        else:
            assert result["tracks"] == []
            assert result["matched_artists"] == []


class TestStrategyIntegration:
    """Integration tests for the complete strategy system."""

    def test_unicode_character_handling(self, mock_track):
        """Test handling of Unicode character differences."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Static‐X"  # With en-dash
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Static‐X"
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name.replace("‐", "-")

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Static-X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        # The matched artist should be the normalized version
        assert result["matched_artists"] == ["Static-X"]

    def test_case_insensitive_search(self, mock_track):
        """Test case-insensitive search functionality."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Queen"
        mock_music_section.searchTracks.return_value = [mock_track]

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Queen"
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "queen", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        # The ExactMatchStrategy returns the search term in matched_artists
        assert result["matched_artists"] == ["queen"]

    def test_strategy_fallback_behavior(self, mock_track):
        """Test that strategies fall back correctly when earlier ones fail."""
        mock_music_section = MagicMock()
        # First strategy fails (no exact match), second succeeds (normalized match)
        mock_music_section.searchTracks.side_effect = [[], [mock_track]]

        mock_server = MagicMock()

        def mock_normalizer(name):
            return name.replace("‐", "-")

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Static‐X", 10)

        assert result["success"] is True
        assert result["tracks"] == [mock_track]
        assert result["matched_artists"] == ["Static-X"]

    def test_error_handling_across_strategies(self):
        """Test error handling when all strategies encounter errors."""
        mock_music_section = MagicMock()
        mock_music_section.searchTracks.side_effect = BadRequest("Invalid query")

        mock_server = MagicMock()
        mock_server.search.side_effect = BadRequest("Invalid query")

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Invalid", 10)

        assert result["success"] is False
        assert result["tracks"] == []
        assert result["matched_artists"] == []

    def test_performance_with_large_datasets(self, mock_track):
        """Test performance characteristics with larger datasets."""
        mock_music_section = MagicMock()
        mock_track.grandparentTitle = "Queen"
        # Simulate multiple tracks
        tracks = [mock_track] * 50
        mock_music_section.searchTracks.return_value = tracks

        mock_server = MagicMock()
        mock_artist = MagicMock()
        mock_artist.type = "artist"
        mock_artist.title = "Queen"
        mock_server.search.return_value = [mock_artist]

        def mock_normalizer(name):
            return name

        context = ArtistSearchContext(mock_server)
        result = context.search_tracks_by_artist(mock_music_section, "Queen", 20)

        assert result["success"] is True
        assert len(result["tracks"]) == 50  # All tracks returned
        assert result["matched_artists"] == ["Queen"]
