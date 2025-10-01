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

"""Photo Library section for Plex MCP Server."""

import logging
from typing import Any

from fastmcp import FastMCP
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.client.plex_client import PlexClient

logger = logging.getLogger(__name__)


class PhotoLibrarySection:
    """Photo Library section for Plex MCP Server operations."""

    def __init__(self, mcp: FastMCP, plex_client: PlexClient):
        """
        Initialize the Photo Library section.

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
        """Register all photo library-related MCP tools."""
        # Register tools using the new FastMCP API
        self.mcp.tool(self.list_photos)
        self.mcp.tool(self.get_photo_info)
        self.mcp.tool(self.search_photos)
        self.mcp.tool(self.get_photo_albums)
        self.mcp.tool(self.get_album_photos)
        self.mcp.tool(self.get_recently_added_photos)
        self.mcp.tool(self.get_photo_timeline)

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

    def list_photos(
        self,
        section_title: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List photos in a photo library section.

        Parameters
        ----------
        section_title : str
            The title of the library section
        limit : int, default=50
            Maximum number of photos to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing list of photos
        """
        try:
            section = self._get_library_section(section_title)
            photos = section.searchPhotos(limit=limit)

            results = [
                {
                    "title": photo.title,
                    "summary": getattr(photo, "summary", None),
                    "rating_key": photo.ratingKey,
                    "thumb": getattr(photo, "thumb", None),
                    "art": getattr(photo, "art", None),
                    "originally_available_at": getattr(
                        photo, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(photo, "addedAt", None),
                    "updated_at": getattr(photo, "updatedAt", None),
                    "media": [
                        {
                            "width": getattr(media, "width", None),
                            "height": getattr(media, "height", None),
                            "aspect_ratio": getattr(media, "aspectRatio", None),
                            "video_codec": getattr(media, "videoCodec", None),
                            "video_resolution": getattr(media, "videoResolution", None),
                            "video_frame_rate": getattr(media, "videoFrameRate", None),
                        }
                        for media in getattr(photo, "media", [])
                    ],
                }
                for photo in photos
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "total_photos": len(results),
                "photos": results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error listing photos: %s")
            return {"success": False, "error": f"Error listing photos: {e}"}
        else:
            return result

    def get_photo_info(
        self,
        photo_rating_key: str,
    ) -> dict[str, Any]:
        """
        Get detailed information about a specific photo.

        Parameters
        ----------
        photo_rating_key : str
            The rating key of the photo

        Returns
        -------
        dict[str, Any]
            Dictionary containing detailed photo information
        """
        try:
            server = self.plex_client.get_server()
            photo = server.fetchItem(int(photo_rating_key))

            if not photo:
                return {
                    "success": False,
                    "error": f"Photo with rating key {photo_rating_key} not found",
                }

            result = {
                "success": True,
                "photo": {
                    "title": photo.title,
                    "summary": getattr(photo, "summary", None),
                    "rating_key": photo.ratingKey,
                    "thumb": getattr(photo, "thumb", None),
                    "art": getattr(photo, "art", None),
                    "originally_available_at": getattr(
                        photo, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(photo, "addedAt", None),
                    "updated_at": getattr(photo, "updatedAt", None),
                    "library_section_id": getattr(photo, "librarySectionID", None),
                    "library_section_title": getattr(
                        photo, "librarySectionTitle", None
                    ),
                    "media": [
                        {
                            "width": getattr(media, "width", None),
                            "height": getattr(media, "height", None),
                            "aspect_ratio": getattr(media, "aspectRatio", None),
                            "video_codec": getattr(media, "videoCodec", None),
                            "video_resolution": getattr(media, "videoResolution", None),
                            "video_frame_rate": getattr(media, "videoFrameRate", None),
                            "container": getattr(media, "container", None),
                            "bitrate": getattr(media, "bitrate", None),
                        }
                        for media in getattr(photo, "media", [])
                    ],
                },
            }

        except NotFound as e:
            logger.exception("Photo not found: %s")
            return {"success": False, "error": f"Photo not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting photo info: %s")
            return {"success": False, "error": f"Error getting photo info: {e}"}
        else:
            return result

    def search_photos(
        self,
        section_title: str,
        query: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Search for photos by title, date, or other criteria.

        Parameters
        ----------
        section_title : str
            The title of the library section
        query : str
            The search query
        limit : int, default=20
            Maximum number of photos to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing search results
        """
        try:
            section = self._get_library_section(section_title)
            photos = section.searchPhotos(title=query, limit=limit)

            results = [
                {
                    "title": photo.title,
                    "summary": getattr(photo, "summary", None),
                    "rating_key": photo.ratingKey,
                    "thumb": getattr(photo, "thumb", None),
                    "originally_available_at": getattr(
                        photo, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(photo, "addedAt", None),
                }
                for photo in photos
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "query": query,
                "total_results": len(results),
                "photos": results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error searching photos: %s")
            return {"success": False, "error": f"Error searching photos: {e}"}
        else:
            return result

    def get_photo_albums(
        self,
        section_title: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List photo albums in a library section.

        Parameters
        ----------
        section_title : str
            The title of the library section
        limit : int, default=50
            Maximum number of albums to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing list of photo albums
        """
        try:
            section = self._get_library_section(section_title)
            albums = section.searchAlbums(limit=limit)

            results = [
                {
                    "title": album.title,
                    "summary": getattr(album, "summary", None),
                    "rating_key": album.ratingKey,
                    "thumb": getattr(album, "thumb", None),
                    "art": getattr(album, "art", None),
                    "originally_available_at": getattr(
                        album, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(album, "addedAt", None),
                    "updated_at": getattr(album, "updatedAt", None),
                    "child_count": getattr(album, "childCount", 0),
                }
                for album in albums
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "total_albums": len(results),
                "albums": results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting photo albums: %s")
            return {"success": False, "error": f"Error getting photo albums: {e}"}
        else:
            return result

    def get_album_photos(
        self,
        album_rating_key: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get photos from a specific album.

        Parameters
        ----------
        album_rating_key : str
            The rating key of the album
        limit : int, default=50
            Maximum number of photos to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing album photos
        """
        try:
            server = self.plex_client.get_server()
            album = server.fetchItem(int(album_rating_key))

            if not album:
                return {
                    "success": False,
                    "error": f"Album with rating key {album_rating_key} not found",
                }

            photos = album.photos()

            results = [
                {
                    "title": photo.title,
                    "summary": getattr(photo, "summary", None),
                    "rating_key": photo.ratingKey,
                    "thumb": getattr(photo, "thumb", None),
                    "originally_available_at": getattr(
                        photo, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(photo, "addedAt", None),
                }
                for photo in photos[:limit]
            ]

            result = {
                "success": True,
                "album_title": album.title,
                "total_photos": len(results),
                "photos": results,
            }

        except NotFound as e:
            logger.exception("Album not found: %s")
            return {"success": False, "error": f"Album not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting album photos: %s")
            return {"success": False, "error": f"Error getting album photos: {e}"}
        else:
            return result

    def get_recently_added_photos(
        self,
        section_title: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        Get recently added photos.

        Parameters
        ----------
        section_title : str
            The title of the library section
        limit : int, default=20
            Maximum number of photos to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing recently added photos
        """
        try:
            section = self._get_library_section(section_title)
            photos = section.recentlyAddedAlbums(limit=limit)

            results = [
                {
                    "title": photo.title,
                    "summary": getattr(photo, "summary", None),
                    "rating_key": photo.ratingKey,
                    "thumb": getattr(photo, "thumb", None),
                    "originally_available_at": getattr(
                        photo, "originallyAvailableAt", None
                    ),
                    "added_at": getattr(photo, "addedAt", None),
                }
                for photo in photos
            ]

            result = {
                "success": True,
                "section_title": section_title,
                "total_photos": len(results),
                "photos": results,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting recently added photos: %s")
            return {
                "success": False,
                "error": f"Error getting recently added photos: {e}",
            }
        else:
            return result

    def get_photo_timeline(
        self,
        section_title: str,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get photos organized by date/timeline.

        Parameters
        ----------
        section_title : str
            The title of the library section
        limit : int, default=50
            Maximum number of photos to return

        Returns
        -------
        dict[str, Any]
            Dictionary containing photos organized by timeline
        """
        try:
            section = self._get_library_section(section_title)
            photos = section.searchPhotos(limit=limit)

            # Group photos by date
            timeline = {}
            for photo in photos:
                date = getattr(photo, "originallyAvailableAt", None)
                if date:
                    date_str = (
                        date.strftime("%Y-%m-%d")
                        if hasattr(date, "strftime")
                        else str(date)
                    )
                    if date_str not in timeline:
                        timeline[date_str] = []
                    timeline[date_str].append({
                        "title": photo.title,
                        "rating_key": photo.ratingKey,
                        "thumb": getattr(photo, "thumb", None),
                        "added_at": getattr(photo, "addedAt", None),
                    })

            result = {
                "success": True,
                "section_title": section_title,
                "total_dates": len(timeline),
                "timeline": timeline,
            }

        except NotFound as e:
            logger.exception("Library section not found: %s")
            return {"success": False, "error": f"Library section not found: {e}"}
        except (BadRequest, ValueError) as e:
            logger.exception("Error getting photo timeline: %s")
            return {"success": False, "error": f"Error getting photo timeline: {e}"}
        else:
            return result
