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

"""Tests for AdvancedSearchSection class."""

from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.advanced_search import AdvancedSearchSection


class TestAdvancedSearchSection:
    """Test cases for AdvancedSearchSection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test AdvancedSearchSection initialization."""
        section = AdvancedSearchSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 8

    def test_global_search_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_search_results: list[MagicMock],
    ) -> None:
        """Test successful global search."""
        mock_server = MagicMock()
        mock_server.search.return_value = mock_search_results

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.global_search("test query", limit=10)

        assert result["success"] is True
        assert result["query"] == "test query"
        assert result["total_results"] == len(mock_search_results)
        assert "results_by_type" in result
        mock_server.search.assert_called_once_with("test query", limit=10)

    def test_global_search_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test global search with error."""
        mock_server = MagicMock()
        mock_server.search.side_effect = BadRequest("Search error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.global_search("test query")

        assert result["success"] is False
        assert "Error performing global search" in result["error"]

    def test_advanced_search_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful advanced search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        filters = {"year": 2020, "genre": "Action"}
        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.advanced_search(
                "Movies", filters=filters, sort="title", limit=10
            )

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["filters_applied"] == filters
        assert result["sort_applied"] == "title"
        assert result["total_results"] == len(mock_movies)
        mock_movies_section.search.assert_called_once_with(
            limit=10, year=2020, genre="Action", sort="title"
        )

    def test_advanced_search_section_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test advanced search with section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.advanced_search("Movies")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_search_by_year_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful year-based search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_year("Movies", year=2020, limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["year_filter"] == {"year": 2020}
        assert result["total_results"] == len(mock_movies)
        mock_movies_section.search.assert_called_once_with(limit=10, year=2020)

    def test_search_by_year_range_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful year range search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_year(
                "Movies", year_from=2010, year_to=2020, limit=10
            )

        assert result["success"] is True
        assert result["year_filter"] == {"year__gte": 2010, "year__lte": 2020}
        mock_movies_section.search.assert_called_once_with(
            limit=10, year__gte=2010, year__lte=2020
        )

    def test_search_by_year_no_parameters(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test year search with no parameters."""
        section = AdvancedSearchSection(mock_fastmcp, plex_client)
        result = section.search_by_year("Movies")

        assert result["success"] is False
        assert (
            "Either 'year' or ('year_from' and/or 'year_to') must be provided"
            in result["error"]
        )

    def test_search_by_genre_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful genre-based search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_genre("Movies", "Action", limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["genre"] == "Action"
        assert result["total_results"] == len(mock_movies)
        mock_movies_section.search.assert_called_once_with(limit=10, genre="Action")

    def test_search_by_rating_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful rating-based search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_rating(
                "Movies", min_rating=8.0, max_rating=10.0, limit=10
            )

        assert result["success"] is True
        assert result["rating_filter"] == {
            "userRating__gte": 8.0,
            "userRating__lte": 10.0,
        }
        mock_movies_section.search.assert_called_once_with(
            limit=10, userRating__gte=8.0, userRating__lte=10.0
        )

    def test_search_by_rating_no_parameters(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test rating search with no parameters."""
        section = AdvancedSearchSection(mock_fastmcp, plex_client)
        result = section.search_by_rating("Movies")

        assert result["success"] is False
        assert "Either 'min_rating' or 'max_rating' must be provided" in result["error"]

    def test_search_by_duration_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful duration-based search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_duration(
                "Movies", min_duration=90, max_duration=120, limit=10
            )

        assert result["success"] is True
        assert result["duration_filter"] == {
            "duration__gte": 5400000,
            "duration__lte": 7200000,
        }
        mock_movies_section.search.assert_called_once_with(
            limit=10, duration__gte=5400000, duration__lte=7200000
        )

    def test_search_by_duration_no_parameters(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test duration search with no parameters."""
        section = AdvancedSearchSection(mock_fastmcp, plex_client)
        result = section.search_by_duration("Movies")

        assert result["success"] is False
        assert (
            "Either 'min_duration' or 'max_duration' must be provided"
            in result["error"]
        )

    def test_search_by_keyword_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test successful keyword-based search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_keyword(
                "Movies", "action", ["title", "summary"], limit=10
            )

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["keyword"] == "action"
        assert result["search_fields"] == ["title", "summary"]
        assert result["total_results"] == len(mock_movies)
        mock_movies_section.search.assert_called_once_with(
            limit=10, title__icontains="action", summary__icontains="action"
        )

    def test_search_by_keyword_default_fields(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_movies: list[MagicMock],
    ) -> None:
        """Test keyword search with default fields."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.search.return_value = mock_movies

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.search_by_keyword("Movies", "action", limit=10)

        assert result["success"] is True
        assert result["search_fields"] == ["title", "summary"]
        mock_movies_section.search.assert_called_once_with(
            limit=10, title__icontains="action", summary__icontains="action"
        )

    def test_get_search_suggestions_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_search_results: list[MagicMock],
    ) -> None:
        """Test successful search suggestions."""
        mock_server = MagicMock()
        mock_server.search.return_value = mock_search_results

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.get_search_suggestions("test", limit=5)

        assert result["success"] is True
        assert result["partial_query"] == "test"
        assert result["total_suggestions"] <= 5
        assert "suggestions" in result
        mock_server.search.assert_called_once_with("test", limit=5)

    def test_get_search_suggestions_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test search suggestions with error."""
        mock_server = MagicMock()
        mock_server.search.side_effect = BadRequest("Search error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = AdvancedSearchSection(mock_fastmcp, plex_client)
            result = section.get_search_suggestions("test")

        assert result["success"] is False
        assert "Error getting search suggestions" in result["error"]


@pytest.fixture
def mock_search_results():
    """Create a list of mock search results."""
    results = []
    for i in range(5):
        item = MagicMock()
        item.title = f"Item {i}"
        item.ratingKey = f"key{i}"
        item.type = "movie" if i % 2 == 0 else "show"
        item.thumb = f"thumb{i}"
        item.summary = f"Summary {i}"
        item.year = 2020 + i
        item.librarySectionTitle = "Movies" if i % 2 == 0 else "TV Shows"
        results.append(item)
    return results
