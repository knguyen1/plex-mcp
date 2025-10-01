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

"""Movies section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class MoviesSection:
    """Movies section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Movies section.

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
        """Register all movies-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(self.search_movies)
        self.mcp.tool(self.get_movies_library)
        self.mcp.tool(self.get_movie_info)
        self.mcp.tool(self.search_movies_by_genre)
        self.mcp.tool(self.search_movies_by_year)
        self.mcp.tool(self.get_recently_added_movies)
        self.mcp.tool(self.get_movies_by_rating)

    def _get_movies_section(self) -> Any:
        """
        Get the movies library section from Plex.

        Returns
        -------
        plexapi.library.MovieSection
            The movies library section

        Raises
        ------
        NotFound
            If no movies library is found on the server
        """
        server = self.plex_client.get_server()
        for section in server.library.sections():
            if section.TYPE == "movie":  # Movies sections have TYPE 'movie'
                return section
        msg = "No movies library found on this server"
        raise NotFound(msg)

    def search_movies(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for movies in the Plex library.

        Parameters
        ----------
        query : str
            The search query for movies
        limit : int, default=20
            Maximum number of movies to return
        **kwargs : Any
            Additional search parameters (genre, year, etc.)

        Returns
        -------
        dict[str, Any]
            Dictionary containing search results and movie information
        """
        try:
            movies_section = self._get_movies_section()
            movies = movies_section.searchMovies(title=query, limit=limit)

            results = [
                {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "summary": getattr(movie, "summary", None),
                    "rating": getattr(movie, "rating", None),
                    "duration": getattr(movie, "duration", None),
                    "rating_key": movie.ratingKey,
                    "thumb": getattr(movie, "thumb", None),
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                }
                for movie in movies
            ]

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "movies": results,
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching movies: %s")
            return {"success": False, "error": f"Error searching movies: {e}"}

    def get_movies_library(self) -> dict[str, Any]:
        """
        Get information about the movies library section.

        Returns
        -------
        dict[str, Any]
            Dictionary containing movies library information
        """
        try:
            movies_section = self._get_movies_section()
            return {
                "success": True,
                "library_info": {
                    "title": movies_section.title,
                    "type": movies_section.TYPE,
                    "key": movies_section.key,
                    "refreshing": getattr(movies_section, "refreshing", False),
                },
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting movies library: %s")
            return {"success": False, "error": f"Error getting movies library: {e}"}

    def get_movie_info(
        self,
        movie_rating_key: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific movie.

        Parameters
        ----------
        movie_rating_key : str
            The rating key of the movie

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed movie information
        """
        try:
            server = self.plex_client.get_server()
            movie = server.fetchItem(int(movie_rating_key))

            if not movie:
                return {
                    "success": False,
                    "error": f"Movie with rating key {movie_rating_key} not found",
                }

            # Get additional details
            genres = []
            if hasattr(movie, "genres"):
                genres.extend(genre.tag for genre in movie.genres)

            directors = []
            if hasattr(movie, "directors"):
                directors.extend(director.tag for director in movie.directors)

            actors = []
            if hasattr(movie, "actors"):
                actors.extend(actor.tag for actor in movie.actors)

            return {
                "success": True,
                "movie": {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "summary": getattr(movie, "summary", None),
                    "rating": getattr(movie, "rating", None),
                    "duration": getattr(movie, "duration", None),
                    "rating_key": movie.ratingKey,
                    "thumb": getattr(movie, "thumb", None),
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                    "viewed_at": getattr(movie, "viewedAt", None),
                    "genres": genres,
                    "directors": directors,
                    "actors": actors,
                    "studio": getattr(movie, "studio", None),
                    "content_rating": getattr(movie, "contentRating", None),
                },
            }

        except NotFound as e:
            logger.exception("Movie not found: %s")
            return {"success": False, "error": f"Movie not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting movie info: %s")
            return {"success": False, "error": f"Error getting movie info: {e}"}

    def search_movies_by_genre(
        self,
        genre: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for movies by genre.

        Parameters
        ----------
        genre : str
            The genre to search for
        limit : int, default=20
            Maximum number of movies to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing movies in the specified genre
        """
        try:
            movies_section = self._get_movies_section()
            movies = movies_section.searchMovies(genre=genre, limit=limit)

            results = [
                {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "summary": getattr(movie, "summary", None),
                    "rating": getattr(movie, "rating", None),
                    "rating_key": movie.ratingKey,
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                }
                for movie in movies
            ]

            return {
                "success": True,
                "genre": genre,
                "total_results": len(results),
                "movies": results,
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching movies by genre: %s")
            return {"success": False, "error": f"Error searching movies: {e}"}

    def search_movies_by_year(
        self,
        year: int | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for movies by year or year range.

        Parameters
        ----------
        year : int, optional
            Specific year to search for
        year_from : int, optional
            Start year for range search
        year_to : int, optional
            End year for range search
        limit : int, default=20
            Maximum number of movies to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing movies from the specified year(s)
        """
        try:
            movies_section = self._get_movies_section()

            if year is not None:
                movies = movies_section.searchMovies(year=year, limit=limit)
                search_desc = f"year {year}"
            elif year_from is not None and year_to is not None:
                # Use API filters for year range
                movies = movies_section.searchMovies(
                    filters={"year>>": year_from - 1, "year<<": year_to + 1},
                    limit=limit,
                )
                search_desc = f"years {year_from}-{year_to}"
            else:
                return {
                    "success": False,
                    "error": "Either 'year' or both 'year_from' and 'year_to' must be specified",
                }

            results = [
                {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "summary": getattr(movie, "summary", None),
                    "rating": getattr(movie, "rating", None),
                    "rating_key": movie.ratingKey,
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                }
                for movie in movies
            ]

            return {
                "success": True,
                "search_criteria": search_desc,
                "total_results": len(results),
                "movies": results,
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching movies by year: %s")
            return {"success": False, "error": f"Error searching movies: {e}"}

    def get_recently_added_movies(
        self,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get recently added movies.

        Parameters
        ----------
        limit : int, default=10
            Maximum number of movies to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing recently added movies
        """
        try:
            movies_section = self._get_movies_section()
            movies = movies_section.recentlyAdded(maxresults=limit)

            results = [
                {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "summary": getattr(movie, "summary", None),
                    "rating": getattr(movie, "rating", None),
                    "rating_key": movie.ratingKey,
                    "added_at": getattr(movie, "addedAt", None),
                    "thumb": getattr(movie, "thumb", None),
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                }
                for movie in movies
            ]

            return {
                "success": True,
                "total_results": len(results),
                "movies": results,
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting recently added movies: %s")
            return {
                "success": False,
                "error": f"Error getting recently added movies: {e}",
            }

    def get_movies_by_rating(
        self,
        min_rating: float | None = None,
        max_rating: float | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get movies filtered by rating.

        Parameters
        ----------
        min_rating : float, optional
            Minimum rating to filter by
        max_rating : float, optional
            Maximum rating to filter by
        limit : int, default=20
            Maximum number of movies to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing movies matching the rating criteria
        """
        try:
            movies_section = self._get_movies_section()

            # Build filters for rating
            filters = {}
            if min_rating is not None:
                filters["rating>>"] = min_rating - 0.1  # Greater than min_rating
            if max_rating is not None:
                filters["rating<<"] = max_rating + 0.1  # Less than max_rating

            # Search with filters
            if filters:
                filtered_movies = movies_section.searchMovies(
                    filters=filters, limit=limit
                )
            else:
                filtered_movies = movies_section.searchMovies(limit=limit)

            results = [
                {
                    "title": movie.title,
                    "year": getattr(movie, "year", None),
                    "rating": getattr(movie, "rating", None),
                    "summary": getattr(movie, "summary", None),
                    "rating_key": movie.ratingKey,
                    "viewed": getattr(movie, "viewedAt", None) is not None,
                }
                for movie in filtered_movies
            ]

            rating_desc = "all ratings"
            if min_rating is not None and max_rating is not None:
                rating_desc = f"rating {min_rating}-{max_rating}"
            elif min_rating is not None:
                rating_desc = f"rating >= {min_rating}"
            elif max_rating is not None:
                rating_desc = f"rating <= {max_rating}"

            return {
                "success": True,
                "rating_criteria": rating_desc,
                "total_results": len(results),
                "movies": results,
            }

        except NotFound as e:
            logger.exception("Movies library not found: %s")
            return {"success": False, "error": f"Movies library not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting movies by rating: %s")
            return {"success": False, "error": f"Error getting movies by rating: {e}"}
