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

"""Advanced Search section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class AdvancedSearchSection:
    """Advanced Search section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Advanced Search section.

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
        """Register all advanced search-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(
            self.global_search,
            name="global_search",
            description="Search across all library sections for content",
        )
        self.mcp.tool(
            self.advanced_search,
            name="advanced_search",
            description="Perform advanced search with filters and sorting",
        )
        self.mcp.tool(
            self.search_by_year,
            name="search_by_year",
            description="Search for content by year or year range",
        )
        self.mcp.tool(
            self.search_by_genre,
            name="search_by_genre",
            description="Search for content by genre",
        )
        self.mcp.tool(
            self.search_by_rating,
            name="search_by_rating",
            description="Search for content by rating",
        )
        self.mcp.tool(
            self.search_by_duration,
            name="search_by_duration",
            description="Search for content by duration range",
        )
        self.mcp.tool(
            self.search_by_keyword,
            name="search_by_keyword",
            description="Search for content by keyword in title, summary, or tags",
        )
        self.mcp.tool(
            self.get_search_suggestions,
            name="get_search_suggestions",
            description="Get search suggestions based on partial input",
        )

    def global_search(
        self,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search across all library sections for content.

        Parameters
        ----------
        query : str
            The search query
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing global search results
        """
        try:
            server = self.plex_client.get_server()
            results = server.search(query, limit=limit)

            # Organize results by type
            organized_results = {
                "movies": [],
                "shows": [],
                "episodes": [],
                "artists": [],
                "albums": [],
                "tracks": [],
                "photos": [],
                "other": [],
            }

            for item in results:
                item_type = getattr(item, "type", "other")
                item_data = {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "summary": getattr(item, "summary", None),
                    "year": getattr(item, "year", None),
                    "library_section_title": getattr(item, "librarySectionTitle", None),
                }

                if item_type in organized_results:
                    organized_results[item_type].append(item_data)
                else:
                    organized_results["other"].append(item_data)

            result = {
                "success": True,
                "query": query,
                "total_results": len(results),
                "results_by_type": organized_results,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error performing global search: %s")
            return {"success": False, "error": f"Error performing global search: {e}"}
        else:
            return result

    def advanced_search(
        self,
        section_title: str,
        filters: dict[str, Any] | None = None,
        sort: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Perform advanced search with filters and sorting.

        Parameters
        ----------
        section_title : str
            The title of the library section
        filters : dict[str, Any], optional
            Advanced filters to apply
        sort : str, optional
            Sort order for results
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing advanced search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Build search parameters
            search_params = {"limit": limit}
            if filters:
                search_params.update(filters)
            if sort:
                search_params["sort"] = sort

            results = section.search(**search_params)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "summary": getattr(item, "summary", None),
                    "year": getattr(item, "year", None),
                    "type": getattr(item, "type", None),
                    "added_at": getattr(item, "addedAt", None),
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "filters_applied": filters,
                "sort_applied": sort,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error performing advanced search: %s")
            return {"success": False, "error": f"Error performing advanced search: {e}"}
        else:
            return result

    def search_by_year(
        self,
        section_title: str,
        year: int | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for content by year or year range.

        Parameters
        ----------
        section_title : str
            The title of the library section
        year : int, optional
            Specific year to search for
        year_from : int, optional
            Start year for range search
        year_to : int, optional
            End year for range search
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing year-based search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Build year filter
            if year:
                year_filter = {"year": year}
            elif year_from and year_to:
                year_filter = {"year__gte": year_from, "year__lte": year_to}
            elif year_from:
                year_filter = {"year__gte": year_from}
            elif year_to:
                year_filter = {"year__lte": year_to}
            else:
                return {
                    "success": False,
                    "error": "Either 'year' or ('year_from' and/or 'year_to') must be provided",
                }

            results = section.search(limit=limit, **year_filter)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "year": getattr(item, "year", None),
                    "type": getattr(item, "type", None),
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "year_filter": year_filter,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching by year: %s")
            return {"success": False, "error": f"Error searching by year: {e}"}
        else:
            return result

    def search_by_genre(
        self,
        section_title: str,
        genre: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for content by genre.

        Parameters
        ----------
        section_title : str
            The title of the library section
        genre : str
            The genre to search for
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing genre-based search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            results = section.search(limit=limit, genre=genre)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "year": getattr(item, "year", None),
                    "type": getattr(item, "type", None),
                    "genres": [genre.title for genre in getattr(item, "genres", [])],
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "genre": genre,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching by genre: %s")
            return {"success": False, "error": f"Error searching by genre: {e}"}
        else:
            return result

    def search_by_rating(
        self,
        section_title: str,
        min_rating: float | None = None,
        max_rating: float | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for content by rating.

        Parameters
        ----------
        section_title : str
            The title of the library section
        min_rating : float, optional
            Minimum rating to search for
        max_rating : float, optional
            Maximum rating to search for
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing rating-based search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Build rating filter
            rating_filter = {}
            if min_rating is not None:
                rating_filter["userRating__gte"] = min_rating
            if max_rating is not None:
                rating_filter["userRating__lte"] = max_rating

            if not rating_filter:
                return {
                    "success": False,
                    "error": "Either 'min_rating' or 'max_rating' must be provided",
                }

            results = section.search(limit=limit, **rating_filter)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "user_rating": getattr(item, "userRating", None),
                    "audience_rating": getattr(item, "audienceRating", None),
                    "type": getattr(item, "type", None),
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "rating_filter": rating_filter,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching by rating: %s")
            return {"success": False, "error": f"Error searching by rating: {e}"}
        else:
            return result

    def search_by_duration(
        self,
        section_title: str,
        min_duration: int | None = None,
        max_duration: int | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for content by duration range.

        Parameters
        ----------
        section_title : str
            The title of the library section
        min_duration : int, optional
            Minimum duration in minutes
        max_duration : int, optional
            Maximum duration in minutes
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing duration-based search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Build duration filter
            duration_filter = {}
            if min_duration is not None:
                duration_filter["duration__gte"] = (
                    min_duration * 60000
                )  # Convert to milliseconds
            if max_duration is not None:
                duration_filter["duration__lte"] = (
                    max_duration * 60000
                )  # Convert to milliseconds

            if not duration_filter:
                return {
                    "success": False,
                    "error": "Either 'min_duration' or 'max_duration' must be provided",
                }

            results = section.search(limit=limit, **duration_filter)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "duration": getattr(item, "duration", None),
                    "type": getattr(item, "type", None),
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "duration_filter": duration_filter,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching by duration: %s")
            return {"success": False, "error": f"Error searching by duration: {e}"}
        else:
            return result

    def search_by_keyword(
        self,
        section_title: str,
        keyword: str,
        search_fields: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for content by keyword in title, summary, or tags.

        Parameters
        ----------
        section_title : str
            The title of the library section
        keyword : str
            The keyword to search for
        search_fields : list[str], optional
            Fields to search in (title, summary, tags)
        limit : int, default=20
            Maximum number of results to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing keyword-based search results
        """
        try:
            server = self.plex_client.get_server()
            section = server.library.section(section_title)

            # Default search fields
            if search_fields is None:
                search_fields = ["title", "summary"]

            # Build search parameters
            search_params = {"limit": limit}
            for field in search_fields:
                search_params[f"{field}__icontains"] = keyword

            results = section.search(**search_params)

            organized_results = [
                {
                    "title": item.title,
                    "rating_key": item.ratingKey,
                    "thumb": getattr(item, "thumb", None),
                    "summary": getattr(item, "summary", None),
                    "type": getattr(item, "type", None),
                    "matched_fields": [
                        field
                        for field in search_fields
                        if keyword.lower() in getattr(item, field, "").lower()
                    ],
                }
                for item in results
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "keyword": keyword,
                "search_fields": search_fields,
                "total_results": len(organized_results),
                "results": organized_results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching by keyword: %s")
            return {"success": False, "error": f"Error searching by keyword: {e}"}
        else:
            return result

    def get_search_suggestions(
        self,
        partial_query: str,
        limit: int = 10,
    ) -> dict[str, Any]:
        """
        Get search suggestions based on partial input.

        Parameters
        ----------
        partial_query : str
            Partial search query
        limit : int, default=10
            Maximum number of suggestions to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing search suggestions
        """
        try:
            server = self.plex_client.get_server()

            # Get suggestions from server
            suggestions = server.search(partial_query, limit=limit)

            # Extract unique titles as suggestions
            unique_suggestions = []
            seen_titles = set()

            for item in suggestions:
                title = item.title
                if title not in seen_titles:
                    unique_suggestions.append({
                        "title": title,
                        "type": getattr(item, "type", None),
                        "library_section": getattr(item, "librarySectionTitle", None),
                    })
                    seen_titles.add(title)

                    if len(unique_suggestions) >= limit:
                        break

            result = {
                "success": True,
                "partial_query": partial_query,
                "total_suggestions": len(unique_suggestions),
                "suggestions": unique_suggestions,
            }

        except (BadRequest, ValueError) as e:
            logger.exception("Error getting search suggestions: %s")
            return {"success": False, "error": f"Error getting search suggestions: {e}"}
        else:
            return result
