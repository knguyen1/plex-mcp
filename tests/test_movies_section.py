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

"""Tests for MoviesSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.movies import MoviesSection


class TestMoviesSection:
    """Test cases for MoviesSection class."""

    def test_init(self, mock_fastmcp, plex_client):
        """Test MoviesSection initialization."""
        section = MoviesSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 7

    def test_get_movies_section_success(
        self, mock_fastmcp, plex_client, mock_movies_section
    ):
        """Test successful retrieval of movies section."""
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section._get_movies_section()

        assert result == mock_movies_section

    def test_get_movies_section_not_found(self, mock_fastmcp, plex_client):
        """Test movies section not found."""
        # Mock server with no movies section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = [
            MagicMock(TYPE="artist"),  # Music section
            MagicMock(TYPE="show"),  # TV section
        ]
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        with pytest.raises(NotFound, match="No movies library found on this server"):
            section._get_movies_section()

    @pytest.mark.parametrize(
        ("query", "limit"),
        [
            ("action", 10),
            ("comedy", 20),
            ("drama", 5),
            ("sci-fi", 50),
        ],
    )
    def test_search_movies_success(
        self, mock_fastmcp, plex_client, mock_movies_section, mock_movie, query, limit
    ):
        """Test successful movie search with various parameters."""
        mock_movies_section.searchMovies.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies(query, limit)

        assert result["success"] is True
        assert result["query"] == query
        assert result["total_results"] == 1
        assert len(result["movies"]) == 1
        assert result["movies"][0]["title"] == "Test Movie"
        mock_movies_section.searchMovies.assert_called_once_with(
            title=query, limit=limit
        )

    def test_search_movies_not_found(self, mock_fastmcp, plex_client):
        """Test movie search when movies section is not found."""
        # Mock server with no movies section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies("test")

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    def test_search_movies_bad_request(
        self, mock_fastmcp, plex_client, mock_movies_section
    ):
        """Test movie search with bad request error."""
        mock_movies_section.searchMovies.side_effect = BadRequest("Invalid query")
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies("invalid")

        assert result["success"] is False
        assert "Error searching movies" in result["error"]

    def test_search_movies_value_error(
        self, mock_fastmcp, plex_client, mock_movies_section
    ):
        """Test movie search with value error."""
        mock_movies_section.searchMovies.side_effect = ValueError("Invalid value")
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies("test")

        assert result["success"] is False
        assert "Error searching movies" in result["error"]

    def test_get_movies_library_success(
        self, mock_fastmcp, plex_client, mock_movies_section
    ):
        """Test successful retrieval of movies library info."""
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movies_library()

        assert result["success"] is True
        assert "library_info" in result
        assert result["library_info"]["title"] == "Movies"
        assert result["library_info"]["type"] == "movie"

    def test_get_movies_library_not_found(self, mock_fastmcp, plex_client):
        """Test movies library info when section not found."""
        # Mock server with no movies section
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movies_library()

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    def test_get_movie_info_success(self, mock_fastmcp, plex_client, mock_movie):
        """Test successful retrieval of movie info."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_movie
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movie_info("12345")

        assert result["success"] is True
        assert "movie" in result
        assert result["movie"]["title"] == "Test Movie"
        assert result["movie"]["year"] == 2023
        assert result["movie"]["genres"] == ["Action", "Drama"]
        assert result["movie"]["directors"] == ["John Director"]
        assert result["movie"]["actors"] == ["Jane Actor", "Bob Actor"]

    def test_get_movie_info_not_found(self, mock_fastmcp, plex_client):
        """Test movie info when movie not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movie_info("12345")  # Use numeric string

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_movie_info_plex_exception(self, mock_fastmcp, plex_client):
        """Test movie info with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Movie not found")
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movie_info("12345")

        assert result["success"] is False
        assert "Movie not found" in result["error"]

    @pytest.mark.parametrize(
        ("genre", "limit"),
        [
            ("Action", 10),
            ("Comedy", 20),
            ("Drama", 5),
            ("Sci-Fi", 50),
        ],
    )
    def test_search_movies_by_genre_success(
        self, mock_fastmcp, plex_client, mock_movies_section, mock_movie, genre, limit
    ):
        """Test successful movie search by genre."""
        mock_movies_section.searchMovies.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_genre(genre, limit)

        assert result["success"] is True
        assert result["genre"] == genre
        assert result["total_results"] == 1
        mock_movies_section.searchMovies.assert_called_once_with(
            genre=genre, limit=limit
        )

    def test_search_movies_by_genre_not_found(self, mock_fastmcp, plex_client):
        """Test movie search by genre when section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_genre("Action")

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    @pytest.mark.parametrize(
        ("year", "limit"),
        [
            (2020, 10),
            (1990, 20),
            (2010, 5),
        ],
    )
    def test_search_movies_by_year_success(
        self, mock_fastmcp, plex_client, mock_movies_section, mock_movie, year, limit
    ):
        """Test successful movie search by year."""
        mock_movies_section.searchMovies.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_year(year=year, limit=limit)

        assert result["success"] is True
        assert result["search_criteria"] == f"year {year}"
        assert result["total_results"] == 1
        mock_movies_section.searchMovies.assert_called_once_with(year=year, limit=limit)

    def test_search_movies_by_year_range_success(
        self, mock_fastmcp, plex_client, mock_movies_section, mock_movie
    ):
        """Test successful movie search by year range."""
        mock_movies_section.searchMovies.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_year(year_from=1990, year_to=2000, limit=10)

        assert result["success"] is True
        assert result["search_criteria"] == "years 1990-2000"
        assert result["total_results"] == 1
        mock_movies_section.searchMovies.assert_called_once_with(
            filters={"year>>": 1989, "year<<": 2001}, limit=10
        )

    def test_search_movies_by_year_invalid_params(self, mock_fastmcp, plex_client):
        """Test movie search by year with invalid parameters."""
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_year()

        assert result["success"] is False
        assert (
            "Either 'year' or both 'year_from' and 'year_to' must be specified"
            in result["error"]
        )

    def test_search_movies_by_year_not_found(self, mock_fastmcp, plex_client):
        """Test movie search by year when section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies_by_year(year=2020)

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    @pytest.mark.parametrize("limit", [5, 10, 20, 50])
    def test_get_recently_added_movies_success(
        self, mock_fastmcp, plex_client, mock_movies_section, mock_movie, limit
    ):
        """Test successful retrieval of recently added movies."""
        mock_movies_section.recentlyAdded.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_recently_added_movies(limit)

        assert result["success"] is True
        assert result["total_results"] == 1
        assert len(result["movies"]) == 1
        assert result["movies"][0]["title"] == "Test Movie"
        mock_movies_section.recentlyAdded.assert_called_once_with(maxresults=limit)

    def test_get_recently_added_movies_not_found(self, mock_fastmcp, plex_client):
        """Test recently added movies when section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_recently_added_movies()

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    @pytest.mark.parametrize(
        ("min_rating", "max_rating", "limit"),
        [
            (7.0, 10.0, 10),
            (8.0, None, 20),
            (None, 6.0, 5),
            (None, None, 15),
        ],
    )
    def test_get_movies_by_rating_success(
        self,
        mock_fastmcp,
        plex_client,
        mock_movies_section,
        mock_movie,
        min_rating,
        max_rating,
        limit,
    ):
        """Test successful movie search by rating."""
        mock_movies_section.searchMovies.return_value = [mock_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movies_by_rating(min_rating, max_rating, limit)

        assert result["success"] is True
        assert result["total_results"] == 1

        # Check that filters were applied correctly
        if min_rating is not None and max_rating is not None:
            expected_filters = {
                "rating>>": min_rating - 0.1,
                "rating<<": max_rating + 0.1,
            }
            mock_movies_section.searchMovies.assert_called_once_with(
                filters=expected_filters, limit=limit
            )
        elif min_rating is not None:
            expected_filters = {"rating>>": min_rating - 0.1}
            mock_movies_section.searchMovies.assert_called_once_with(
                filters=expected_filters, limit=limit
            )
        elif max_rating is not None:
            expected_filters = {"rating<<": max_rating + 0.1}
            mock_movies_section.searchMovies.assert_called_once_with(
                filters=expected_filters, limit=limit
            )
        else:
            mock_movies_section.searchMovies.assert_called_once_with(limit=limit)

    def test_get_movies_by_rating_not_found(self, mock_fastmcp, plex_client):
        """Test movie search by rating when section not found."""
        mock_server = MagicMock()
        mock_server.library.sections.return_value = []
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movies_by_rating(min_rating=8.0)

        assert result["success"] is False
        assert "Movies library not found" in result["error"]

    def test_movie_attributes_handling(
        self, mock_fastmcp, plex_client, mock_movies_section
    ):
        """Test that movie attributes are handled correctly when missing."""
        # Create a movie with minimal attributes
        minimal_movie = MagicMock()
        minimal_movie.title = "Minimal Movie"
        minimal_movie.ratingKey = "minimal123"
        # Don't set year, summary, rating, etc. - use side_effect to return None
        minimal_movie.year = None
        minimal_movie.summary = None
        minimal_movie.rating = None

        mock_movies_section.searchMovies.return_value = [minimal_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies("minimal")

        assert result["success"] is True
        assert result["movies"][0]["title"] == "Minimal Movie"
        assert result["movies"][0]["year"] is None
        assert result["movies"][0]["summary"] is None
        assert result["movies"][0]["rating"] is None

    def test_movie_viewed_status(self, mock_fastmcp, plex_client, mock_movies_section):
        """Test movie viewed status handling."""
        # Create a movie that has been viewed
        viewed_movie = MagicMock()
        viewed_movie.title = "Viewed Movie"
        viewed_movie.ratingKey = "viewed123"
        viewed_movie.viewedAt = "2023-01-01T00:00:00Z"

        mock_movies_section.searchMovies.return_value = [viewed_movie]
        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.search_movies("viewed")

        assert result["success"] is True
        assert result["movies"][0]["viewed"] is True

    def test_movie_with_genres_directors_actors(
        self, mock_fastmcp, plex_client, mock_movie
    ):
        """Test movie info with genres, directors, and actors."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_movie
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movie_info("12345")

        assert result["success"] is True
        movie_info = result["movie"]
        assert movie_info["genres"] == ["Action", "Drama"]
        assert movie_info["directors"] == ["John Director"]
        assert movie_info["actors"] == ["Jane Actor", "Bob Actor"]
        assert movie_info["studio"] == "Test Studio"
        assert movie_info["content_rating"] == "PG-13"

    def test_movie_without_genres_directors_actors(self, mock_fastmcp, plex_client):
        """Test movie info without genres, directors, and actors."""
        # Create a movie without these attributes
        simple_movie = MagicMock()
        simple_movie.title = "Simple Movie"
        simple_movie.ratingKey = "123456"
        # Don't set genres, directors, actors attributes

        mock_server = MagicMock()
        mock_server.fetchItem.return_value = simple_movie
        plex_client._server = mock_server

        section = MoviesSection(mock_fastmcp, plex_client)

        result = section.get_movie_info("123456")

        assert result["success"] is True
        movie_info = result["movie"]
        assert movie_info["genres"] == []
        assert movie_info["directors"] == []
        assert movie_info["actors"] == []
