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

"""Artist search strategies using the Strategy Pattern."""

import logging
import re
import unicodedata
from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Any

from plexapi.exceptions import BadRequest, NotFound

logger = logging.getLogger(__name__)


def normalize_artist_name(name: str) -> str:
    """
    Normalize artist name for better matching.

    This handles common Unicode character differences like:
    - Hyphens vs en-dashes vs em-dashes
    - Different types of spaces
    - Accented characters

    Parameters
    ----------
    name : str
        The artist name to normalize

    Returns
    -------
    str
        The normalized artist name
    """
    # Normalize Unicode characters
    normalized = unicodedata.normalize("NFKD", name)

    # Replace various dash types with standard hyphen
    dash_variants = [
        "‐",
        "–",
        "—",
        "−",
        "‒",
        "―",
    ]
    for dash in dash_variants:
        normalized = normalized.replace(dash, "-")

    # Replace various space types with standard space
    space_variants = [
        "\u00a0",
        "\u2000",
        "\u2001",
        "\u2002",
        "\u2003",
        "\u2004",
        "\u2005",
        "\u2006",
        "\u2007",
        "\u2008",
        "\u2009",
        "\u200a",
    ]
    for space in space_variants:
        normalized = normalized.replace(space, " ")

    # Remove extra whitespace
    return re.sub(r"\s+", " ", normalized).strip()


class ArtistSearchStrategy(ABC):
    """Abstract base class for artist search strategies."""

    @abstractmethod
    def search_tracks(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """
        Search for tracks by artist using this strategy.

        Parameters
        ----------
        music_section : Any
            The Plex music section
        artist : str
            The artist name to search for
        limit : int
            Maximum number of tracks to return

        Returns
        -------
        dict[str, Any]
            Search results with 'success', 'tracks', and 'matched_artists' keys
        """


class ExactMatchStrategy(ArtistSearchStrategy):
    """Strategy for exact artist name matching."""

    def search_tracks(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """Search using exact artist name match."""
        with suppress(BadRequest, NotFound):
            tracks = music_section.searchTracks(
                filters={"artist.title": artist}, limit=limit
            )
            if tracks:
                return {
                    "success": True,
                    "tracks": tracks,
                    "matched_artists": [artist],
                }

        return {"success": False, "tracks": [], "matched_artists": []}


class NormalizedMatchStrategy(ArtistSearchStrategy):
    """Strategy for normalized artist name matching."""

    def search_tracks(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """Search using normalized artist name match."""
        normalized_artist = normalize_artist_name(artist)
        if normalized_artist != artist:
            with suppress(BadRequest, NotFound):
                tracks = music_section.searchTracks(
                    filters={"artist.title": normalized_artist}, limit=limit
                )
                if tracks:
                    return {
                        "success": True,
                        "tracks": tracks,
                        "matched_artists": [normalized_artist],
                    }

        return {"success": False, "tracks": [], "matched_artists": []}


class GlobalSearchStrategy(ArtistSearchStrategy):
    """Strategy using global search to find artist, then targeted track search."""

    def __init__(self, server):
        """
        Initialize with server.

        Parameters
        ----------
        server : Any
            Plex server instance
        """
        self.server = server

    def search_tracks(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """Search using global search to find artist, then get tracks."""
        with suppress(BadRequest, NotFound):
            global_results = self.server.search(artist, limit=50)

            # Find matching artists from global search
            matching_artists = [
                item.title
                for item in global_results
                if (
                    hasattr(item, "type")
                    and item.type == "artist"
                    and item.title
                    and (
                        item.title.lower() == artist.lower()
                        or normalize_artist_name(item.title).lower()
                        == normalize_artist_name(artist).lower()
                    )
                )
            ]

            if matching_artists:
                # Get tracks for the first matching artist
                artist_name = matching_artists[0]
                tracks = music_section.searchTracks(
                    filters={"artist.title": artist_name}, limit=limit
                )
                if tracks:
                    return {
                        "success": True,
                        "tracks": tracks,
                        "matched_artists": [artist_name],
                    }

        return {"success": False, "tracks": [], "matched_artists": []}


class FuzzySearchStrategy(ArtistSearchStrategy):
    """Strategy for fuzzy artist name matching."""

    def __init__(self):
        """Initialize the fuzzy search strategy."""

    def search_tracks(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """Search using fuzzy matching with filtering."""
        with suppress(BadRequest, NotFound):
            # Use Plex's searchTracks with title parameter for fuzzy matching
            tracks = music_section.searchTracks(title=artist, limit=limit)
            if tracks:
                # Filter tracks to only include those by matching artists
                matching_tracks = []
                matched_artists = set()

                for track in tracks:
                    if track.grandparentTitle and (
                        track.grandparentTitle.lower() == artist.lower()
                        or normalize_artist_name(track.grandparentTitle).lower()
                        == normalize_artist_name(artist).lower()
                    ):
                        matching_tracks.append(track)
                        matched_artists.add(track.grandparentTitle)

                if matching_tracks:
                    return {
                        "success": True,
                        "tracks": matching_tracks,
                        "matched_artists": list(matched_artists),
                    }

        return {"success": False, "tracks": [], "matched_artists": []}


class ArtistSearchContext:
    """Context class that uses different search strategies."""

    def __init__(self, server):
        """
        Initialize the search context with strategies.

        Parameters
        ----------
        server : Any
            Plex server instance
        """
        self.server = server

        # Initialize strategies in order of preference
        self.strategies = [
            ExactMatchStrategy(),
            NormalizedMatchStrategy(),
            GlobalSearchStrategy(server),
            FuzzySearchStrategy(),
        ]

    def search_tracks_by_artist(
        self, music_section: Any, artist: str, limit: int
    ) -> dict[str, Any]:
        """
        Search for tracks by artist using multiple strategies.

        Parameters
        ----------
        music_section : Any
            The Plex music section
        artist : str
            The artist name to search for
        limit : int
            Maximum number of tracks to return

        Returns
        -------
        dict[str, Any]
            Search results with success status, tracks, and matched artists
        """
        for strategy in self.strategies:
            result = strategy.search_tracks(music_section, artist, limit)
            if result["success"]:
                logger.debug("Strategy %s succeeded", strategy.__class__.__name__)
                return result

        # If all strategies fail
        return {
            "success": False,
            "tracks": [],
            "matched_artists": [],
        }
