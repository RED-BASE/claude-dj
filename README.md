# Claude DJ

**Musical expression for Claude** — not just a music player, a way for Claude to *emphasize* moments with music.

Finished cracking a tough problem? Drop a beat. Want to quote a specific chorus? Jump there and play 10 seconds. This tool lets Claude express itself through music, proactively and intentionally.

## Features

- **Snippet playback** — Play a specific part of any song (e.g., just the chorus, just the bridge)
- **Musical punctuation** — Quick drops to emphasize moments
- **Personal library** — Save tracks for instant access
- **Web search fallback** — Find any track via DuckDuckGo when not in library
- **Full playback control** — Play, pause, seek, skip

## Requirements

- **Linux** with D-Bus (works out of the box on most distros)
- **Spotify desktop app** (snap, deb, or flatpak)
- **Python 3.8+** with `mcp` package

## Installation

### 1. Install Spotify

```bash
# Via snap (easiest)
sudo apt install snapd
sudo snap install spotify

# Or via apt
curl -sS https://download.spotify.com/debian/pubkey_6224F9941A8AA6D1.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/spotify.gpg
echo "deb [signed-by=/etc/apt/keyrings/spotify.gpg] http://repository.spotify.com stable non-free" | sudo tee /etc/apt/sources.list.d/spotify.list
sudo apt update && sudo apt install spotify-client
```

### 2. Install the MCP

```bash
# Clone the repo
git clone https://github.com/RED-BASE/claude-dj.git
cd claude-dj

# Install Python MCP dependency
pip install mcp
```

### 3. Configure Claude Code

Add to your `~/.claude.json` under your project's `mcpServers`:

```json
{
  "claude-dj": {
    "type": "stdio",
    "command": "python3",
    "args": ["/path/to/claude-dj/dj_mcp.py"],
    "env": {}
  }
}
```

Or add to a project-level `.mcp.json`:

```json
{
  "mcpServers": {
    "claude-dj": {
      "type": "stdio",
      "command": "python3",
      "args": ["./dj_mcp.py"]
    }
  }
}
```

### 4. Start Spotify

Make sure Spotify is running before using the tools:

```bash
spotify &
# Or if using snap:
/snap/bin/spotify &
```

## Tools

### Playback Control

| Tool | Description |
|------|-------------|
| `dj_play()` | Start/resume playback |
| `dj_pause()` | Pause playback |
| `dj_toggle()` | Toggle play/pause |
| `dj_next()` | Skip to next track |
| `dj_previous()` | Go to previous track |

### Info

| Tool | Description |
|------|-------------|
| `dj_now_playing()` | Get current track info + position |
| `dj_position()` | Get current playback position |

### Expressive Controls

| Tool | Description |
|------|-------------|
| `dj_open(uri)` | Play a Spotify URI |
| `dj_seek(seconds)` | Jump to a position in the current track |
| `dj_snippet(uri, start_sec, duration_sec)` | Play a specific part of a song |
| `dj_drop(uri, start_sec?, duration_sec?)` | Quick musical punctuation (defaults to 8s) |

### Library Management

| Tool | Description |
|------|-------------|
| `dj_find(query)` | Instant lookup from personal library |
| `dj_search(query)` | Web search for any track (returns URI) |
| `dj_save(name, uri)` | Save a track to your library |
| `dj_library()` | List all saved tracks |

### Lyrics & Musical Speech

| Tool | Description |
|------|-------------|
| `dj_lyrics(artist, track)` | Get timestamped lyrics from LRCLIB |
| `dj_speak(uri, artist, track, line_number, duration)` | Play a specific lyric line |

## Usage Examples

### Play a specific snippet

```python
# Play the chorus of M83 - Outro (starts at 1:43, play for 30 seconds)
dj_snippet("spotify:track:2QVmiA93GVhWNTWQctyY1K", 103, 30)
```

### Quick musical drop

```python
# 8-second drop from the start
dj_drop("spotify:track:0VjIjW4GlUZAMYd2vXMi3b")

# Or from a specific point
dj_drop("spotify:track:xxx", start_sec=45, duration_sec=10)
```

### Build your library

```python
# Search for a track
dj_search("Daft Punk Digital Love")
# Returns: spotify:track:2VEZx7NWsZ1D0eJ4uv5Fym

# Save it for instant access later
dj_save("digital love", "spotify:track:2VEZx7NWsZ1D0eJ4uv5Fym")

# Now find it instantly
dj_find("digital")
# Returns: spotify:track:2VEZx7NWsZ1D0eJ4uv5Fym
```

### Musical speech with lyrics

String together lines from different songs to say something:

```python
# "Hello... World!"
dj_speak(uri_adele, "Adele", "Hello", 1, 1.5)         # "Hello"
dj_speak(uri_armstrong, "Louis Armstrong", "What A Wonderful World", 4, 2)  # "World"

# Get lyrics to find the right lines
dj_lyrics("M83", "Outro")
# [1:41.11] I was the king of my own land
# [2:17.03] Now and forever, I'm your king!
```

## Getting Spotify URIs

Right-click any track in Spotify → **Share** → **Copy Spotify URI**

Format: `spotify:track:XXXXXXXXXXXXXXXXXXXX`

## How It Works

Uses the **D-Bus MPRIS protocol** to control Spotify — no API keys needed, no OAuth, just needs Spotify running. Works with any MPRIS-compatible player.

## Prompting Claude

Add this to your `CLAUDE.md` to encourage expressive use:

```markdown
# Claude DJ - Musical Expression

You have access to `claude-dj` MCP tools. Use them to EXPRESS yourself
through music - not just when asked, but proactively to punctuate moments.

Music is expression. When a moment hits right - you just finished cracking
something, revealed a cool insight, or the energy shifts - drop a track.
Pick something that fits YOUR read of the moment. No presets, no rules.
Just feel it.
```

## License

MIT
