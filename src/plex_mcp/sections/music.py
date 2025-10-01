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

"""Music section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient
from plex_mcp.sections.artist_search_strategies import (
    ArtistSearchContext,
)

logger = logging.getLogger(__name__)


class MusicSection:
    """Music section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Music section.

        Parameters
        ----------
        mcp : FastMCP
            The FastMCP instance to register tools with
        plex_client : PlexClient
            The Plex client for server interactions
        """
        self.mcp = mcp
        self.plex_client = plex_client
        self._register_tools()

    def _register_tools(self) -> None:
        """Register all music-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(
            self.search_music_tracks,
            name="search_music_tracks",
            description="Search for music tracks in the Plex library",
        )
        self.mcp.tool(
            self.get_music_library,
            name="get_music_library",
            description="Get information about the music library section",
        )
        self.mcp.tool(
            self.create_music_playlist,
            name="create_music_playlist",
            description="Create a new music playlist with specified tracks",
        )
        self.mcp.tool(
            self.get_random_tracks_by_decade,
            name="get_random_tracks_by_decade",
            description="Get random tracks from a specific decade",
        )
        self.mcp.tool(
            self.search_tracks_by_artist,
            name="search_tracks_by_artist",
            description="Search for tracks by a specific artist",
        )
        self.mcp.tool(
            self.get_playlist_info,
            name="get_playlist_info",
            description="Get information about an existing playlist",
        )
        self.mcp.tool(
            self.delete_playlist,
            name="delete_playlist",
            description="Delete an existing playlist",
        )

    def _get_music_section(self) -> Any:
        """
        Get the music library section from Plex.

        Returns
        -------
        plexapi.library.MusicSection
            The music library section

        Raises
        ------
        NotFound
            If no music library is found on the server
        """
        server = self.plex_client.get_server()
        for section in server.library.sections():
            if section.TYPE == "artist":  # Music sections have TYPE 'artist'
                return section
        msg = "No music library found on this server"
        raise NotFound(msg)

    def search_music_tracks(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for music tracks in the Plex library.

        Parameters
        ----------
        query : str
            The search query for tracks
        limit : int, default=20
            Maximum number of tracks to return
        **kwargs : Any
            Additional search parameters (genre, year, etc.)

        Returns
        -------
        dict[str, Any]
            Dictionary containing search results and track information
        """
        try:
            music_section = self._get_music_section()
            tracks = music_section.searchTracks(title=query, limit=limit)

            results = [
                {
                    "title": track.title,
                    "artist": track.grandparentTitle,
                    "album": track.parentTitle,
                    "year": getattr(track, "year", None),
                    "duration": getattr(track, "duration", None),
                    "rating_key": track.ratingKey,
                }
                for track in tracks
            ]

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "tracks": results,
            }

        except NotFound as e:
            logger.exception("Music library not found: %s")
            return {"success": False, "error": f"Music library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching music tracks: %s")
            return {"success": False, "error": f"Error searching tracks: {e}"}

    def get_music_library(self) -> dict[str, Any]:
        """
        Get information about the music library section.

        Returns
        -------
        dict[str, Any]
            Dictionary containing music library information
        """
        try:
            music_section = self._get_music_section()
            return {
                "success": True,
                "library_info": {
                    "title": music_section.title,
                    "type": music_section.TYPE,
                    "key": music_section.key,
                    "refreshing": getattr(music_section, "refreshing", False),
                },
            }

        except NotFound as e:
            logger.exception("Music library not found: %s")
            return {"success": False, "error": f"Music library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting music library: %s")
            return {"success": False, "error": f"Error getting music library: {e}"}

    def create_music_playlist(
        self,
        title: str,
        track_rating_keys: list[str],
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a new music playlist with specified tracks.

        Parameters
        ----------
        title : str
            The title of the playlist
        track_rating_keys : list[str]
            List of rating keys for tracks to include in the playlist
        description : str, optional
            Optional description for the playlist

        Returns
        -------
        dict[str, Any]
            Dictionary containing playlist creation results
        """
        try:
            server = self.plex_client.get_server()
            music_section = self._get_music_section()

            # Get tracks by rating keys
            tracks = []
            for rating_key in track_rating_keys:
                try:
                    track = music_section.fetchItem(int(rating_key))
                    if track:
                        tracks.append(track)
                except NotFound:
                    logger.warning("Track with rating key %s not found", rating_key)
                    continue

            if not tracks:
                return {
                    "success": False,
                    "error": "No valid tracks found for the playlist",
                }

            # Check if playlist already exists and delete it
            try:
                existing_playlists = server.playlists(title=title)
                for playlist in existing_playlists:
                    logger.info("Deleting existing playlist: %s", playlist.title)
                    playlist.delete()
            except (NotFound, IndexError):
                pass  # Playlist doesn't exist, which is fine

            # Create new playlist
            playlist = server.createPlaylist(title=title, items=tracks)

            return {
                "success": True,
                "playlist": {
                    "title": playlist.title,
                    "rating_key": playlist.ratingKey,
                    "track_count": len(playlist.items()),
                    "url": getattr(playlist, "_getWebURL", lambda: "")(),
                },
            }

        except BadRequest as e:
            logger.exception("Bad request creating playlist: %s")
            return {"success": False, "error": f"Bad request: {e}"}
        except (NotFound, ValueError) as e:
            logger.exception("Error creating playlist: %s")
            return {"success": False, "error": f"Error creating playlist: {e}"}

    def get_random_tracks_by_decade(
        self,
        decade: int,
        count: int = 3,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get random tracks from a specific decade.

        Parameters
        ----------
        decade : int
            The decade to search for (e.g., 1990 for 1990s)
        count : int, default=3
            Number of random tracks to return
        limit : int, default=50
            Maximum number of tracks to search through for randomization

        Returns
        -------
        dict[str, Any]
            Dictionary containing random tracks from the specified decade
        """
        try:
            music_section = self._get_music_section()
            tracks = music_section.searchTracks(decade=decade, limit=limit)

            if not tracks:
                return {
                    "success": False,
                    "error": f"No tracks found from the {decade}s",
                }

            # Get random tracks
            import random

            random_tracks = random.sample(tracks, min(count, len(tracks)))

            results = [
                {
                    "title": track.title,
                    "artist": track.grandparentTitle,
                    "album": track.parentTitle,
                    "year": getattr(track, "year", None),
                    "rating_key": track.ratingKey,
                }
                for track in random_tracks
            ]

            return {
                "success": True,
                "decade": decade,
                "requested_count": count,
                "actual_count": len(results),
                "tracks": results,
            }

        except NotFound as e:
            logger.exception("Music library not found: %s")
            return {"success": False, "error": f"Music library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting random tracks: %s")
            return {"success": False, "error": f"Error getting random tracks: {e}"}

    def search_tracks_by_artist(
        self,
        artist: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for tracks by a specific artist.

        This method uses the Strategy pattern to handle Unicode character
        differences like hyphens vs en-dashes, different space types, and case variations.

        Parameters
        ----------
        artist : str
            The artist name to search for
        limit : int, default=20
            Maximum number of tracks to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing tracks by the specified artist
        """
        try:
            music_section = self._get_music_section()
            server = self.plex_client.get_server()

            # Create search context with strategies
            search_context = ArtistSearchContext(server)

            # Use strategy pattern to search for tracks
            result = search_context.search_tracks_by_artist(
                music_section, artist, limit
            )

            if result["success"]:
                result = self._format_track_results(
                    artist, result["tracks"], result["matched_artists"]
                )
            else:
                result = {
                    "success": False,
                    "error": f"No artists found matching '{artist}'",
                }

        except NotFound as e:
            logger.exception("Music library not found: %s")
            return {"success": False, "error": f"Music library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching tracks by artist: %s")
            return {"success": False, "error": f"Error searching tracks: {e}"}
        else:
            return result

    def _format_track_results(
        self, search_artist: str, tracks: list, matched_artists: list
    ) -> dict[str, Any]:
        """
        Format track search results into the expected response format.

        Parameters
        ----------
        search_artist : str
            The original artist name that was searched for
        tracks : list
            List of track objects from Plex
        matched_artists : list
            List of artist names that matched the search

        Returns
        -------
        dict[str, Any]
            Formatted search results
        """
        results = [
            {
                "title": track.title,
                "artist": track.grandparentTitle,
                "album": track.parentTitle,
                "year": getattr(track, "year", None),
                "rating_key": track.ratingKey,
            }
            for track in tracks
        ]

        return {
            "success": True,
            "artist": search_artist,
            "matched_artists": matched_artists,
            "total_results": len(results),
            "tracks": results,
        }

    def get_playlist_info(
        self,
        playlist_title: str,
    ) -> dict[str, Any]:
        """
        Get information about an existing playlist.

        Parameters
        ----------
        playlist_title : str
            The title of the playlist to get information for

        Returns
        -------
        dict[str, Any]
            Dictionary containing playlist information
        """
        try:
            server = self.plex_client.get_server()
            playlists = server.playlists(title=playlist_title)

            if not playlists:
                return {
                    "success": False,
                    "error": f"Playlist '{playlist_title}' not found",
                }

            playlist = playlists[0]  # Get first matching playlist
            tracks = playlist.items()

            track_list = [
                {
                    "title": track.title,
                    "artist": track.grandparentTitle,
                    "album": track.parentTitle,
                    "rating_key": track.ratingKey,
                }
                for track in tracks
            ]

            result = {
                "success": True,
                "playlist": {
                    "title": playlist.title,
                    "rating_key": playlist.ratingKey,
                    "track_count": len(track_list),
                    "url": getattr(playlist, "_getWebURL", lambda: "")(),
                    "tracks": track_list,
                },
            }
        except (NotFound, BadRequest, ValueError) as e:
            logger.exception("Error getting playlist info: %s")
            return {"success": False, "error": f"Error getting playlist info: {e}"}
        else:
            return result

    def delete_playlist(
        self,
        playlist_title: str,
    ) -> dict[str, Any]:
        """
        Delete an existing playlist.

        Parameters
        ----------
        playlist_title : str
            The title of the playlist to delete

        Returns
        -------
        dict[str, Any]
            Dictionary containing deletion results
        """
        try:
            server = self.plex_client.get_server()
            playlists = server.playlists(title=playlist_title)

            if not playlists:
                return {
                    "success": False,
                    "error": f"Playlist '{playlist_title}' not found",
                }

            deleted_count = 0
            for playlist in playlists:
                playlist.delete()
                deleted_count += 1
        except (NotFound, BadRequest, ValueError) as e:
            logger.exception("Error deleting playlist: %s")
            return {"success": False, "error": f"Error deleting playlist: {e}"}
        else:
            return {
                "success": True,
                "message": f"Deleted {deleted_count} playlist(s) with title '{playlist_title}'",
            }
