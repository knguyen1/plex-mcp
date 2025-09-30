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

"""TV Shows section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class TVShowsSection:
    """TV Shows section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the TV Shows section.

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
        """Register all TV shows-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(
            self.search_tv_shows,
            name="search_tv_shows",
            description="Search for TV shows in the Plex library",
        )
        self.mcp.tool(
            self.get_tv_shows_library,
            name="get_tv_shows_library",
            description="Get information about the TV shows library section",
        )
        self.mcp.tool(
            self.get_show_episodes,
            name="get_show_episodes",
            description="Get episodes for a specific TV show",
        )
        self.mcp.tool(
            self.get_episode_info,
            name="get_episode_info",
            description="Get detailed information about a specific episode",
        )
        self.mcp.tool(
            self.search_episodes_by_show,
            name="search_episodes_by_show",
            description="Search for episodes within a specific TV show",
        )
        self.mcp.tool(
            self.get_recently_added_shows,
            name="get_recently_added_shows",
            description="Get recently added TV shows",
        )

    def _get_tv_shows_section(self) -> Any:
        """
        Get the TV shows library section from Plex.

        Returns
        -------
        plexapi.library.ShowSection
            The TV shows library section

        Raises
        ------
        NotFound
            If no TV shows library is found on the server
        """
        server = self.plex_client.get_server()
        for section in server.library.sections():
            if section.TYPE == "show":  # TV shows sections have TYPE 'show'
                return section
        msg = "No TV shows library found on this server"
        raise NotFound(msg)

    def search_tv_shows(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for TV shows in the Plex library.

        Parameters
        ----------
        query : str
            The search query for TV shows
        limit : int, default=20
            Maximum number of shows to return
        **kwargs : Any
            Additional search parameters (genre, year, etc.)

        Returns
        -------
        dict[str, Any]
            Dictionary containing search results and show information
        """
        try:
            tv_section = self._get_tv_shows_section()
            shows = tv_section.searchShows(title=query, limit=limit)

            results = [
                {
                    "title": show.title,
                    "year": getattr(show, "year", None),
                    "summary": getattr(show, "summary", None),
                    "rating": getattr(show, "rating", None),
                    "rating_key": show.ratingKey,
                    "thumb": getattr(show, "thumb", None),
                }
                for show in shows
            ]

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "shows": results,
            }

        except NotFound as e:
            logger.exception("TV shows library not found: %s")
            return {"success": False, "error": f"TV shows library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching TV shows: %s")
            return {"success": False, "error": f"Error searching shows: {e}"}

    def get_tv_shows_library(self) -> dict[str, Any]:
        """
        Get information about the TV shows library section.

        Returns
        -------
        dict[str, Any]
            Dictionary containing TV shows library information
        """
        try:
            tv_section = self._get_tv_shows_section()
            return {
                "success": True,
                "library_info": {
                    "title": tv_section.title,
                    "type": tv_section.TYPE,
                    "key": tv_section.key,
                    "refreshing": getattr(tv_section, "refreshing", False),
                },
            }

        except NotFound as e:
            logger.exception("TV shows library not found: %s")
            return {"success": False, "error": f"TV shows library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting TV shows library: %s")
            return {"success": False, "error": f"Error getting TV shows library: {e}"}

    def get_show_episodes(
        self,
        show_rating_key: str,
        season: int | None = None,
    ) -> dict[str, Any]:
        """
        Get episodes for a specific TV show.

        Parameters
        ----------
        show_rating_key : str
            The rating key of the TV show
        season : int, optional
            Specific season number to get episodes for

        Returns
        -------
        dict[str, Any]
            Dictionary containing episodes information
        """
        try:
            tv_section = self._get_tv_shows_section()
            show = tv_section.fetchItem(int(show_rating_key))

            if not show:
                return {
                    "success": False,
                    "error": f"TV show with rating key {show_rating_key} not found",
                }

            episodes = []
            if season is not None:
                # Get episodes for specific season
                try:
                    season_obj = show.season(season)
                    episodes.extend([
                        {
                            "title": episode.title,
                            "season": episode.seasonNumber,
                            "episode": episode.episodeNumber,
                            "summary": getattr(episode, "summary", None),
                            "duration": getattr(episode, "duration", None),
                            "rating_key": episode.ratingKey,
                            "viewed": getattr(episode, "viewedAt", None) is not None,
                        }
                        for episode in season_obj.episodes()
                    ])
                except NotFound:
                    return {
                        "success": False,
                        "error": f"Season {season} not found for show {show.title}",
                    }
            else:
                # Get all episodes
                for season_obj in show.seasons():
                    episodes.extend([
                        {
                            "title": episode.title,
                            "season": episode.seasonNumber,
                            "episode": episode.episodeNumber,
                            "summary": getattr(episode, "summary", None),
                            "duration": getattr(episode, "duration", None),
                            "rating_key": episode.ratingKey,
                            "viewed": getattr(episode, "viewedAt", None) is not None,
                        }
                        for episode in season_obj.episodes()
                    ])

            return {
                "success": True,
                "show_title": show.title,
                "season": season,
                "total_episodes": len(episodes),
                "episodes": episodes,
            }

        except NotFound as e:
            logger.exception("TV show not found: %s")
            return {"success": False, "error": f"TV show not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting show episodes: %s")
            return {"success": False, "error": f"Error getting episodes: {e}"}

    def get_episode_info(
        self,
        episode_rating_key: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific episode.

        Parameters
        ----------
        episode_rating_key : str
            The rating key of the episode

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed episode information
        """
        try:
            server = self.plex_client.get_server()
            episode = server.fetchItem(int(episode_rating_key))

            if not episode:
                return {
                    "success": False,
                    "error": f"Episode with rating key {episode_rating_key} not found",
                }

            return {
                "success": True,
                "episode": {
                    "title": episode.title,
                    "show_title": episode.grandparentTitle,
                    "season": episode.seasonNumber,
                    "episode": episode.episodeNumber,
                    "summary": getattr(episode, "summary", None),
                    "duration": getattr(episode, "duration", None),
                    "rating": getattr(episode, "rating", None),
                    "rating_key": episode.ratingKey,
                    "viewed": getattr(episode, "viewedAt", None) is not None,
                    "viewed_at": getattr(episode, "viewedAt", None),
                    "thumb": getattr(episode, "thumb", None),
                },
            }

        except NotFound as e:
            logger.exception("Episode not found: %s")
            return {"success": False, "error": f"Episode not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting episode info: %s")
            return {"success": False, "error": f"Error getting episode info: {e}"}

    def search_episodes_by_show(
        self,
        show_title: str,
        query: str = "",
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for episodes within a specific TV show.

        Parameters
        ----------
        show_title : str
            The title of the TV show to search within
        query : str, default=""
            Additional search query for episodes
        limit : int, default=20
            Maximum number of episodes to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing matching episodes
        """
        try:
            tv_section = self._get_tv_shows_section()
            shows = tv_section.searchShows(title=show_title)

            if not shows:
                return {
                    "success": False,
                    "error": f"TV show '{show_title}' not found",
                }

            show = shows[0]  # Get first matching show
            episodes = []

            for season in show.seasons():
                episodes.extend([
                    {
                        "title": episode.title,
                        "season": episode.seasonNumber,
                        "episode": episode.episodeNumber,
                        "summary": getattr(episode, "summary", None),
                        "rating_key": episode.ratingKey,
                        "viewed": getattr(episode, "viewedAt", None) is not None,
                    }
                    for episode in season.episodes()
                    if not query or query.lower() in episode.title.lower()
                ])

            # Limit results
            episodes = episodes[:limit]

            return {
                "success": True,
                "show_title": show.title,
                "query": query,
                "total_results": len(episodes),
                "episodes": episodes,
            }

        except NotFound as e:
            logger.exception("TV show not found: %s")
            return {"success": False, "error": f"TV show not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching episodes: %s")
            return {"success": False, "error": f"Error searching episodes: {e}"}

    def get_recently_added_shows(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get recently added TV shows.

        Parameters
        ----------
        limit : int, default=10
            Maximum number of shows to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing recently added shows
        """
        try:
            tv_section = self._get_tv_shows_section()
            shows = tv_section.recentlyAdded(maxresults=limit)

            results = [
                {
                    "title": show.title,
                    "year": getattr(show, "year", None),
                    "summary": getattr(show, "summary", None),
                    "rating": getattr(show, "rating", None),
                    "rating_key": show.ratingKey,
                    "added_at": getattr(show, "addedAt", None),
                    "thumb": getattr(show, "thumb", None),
                }
                for show in shows
            ]

            return {
                "success": True,
                "total_results": len(results),
                "shows": results,
            }

        except NotFound as e:
            logger.exception("TV shows library not found: %s")
            return {"success": False, "error": f"TV shows library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting recently added shows: %s")
            return {
                "success": False,
                "error": f"Error getting recently added shows: {e}",
            }
