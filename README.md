# 🎬 Plex MCP Server

A Model Context Protocol (MCP) server that enables AI assistants to interact with your Plex Media Server! 🚀

## ✨ Features

### 🎥 Movies
- **Search movies** by title, genre, year, or rating
- **Browse recently added** movies
- **Get detailed movie info** including cast, directors, and ratings
- **Filter by year ranges** and rating criteria

### 🎵 Music
- **Search music tracks** and artists
- **Create and manage playlists**
- **Get random tracks by decade** for discovery
- **Browse music library** information

### 📺 TV Shows
- **Search TV shows** and episodes
- **Browse episodes by season**
- **Get detailed episode information**
- **Find recently added shows**

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- A running Plex Media Server
- Plex authentication token

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/plex-mcp.git
cd plex-mcp

# Install dependencies
pip install -e .
```

### Configuration

Set up your Plex server credentials:

```bash
export PLEX_BASEURL="http://localhost:32400"  # Your Plex server URL
export PLEX_TOKEN="your-plex-token-here"      # Your Plex token
```

**Finding your Plex token:**
1. Go to your Plex server web interface
2. Navigate to Settings → Network
3. Look for "Plex Token" or use browser dev tools to find the `X-Plex-Token` header

### Running the Server

```bash
plex-mcp
```

### MCP Server Configuration

To use this server with an MCP client (like Cursor), add this configuration to your MCP settings:

```json
{
  "mcpServers": {
    "plex-mcp": {
      "command": "uv",
      "args": [
        "run",
        "plex-mcp",
        "--baseurl",
        "<PLEX_BASEURL>",
        "--token",
        "<PLEX_TOKEN>"
      ]
    }
  }
}
```

Replace `<PLEX_BASEURL>` / `<PLEX_TOKEN>` with your actual Plex server URL and authentication token.

## 🎯 Sample Use Cases

### 🎬 Movie Discovery
```
"Find all sci-fi movies from the 80s with ratings above 7.0"
"Show me recently added action movies"
"What are the highest rated movies in my library?"
```

### 🎵 Music Curation
```
"Create a playlist of random 90s rock songs"
"Find all tracks by The Beatles"
"Show me my most recently added music"
```

### 📺 TV Show Management
```
"List all episodes of Breaking Bad season 1"
"Find shows I haven't watched yet"
"What's the latest episode of The Office?"
```

### 🔍 Smart Search
```
"Find movies similar to Inception"
"Show me horror movies from the last 5 years"
"Create a workout playlist with high-energy songs"
```

## 🛠️ Available Tools

### Movies 🎥
- `search_movies` - Search movies by title
- `get_movies_library` - Get library information
- `get_movie_info` - Detailed movie information
- `search_movies_by_genre` - Filter by genre
- `search_movies_by_year` - Filter by year/range
- `get_recently_added_movies` - Latest additions
- `get_movies_by_rating` - Filter by rating

### Music 🎵
- `search_music_tracks` - Search music library
- `get_music_library` - Library information
- `create_music_playlist` - Create playlists
- `get_random_tracks_by_decade` - Random discovery
- `search_tracks_by_artist` - Artist-specific search
- `get_playlist_info` - Playlist details
- `delete_playlist` - Remove playlists

### TV Shows 📺
- `search_tv_shows` - Search TV library
- `get_tv_shows_library` - Library information
- `get_show_episodes` - Episode listings
- `get_episode_info` - Episode details
- `search_episodes_by_show` - Show-specific episodes
- `get_recently_added_shows` - Latest additions

## 🔧 Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run linting
uv run ruff check --fix && uv run ruff format

# Run tests
pytest
```

### Project Structure

```
src/plex_mcp/
├── client/           # Plex API client
├── sections/         # Media type handlers
│   ├── movies.py     # Movie operations
│   ├── music.py      # Music operations
│   └── tv_shows.py   # TV show operations
└── __init__.py       # Main server entry point
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp) framework
- Uses [PlexAPI](https://github.com/pkkid/python-plexapi) for Plex integration
- Inspired by the Model Context Protocol specification

---

**Happy streaming! 🎬🎵📺**
