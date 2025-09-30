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

"""Tests for CollectionsSection class."""

from unittest.mock import MagicMock

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.collections import CollectionsSection


class TestCollectionsSection:
    """Test cases for CollectionsSection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test CollectionsSection initialization."""
        section = CollectionsSection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 8

    def test_get_library_section_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
    ) -> None:
        """Test successful library section retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section._get_library_section("Movies")

        assert result == mock_movies_section
        mock_server.library.section.assert_called_once_with("Movies")

    def test_get_library_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test library section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        with pytest.raises(NotFound, match="Library section 'Movies' not found"):
            section._get_library_section("Movies")

    @pytest.mark.parametrize("limit", [10, 25, 50, 100])
    def test_list_collections_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_collections: list[MagicMock],
        limit: int,
    ) -> None:
        """Test successful collection listing."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.collections.return_value = mock_collections
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.list_collections("Movies", limit)

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["total_collections"] == 2
        assert len(result["collections"]) == 2
        assert result["collections"][0]["title"] == "Action Movies"
        assert result["collections"][1]["title"] == "Comedy Movies"

    def test_list_collections_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection listing when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.list_collections("Nonexistent Section")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_list_collections_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
    ) -> None:
        """Test collection listing with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.collections.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.list_collections("Movies")

        assert result["success"] is False
        assert "Error listing collections" in result["error"]

    def test_get_collection_info_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
        mock_collection_items: list[MagicMock],
    ) -> None:
        """Test successful collection info retrieval."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_collection
        mock_collection.items.return_value = mock_collection_items
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.get_collection_info("12345")

        assert result["success"] is True
        assert "collection" in result
        assert result["collection"]["title"] == "Action Movies"
        assert result["collection"]["summary"] == "Collection of action movies"
        assert result["collection"]["child_count"] == 2
        assert len(result["collection"]["items"]) == 2

    def test_get_collection_info_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection info when collection not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.get_collection_info("99999")

        assert result["success"] is False
        assert "Collection with rating key 99999 not found" in result["error"]

    def test_get_collection_info_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection info with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Collection not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.get_collection_info("12345")

        assert result["success"] is False
        assert "Collection not found" in result["error"]

    def test_create_collection_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_collection: MagicMock,
    ) -> None:
        """Test successful collection creation."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_server.createCollection.return_value = mock_collection
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.create_collection(
            "Movies", "Test Collection", "Test description"
        )

        assert result["success"] is True
        assert "Created collection 'Test Collection'" in result["message"]
        assert "collection" in result
        assert result["collection"]["title"] == "Action Movies"
        mock_server.createCollection.assert_called_once()

    def test_create_collection_with_items_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_collection: MagicMock,
        mock_media_items: list[MagicMock],
    ) -> None:
        """Test successful collection creation with items."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_server.createCollection.return_value = mock_collection
        mock_server.fetchItem.side_effect = mock_media_items
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.create_collection(
            "Movies", "Test Collection", "Test description", ["12345", "67890"]
        )

        assert result["success"] is True
        assert "Created collection 'Test Collection'" in result["message"]
        mock_server.createCollection.assert_called_once()

    def test_create_collection_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection creation when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.create_collection("Nonexistent Section", "Test Collection")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_create_collection_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
    ) -> None:
        """Test collection creation with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_server.createCollection.side_effect = BadRequest("Invalid request")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.create_collection("Movies", "Test Collection")

        assert result["success"] is False
        assert "Error creating collection" in result["error"]

    def test_add_to_collection_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
        mock_media_items: list[MagicMock],
    ) -> None:
        """Test successful addition to collection."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = [mock_collection, *mock_media_items]
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.add_to_collection("12345", ["67890", "11111"])

        assert result["success"] is True
        assert "Added 2 items to collection 'Action Movies'" in result["message"]
        assert result["collection_title"] == "Action Movies"
        assert result["items_added"] == 2
        mock_collection.addItems.assert_called_once()

    def test_add_to_collection_collection_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test addition to collection when collection not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.add_to_collection("99999", ["67890"])

        assert result["success"] is False
        assert "Collection with rating key 99999 not found" in result["error"]

    def test_add_to_collection_no_valid_items(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
    ) -> None:
        """Test addition to collection with no valid items."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = [
            mock_collection,
            NotFound("Item not found"),
            NotFound("Item not found"),
        ]
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.add_to_collection("12345", ["99999", "88888"])

        assert result["success"] is False
        assert "No valid items found to add to collection" in result["error"]

    def test_add_to_collection_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test addition to collection with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Collection not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.add_to_collection("12345", ["67890"])

        assert result["success"] is False
        assert "Collection not found" in result["error"]

    def test_remove_from_collection_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
        mock_media_items: list[MagicMock],
    ) -> None:
        """Test successful removal from collection."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = [mock_collection, *mock_media_items]
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.remove_from_collection("12345", ["67890", "11111"])

        assert result["success"] is True
        assert "Removed 2 items from collection 'Action Movies'" in result["message"]
        assert result["collection_title"] == "Action Movies"
        assert result["items_removed"] == 2
        mock_collection.removeItems.assert_called_once()

    def test_remove_from_collection_collection_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test removal from collection when collection not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.remove_from_collection("99999", ["67890"])

        assert result["success"] is False
        assert "Collection with rating key 99999 not found" in result["error"]

    def test_remove_from_collection_no_valid_items(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
    ) -> None:
        """Test removal from collection with no valid items."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = [
            mock_collection,
            NotFound("Item not found"),
            NotFound("Item not found"),
        ]
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.remove_from_collection("12345", ["99999", "88888"])

        assert result["success"] is False
        assert "No valid items found to remove from collection" in result["error"]

    def test_remove_from_collection_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test removal from collection with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Collection not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.remove_from_collection("12345", ["67890"])

        assert result["success"] is False
        assert "Collection not found" in result["error"]

    @pytest.mark.parametrize(
        ("title", "summary"),
        [
            ("New Title", None),
            (None, "New Summary"),
            ("New Title", "New Summary"),
        ],
    )
    def test_update_collection_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
        title: str | None,
        summary: str | None,
    ) -> None:
        """Test successful collection update."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_collection
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.update_collection("12345", title, summary)

        assert result["success"] is True
        assert "Updated collection 'Action Movies'" in result["message"]
        assert result["collection_title"] == "Action Movies"

        # Check that appropriate methods were called
        if title is not None:
            mock_collection.editTitle.assert_called_once_with(title)
        if summary is not None:
            mock_collection.editSummary.assert_called_once_with(summary)

    def test_update_collection_collection_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection update when collection not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.update_collection("99999", "New Title")

        assert result["success"] is False
        assert "Collection with rating key 99999 not found" in result["error"]

    def test_update_collection_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection update with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Collection not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.update_collection("12345", "New Title")

        assert result["success"] is False
        assert "Collection not found" in result["error"]

    def test_delete_collection_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
    ) -> None:
        """Test successful collection deletion."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_collection
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.delete_collection("12345")

        assert result["success"] is True
        assert "Deleted collection 'Action Movies'" in result["message"]
        assert result["deleted_title"] == "Action Movies"
        mock_collection.delete.assert_called_once()

    def test_delete_collection_collection_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection deletion when collection not found."""
        mock_server = MagicMock()
        mock_server.fetchItem.return_value = None
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.delete_collection("99999")

        assert result["success"] is False
        assert "Collection with rating key 99999 not found" in result["error"]

    def test_delete_collection_plex_exception(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection deletion with Plex exception."""
        mock_server = MagicMock()
        mock_server.fetchItem.side_effect = NotFound("Collection not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.delete_collection("12345")

        assert result["success"] is False
        assert "Collection not found" in result["error"]

    @pytest.mark.parametrize(
        ("query", "limit"),
        [
            ("action", 10),
            ("comedy", 20),
            ("drama", 5),
            ("sci-fi", 50),
        ],
    )
    def test_search_collections_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_collections: list[MagicMock],
        query: str,
        limit: int,
    ) -> None:
        """Test successful collection search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.searchCollections.return_value = mock_collections
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.search_collections("Movies", query, limit)

        assert result["success"] is True
        assert result["section_title"] == "Movies"
        assert result["query"] == query
        assert result["total_results"] == 2
        assert len(result["collections"]) == 2
        mock_movies_section.searchCollections.assert_called_once_with(
            title=query, limit=limit
        )

    def test_search_collections_section_not_found(
        self, mock_fastmcp: MagicMock, plex_client: MagicMock
    ) -> None:
        """Test collection search when section not found."""
        mock_server = MagicMock()
        mock_server.library.section.side_effect = NotFound("Section not found")
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.search_collections("Nonexistent Section", "action")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_search_collections_bad_request(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
    ) -> None:
        """Test collection search with bad request error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.searchCollections.side_effect = BadRequest(
            "Invalid request"
        )
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.search_collections("Movies", "action")

        assert result["success"] is False
        assert "Error searching collections" in result["error"]

    def test_collection_attributes_handling(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
    ) -> None:
        """Test that collection attributes are handled correctly when missing."""
        # Create a collection with minimal attributes
        minimal_collection = MagicMock()
        minimal_collection.title = "Minimal Collection"
        minimal_collection.ratingKey = "minimal123"
        minimal_collection.childCount = 0
        # Explicitly set summary, thumb, art, etc. to None/False
        minimal_collection.summary = None
        minimal_collection.thumb = None
        minimal_collection.art = None
        minimal_collection.smart = False
        minimal_collection.contentRating = None
        minimal_collection.audienceRating = None
        minimal_collection.userRating = None

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_movies_section.collections.return_value = [minimal_collection]
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.list_collections("Movies")

        assert result["success"] is True
        assert result["collections"][0]["title"] == "Minimal Collection"
        assert result["collections"][0]["summary"] is None
        assert result["collections"][0]["thumb"] is None
        assert result["collections"][0]["art"] is None
        assert result["collections"][0]["smart"] is False

    def test_collection_items_handling(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_collection: MagicMock,
    ) -> None:
        """Test that collection items are handled correctly when missing."""
        # Create collection items with minimal attributes
        minimal_item1 = MagicMock()
        minimal_item1.title = "Minimal Item 1"
        minimal_item1.ratingKey = "item1"
        minimal_item1.type = "movie"
        # Explicitly set year, thumb to None
        minimal_item1.year = None
        minimal_item1.thumb = None

        minimal_item2 = MagicMock()
        minimal_item2.title = "Minimal Item 2"
        minimal_item2.ratingKey = "item2"
        minimal_item2.type = "movie"
        minimal_item2.year = None
        minimal_item2.thumb = None

        mock_collection.items.return_value = [minimal_item1, minimal_item2]

        mock_server = MagicMock()
        mock_server.fetchItem.return_value = mock_collection
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.get_collection_info("12345")

        assert result["success"] is True
        items = result["collection"]["items"]
        assert len(items) == 2
        assert items[0]["title"] == "Minimal Item 1"
        assert items[0]["year"] is None
        assert items[0]["thumb"] is None
        assert items[1]["title"] == "Minimal Item 2"
        assert items[1]["year"] is None
        assert items[1]["thumb"] is None

    def test_create_collection_with_mixed_valid_invalid_items(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_movies_section: MagicMock,
        mock_collection: MagicMock,
        mock_media_item: MagicMock,
    ) -> None:
        """Test collection creation with some valid and some invalid items."""

        # Mock fetchItem to return item for valid key, raise NotFound for invalid
        def mock_fetch_item(rating_key):
            if rating_key == 12345:
                return mock_media_item
            msg = "Item not found"
            raise NotFound(msg)

        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_movies_section
        mock_server.createCollection.return_value = mock_collection
        mock_server.fetchItem.side_effect = mock_fetch_item
        plex_client._server = mock_server

        section = CollectionsSection(mock_fastmcp, plex_client)

        result = section.create_collection(
            "Movies", "Test Collection", "Test description", ["12345", "99999"]
        )

        assert result["success"] is True
        # Should create collection with only the valid item
        mock_server.createCollection.assert_called_once()
        call_args = mock_server.createCollection.call_args
        assert call_args[1]["title"] == "Test Collection"
        assert len(call_args[1]["items"]) == 1  # Only one valid item
