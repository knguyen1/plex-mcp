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

"""Tests for PhotoLibrarySection class."""

from unittest.mock import MagicMock, patch

import pytest
from plexapi.exceptions import BadRequest, NotFound

from plex_mcp.sections.photo_library import PhotoLibrarySection


class TestPhotoLibrarySection:
    """Test cases for PhotoLibrarySection class."""

    def test_init(self, mock_fastmcp: MagicMock, plex_client: MagicMock) -> None:
        """Test PhotoLibrarySection initialization."""
        section = PhotoLibrarySection(mock_fastmcp, plex_client)

        assert section.mcp == mock_fastmcp
        assert section.plex_client == plex_client
        # Verify tools are registered
        assert mock_fastmcp.tool.call_count == 7

    def test_get_library_section_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
    ) -> None:
        """Test successful library section retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.library.section.return_value = mock_photos_section

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section._get_library_section("Photos")

        assert result == mock_photos_section
        mock_server.library.section.assert_called_once_with("Photos")

    def test_get_library_section_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test library section not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.library.section.side_effect = NotFound("Section not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)

            with pytest.raises(NotFound, match="Library section 'Photos' not found"):
                section._get_library_section("Photos")

    def test_list_photos_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
        mock_photos: list[MagicMock],
    ) -> None:
        """Test successful photo listing."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.searchPhotos.return_value = mock_photos

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.list_photos("Photos", limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Photos"
        assert result["total_photos"] == len(mock_photos)
        assert "photos" in result
        mock_photos_section.searchPhotos.assert_called_once_with(limit=10)

    def test_list_photos_section_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test photo listing with section not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.library.section.side_effect = NotFound("Section not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.list_photos("Photos")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_list_photos_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
    ) -> None:
        """Test photo listing with error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.searchPhotos.side_effect = BadRequest("Search error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.list_photos("Photos")

        assert result["success"] is False
        assert "Error listing photos" in result["error"]

    def test_get_photo_info_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photo: MagicMock,
    ) -> None:
        """Test successful photo info retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.fetchItem.return_value = mock_photo

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_info("12345")

        assert result["success"] is True
        assert "photo" in result
        mock_server.fetchItem.assert_called_once_with(12345)

    def test_get_photo_info_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test photo info with photo not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.fetchItem.return_value = None

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_info("12345")

        assert result["success"] is False
        assert "Photo with rating key 12345 not found" in result["error"]

    def test_get_photo_info_error(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test photo info with error."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.fetchItem.side_effect = BadRequest("Fetch error")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_info("12345")

        assert result["success"] is False
        assert "Error getting photo info" in result["error"]

    def test_search_photos_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
        mock_photos: list[MagicMock],
    ) -> None:
        """Test successful photo search."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.searchPhotos.return_value = mock_photos

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.search_photos("Photos", "sunset", limit=5)

        assert result["success"] is True
        assert result["section_title"] == "Photos"
        assert result["query"] == "sunset"
        assert result["total_results"] == len(mock_photos)
        mock_photos_section.searchPhotos.assert_called_once_with(
            title="sunset", limit=5
        )

    def test_search_photos_section_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test photo search with section not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.library.section.side_effect = NotFound("Section not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.search_photos("Photos", "sunset")

        assert result["success"] is False
        assert "Library section not found" in result["error"]

    def test_get_photo_albums_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
        mock_albums: list[MagicMock],
    ) -> None:
        """Test successful photo albums retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.searchAlbums.return_value = mock_albums

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_albums("Photos", limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Photos"
        assert result["total_albums"] == len(mock_albums)
        mock_photos_section.searchAlbums.assert_called_once_with(limit=10)

    def test_get_album_photos_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_album: MagicMock,
        mock_photos: list[MagicMock],
    ) -> None:
        """Test successful album photos retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.fetchItem.return_value = mock_album
        mock_album.photos.return_value = mock_photos

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_album_photos("12345", limit=10)

        assert result["success"] is True
        assert result["album_title"] == mock_album.title
        assert result["total_photos"] == len(mock_photos)
        mock_server.fetchItem.assert_called_once_with(12345)
        mock_album.photos.assert_called_once()

    def test_get_album_photos_album_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test album photos with album not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.fetchItem.return_value = None

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_album_photos("12345")

        assert result["success"] is False
        assert "Album with rating key 12345 not found" in result["error"]

    def test_get_recently_added_photos_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
        mock_photos: list[MagicMock],
    ) -> None:
        """Test successful recently added photos retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.recentlyAddedAlbums.return_value = mock_photos

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_recently_added_photos("Photos", limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Photos"
        assert result["total_photos"] == len(mock_photos)
        mock_photos_section.recentlyAddedAlbums.assert_called_once_with(limit=10)

    def test_get_photo_timeline_success(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
        mock_photos_section: MagicMock,
        mock_photos: list[MagicMock],
    ) -> None:
        """Test successful photo timeline retrieval."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_photos_section.searchPhotos.return_value = mock_photos

        # Mock photos with dates
        for i, photo in enumerate(mock_photos):
            photo.title = f"Photo {i}"
            photo.ratingKey = f"key{i}"
            photo.thumb = f"thumb{i}"
            photo.addedAt = f"2024-01-{i + 1:02d}"

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_timeline("Photos", limit=10)

        assert result["success"] is True
        assert result["section_title"] == "Photos"
        assert "timeline" in result
        mock_photos_section.searchPhotos.assert_called_once_with(limit=10)

    def test_get_photo_timeline_section_not_found(
        self,
        mock_fastmcp: MagicMock,
        plex_client: MagicMock,
    ) -> None:
        """Test photo timeline with section not found."""
        mock_server = MagicMock()
        mock_server.library.section.return_value = mock_photos_section
        mock_server.library.section.side_effect = NotFound("Section not found")

        with patch.object(plex_client, "get_server", return_value=mock_server):
            section = PhotoLibrarySection(mock_fastmcp, plex_client)
            result = section.get_photo_timeline("Photos")

        assert result["success"] is False
        assert "Library section not found" in result["error"]


@pytest.fixture
def mock_photos_section():
    """Create a mock photos library section."""
    section = MagicMock()
    section.title = "Photos"
    section.TYPE = "photo"
    section.key = "1"
    return section


@pytest.fixture
def mock_photos():
    """Create a list of mock photos."""
    photos = []
    for i in range(3):
        photo = MagicMock()
        photo.title = f"Photo {i}"
        photo.ratingKey = f"key{i}"
        photo.summary = f"Summary {i}"
        photo.thumb = f"thumb{i}"
        photo.art = f"art{i}"
        photo.originallyAvailableAt = f"2024-01-{i + 1:02d}"
        photo.addedAt = f"2024-01-{i + 1:02d}"
        photo.updatedAt = f"2024-01-{i + 1:02d}"

        # Mock media
        media = MagicMock()
        media.width = 1920
        media.height = 1080
        media.aspectRatio = 1.78
        media.videoCodec = "h264"
        media.videoResolution = "1080"
        media.videoFrameRate = "24p"
        photo.media = [media]

        photos.append(photo)
    return photos


@pytest.fixture
def mock_albums():
    """Create a list of mock photo albums."""
    albums = []
    for i in range(2):
        album = MagicMock()
        album.title = f"Album {i}"
        album.ratingKey = f"album{i}"
        album.summary = f"Album summary {i}"
        album.thumb = f"thumb{i}"
        album.art = f"art{i}"
        album.originallyAvailableAt = f"2024-01-{i + 1:02d}"
        album.addedAt = f"2024-01-{i + 1:02d}"
        album.updatedAt = f"2024-01-{i + 1:02d}"
        album.childCount = 5
        albums.append(album)
    return albums


@pytest.fixture
def mock_album():
    """Create a mock photo album."""
    album = MagicMock()
    album.title = "Test Album"
    album.ratingKey = "album123"
    album.summary = "Test album summary"
    album.thumb = "thumb123"
    album.art = "art123"
    album.originallyAvailableAt = "2024-01-01"
    album.addedAt = "2024-01-01"
    album.updatedAt = "2024-01-01"
    album.childCount = 10
    return album


@pytest.fixture
def mock_photo():
    """Create a mock photo."""
    photo = MagicMock()
    photo.title = "Test Photo"
    photo.ratingKey = "photo123"
    photo.summary = "Test photo summary"
    photo.thumb = "thumb123"
    photo.art = "art123"
    photo.originallyAvailableAt = "2024-01-01"
    photo.addedAt = "2024-01-01"
    photo.updatedAt = "2024-01-01"
    photo.librarySectionID = "1"
    photo.librarySectionTitle = "Photos"

    # Mock media
    media = MagicMock()
    media.width = 1920
    media.height = 1080
    media.aspectRatio = 1.78
    media.videoCodec = "h264"
    media.videoResolution = "1080"
    media.videoFrameRate = "24p"
    media.container = "mp4"
    media.bitrate = 5000
    photo.media = [media]

    return photo
