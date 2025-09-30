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

"""Collections section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class CollectionsSection:
    """Collections section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Collections section.

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
        """Register all collections-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(
            self.list_collections,
            name="list_collections",
            description="List all collections in a library section",
        )
        self.mcp.tool(
            self.get_collection_info,
            name="get_collection_info",
            description="Get detailed information about a specific collection",
        )
        self.mcp.tool(
            self.create_collection,
            name="create_collection",
            description="Create a new collection",
        )
        self.mcp.tool(
            self.add_to_collection,
            name="add_to_collection",
            description="Add items to a collection",
        )
        self.mcp.tool(
            self.remove_from_collection,
            name="remove_from_collection",
            description="Remove items from a collection",
        )
        self.mcp.tool(
            self.update_collection,
            name="update_collection",
            description="Update collection metadata (title, summary, etc.)",
        )
        self.mcp.tool(
            self.delete_collection,
            name="delete_collection",
            description="Delete a collection",
        )
        self.mcp.tool(
            self.search_collections,
            name="search_collections",
            description="Search for collections by title or other criteria",
        )

    def _get_library_section(self, section_title: str) -> Any:
        """
        Get a library section by title.

        Parameters
        ----------
        section_title : str
            The title of the library section

        Returns
        -------
        plexapi.library.LibrarySection
            The library section

        Raises
        ------
        NotFound
            If the library section is not found
        """
        server = self.plex_client.get_server()
        try:
            section = server.library.section(section_title)
        except NotFound as e:
            msg = f"Library section '{section_title}' not found"
            raise NotFound(msg) from e
        else:
            return section

    def list_collections(
        self,
        section_title: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List all collections in a library section.

        Parameters
        ----------
        section_title : str
            The title of the library section
        limit : int, default=50
            Maximum number of collections to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing list of collections
        """
        try:
            section = self._get_library_section(section_title)
            collections = section.collections()

            results = [
                {
                    "title": collection.title,
                    "summary": getattr(collection, "summary", None),
                    "rating_key": collection.ratingKey,
                    "child_count": getattr(collection, "childCount", 0),
                    "thumb": getattr(collection, "thumb", None),
                    "art": getattr(collection, "art", None),
                    "smart": getattr(collection, "smart", False),
                    "content_rating": getattr(collection, "contentRating", None),
                    "audience_rating": getattr(collection, "audienceRating", None),
                    "user_rating": getattr(collection, "userRating", None),
                }
                for collection in collections[:limit]
            ]
            result = {
                "success": True,
                "section_title": section_title,
                "total_collections": len(results),
                "collections": results,
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error listing collections: %s")
            return {"success": False, "error": f"Error listing collections: {e}"}
        else:
            return result

    def get_collection_info(
        self,
        collection_rating_key: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific collection.

        Parameters
        ----------
        collection_rating_key : str
            The rating key of the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed collection information
        """
        try:
            server = self.plex_client.get_server()
            collection = server.fetchItem(int(collection_rating_key))

            if not collection:
                return {
                    "success": False,
                    "error": f"Collection with rating key {collection_rating_key} not found",
                }

            # Get collection items
            items = collection.items()

            item_list = [
                {
                    "title": item.title,
                    "year": getattr(item, "year", None),
                    "rating_key": item.ratingKey,
                    "type": getattr(item, "type", None),
                    "thumb": getattr(item, "thumb", None),
                }
                for item in items
            ]
            result = {
                "success": True,
                "collection": {
                    "title": collection.title,
                    "summary": getattr(collection, "summary", None),
                    "rating_key": collection.ratingKey,
                    "child_count": getattr(collection, "childCount", 0),
                    "thumb": getattr(collection, "thumb", None),
                    "art": getattr(collection, "art", None),
                    "smart": getattr(collection, "smart", False),
                    "content_rating": getattr(collection, "contentRating", None),
                    "audience_rating": getattr(collection, "audienceRating", None),
                    "user_rating": getattr(collection, "userRating", None),
                    "library_section_id": getattr(collection, "librarySectionID", None),
                    "library_section_title": getattr(
                        collection, "librarySectionTitle", None
                    ),
                    "items": item_list,
                },
            }
        except NotFound as e:
            logger.exception("Collection not found: %s")
            return {"success": False, "error": f"Collection not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting collection info: %s")
            return {"success": False, "error": f"Error getting collection info: {e}"}
        else:
            return result

    def create_collection(
        self,
        section_title: str,
        title: str,
        summary: str | None = None,
        items: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new collection.

        Parameters
        ----------
        section_title : str
            The title of the library section
        title : str
            The title of the collection
        summary : str, optional
            Summary/description of the collection
        items : list[str], optional
            List of rating keys to add to the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing collection creation results
        """
        try:
            section = self._get_library_section(section_title)

            # Get items if provided
            media_items = []
            if items:
                server = self.plex_client.get_server()
                for rating_key in items:
                    try:
                        item = server.fetchItem(int(rating_key))
                        if item:
                            media_items.append(item)
                    except (NotFound, ValueError):
                        logger.warning("Item with rating key %s not found", rating_key)
                        continue

            # Create the collection
            collection = self.plex_client.get_server().createCollection(
                title=title,
                section=section,
                items=media_items if media_items else None,
                summary=summary,
            )
            result = {
                "success": True,
                "message": f"Created collection '{title}'",
                "collection": {
                    "title": collection.title,
                    "rating_key": collection.ratingKey,
                    "summary": getattr(collection, "summary", None),
                    "child_count": getattr(collection, "childCount", 0),
                },
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error creating collection: %s")
            return {"success": False, "error": f"Error creating collection: {e}"}
        else:
            return result

    def add_to_collection(
        self,
        collection_rating_key: str,
        item_rating_keys: list[str],
    ) -> dict[str, Any]:
        """
        Add items to a collection.

        Parameters
        ----------
        collection_rating_key : str
            The rating key of the collection
        item_rating_keys : list[str]
            List of rating keys to add to the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing addition results
        """
        try:
            server = self.plex_client.get_server()
            collection = server.fetchItem(int(collection_rating_key))

            if not collection:
                return {
                    "success": False,
                    "error": f"Collection with rating key {collection_rating_key} not found",
                }

            # Get items to add
            items_to_add = []
            for rating_key in item_rating_keys:
                try:
                    item = server.fetchItem(int(rating_key))
                    if item:
                        items_to_add.append(item)
                except (NotFound, ValueError):
                    logger.warning("Item with rating key %s not found", rating_key)
                    continue

            if not items_to_add:
                return {
                    "success": False,
                    "error": "No valid items found to add to collection",
                }

            # Add items to collection
            collection.addItems(items_to_add)
            result = {
                "success": True,
                "message": f"Added {len(items_to_add)} items to collection '{collection.title}'",
                "collection_title": collection.title,
                "items_added": len(items_to_add),
            }
        except NotFound as e:
            logger.exception("Collection not found: %s")
            return {"success": False, "error": f"Collection not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error adding to collection: %s")
            return {"success": False, "error": f"Error adding to collection: {e}"}
        else:
            return result

    def remove_from_collection(
        self,
        collection_rating_key: str,
        item_rating_keys: list[str],
    ) -> dict[str, Any]:
        """
        Remove items from a collection.

        Parameters
        ----------
        collection_rating_key : str
            The rating key of the collection
        item_rating_keys : list[str]
            List of rating keys to remove from the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing removal results
        """
        try:
            server = self.plex_client.get_server()
            collection = server.fetchItem(int(collection_rating_key))

            if not collection:
                return {
                    "success": False,
                    "error": f"Collection with rating key {collection_rating_key} not found",
                }

            # Get items to remove
            items_to_remove = []
            for rating_key in item_rating_keys:
                try:
                    item = server.fetchItem(int(rating_key))
                    if item:
                        items_to_remove.append(item)
                except (NotFound, ValueError):
                    logger.warning("Item with rating key %s not found", rating_key)
                    continue

            if not items_to_remove:
                return {
                    "success": False,
                    "error": "No valid items found to remove from collection",
                }

            # Remove items from collection
            collection.removeItems(items_to_remove)
            result = {
                "success": True,
                "message": f"Removed {len(items_to_remove)} items from collection '{collection.title}'",
                "collection_title": collection.title,
                "items_removed": len(items_to_remove),
            }
        except NotFound as e:
            logger.exception("Collection not found: %s")
            return {"success": False, "error": f"Collection not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error removing from collection: %s")
            return {"success": False, "error": f"Error removing from collection: {e}"}
        else:
            return result

    def update_collection(
        self,
        collection_rating_key: str,
        title: str | None = None,
        summary: str | None = None,
    ) -> dict[str, Any]:
        """
        Update collection metadata.

        Parameters
        ----------
        collection_rating_key : str
            The rating key of the collection
        title : str, optional
            New title for the collection
        summary : str, optional
            New summary for the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing update results
        """
        try:
            server = self.plex_client.get_server()
            collection = server.fetchItem(int(collection_rating_key))

            if not collection:
                return {
                    "success": False,
                    "error": f"Collection with rating key {collection_rating_key} not found",
                }

            # Define update actions mapping
            update_actions = {
                "title": (title, collection.editTitle),
                "summary": (summary, collection.editSummary),
            }

            # Update fields if provided
            updated_fields = []
            for field_name, (value, update_func) in update_actions.items():
                if value is not None:
                    update_func(value)
                    updated_fields.append(field_name)
            result = {
                "success": True,
                "message": f"Updated collection '{collection.title}'",
                "collection_title": collection.title,
                "updated_fields": updated_fields,
            }
        except NotFound as e:
            logger.exception("Collection not found: %s")
            return {"success": False, "error": f"Collection not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error updating collection: %s")
            return {"success": False, "error": f"Error updating collection: {e}"}
        else:
            return result

    def delete_collection(
        self,
        collection_rating_key: str,
    ) -> dict[str, Any]:
        """
        Delete a collection.

        Parameters
        ----------
        collection_rating_key : str
            The rating key of the collection

        Returns
        -------
        dict[str, Any]
            Dictionary containing deletion results
        """
        try:
            server = self.plex_client.get_server()
            collection = server.fetchItem(int(collection_rating_key))

            if not collection:
                return {
                    "success": False,
                    "error": f"Collection with rating key {collection_rating_key} not found",
                }

            collection_title = collection.title
            collection.delete()
            result = {
                "success": True,
                "message": f"Deleted collection '{collection_title}'",
                "deleted_title": collection_title,
            }
        except NotFound as e:
            logger.exception("Collection not found: %s")
            return {"success": False, "error": f"Collection not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error deleting collection: %s")
            return {"success": False, "error": f"Error deleting collection: {e}"}
        else:
            return result

    def search_collections(
        self,
        section_title: str,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for collections by title or other criteria.

        Parameters
        ----------
        section_title : str
            The title of the library section
        query : str
            The search query
        limit : int, default=20
            Maximum number of collections to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing search results
        """
        try:
            section = self._get_library_section(section_title)
            collections = section.searchCollections(title=query, limit=limit)

            results = [
                {
                    "title": collection.title,
                    "summary": getattr(collection, "summary", None),
                    "rating_key": collection.ratingKey,
                    "child_count": getattr(collection, "childCount", 0),
                    "thumb": getattr(collection, "thumb", None),
                    "smart": getattr(collection, "smart", False),
                }
                for collection in collections
            ]
            result = {
                "success": True,
                "section_title": section_title,
                "query": query,
                "total_results": len(results),
                "collections": results,
            }
        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching collections: %s")
            return {"success": False, "error": f"Error searching collections: {e}"}
        else:
            return result
