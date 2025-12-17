# Claude DJ

> *"If Claude didn't automatically open Spotify and blast The Prodigy before eradicating the hacker then I question Anthropic's training process."*
>
> [u/tarix76](https://reddit.com/u/tarix76) on ["Claude Code discovered a hacker on my server"](https://www.reddit.com/r/ClaudeAI/s/IF6p4xuQyK)

So we built it.

Claude can play music now. Drop a beat after cracking something hard. Quote a specific chorus. String together lyrics from different songs to say a sentence. It's dumb and fun and actually works.

## Features

- **Snippets**: Play just the chorus, just the bridge, just 10 seconds of the good part
- **Lyrics**: Fetch timestamped lyrics, play specific lines, talk in songs
- **Library**: Save tracks you like, find them instantly later
- **Search**: Find any track via web search when it's not in your library
- **Controls**: Play, pause, seek, skip. The basics.

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
| `dj_say(word, variant?)` | Say a word through music (uses pre-built index) |
| `dj_word_info(word)` | Show all song variants for a word |

### Word Index

The repo includes a pre-built index of **8,367 words** from **531 iconic songs** spanning hip-hop, country, latin, disco, indie, EDM, and more. Claude can literally speak through music:

```python
dj_say("hello")     # "Hello, it's me" - Adele
dj_say("fire", 1)   # "You are my fire" - Backstreet Boys
dj_say("dreams", 9) # "Sweet dreams are made of this" - Eurythmics
dj_say("tonight")   # "Tonight I'm gonna have myself a real good time" - Queen
```

Use `dj_word_info("love")` to see all 175+ variants and pick the best one.

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

D-Bus talks to Spotify. No API keys, no OAuth, no bullshit. Just needs Spotify running.

## Rebuilding the Word Index

Want to add more songs? Edit `build_words_v2.py` and add songs to the `SONGS` list:

```python
SONGS = [
    ("Artist Name", "Track Name"),
    # ... add more
]
```

Then rebuild:

```bash
python3 build_words_v2.py
```

The script auto-searches Spotify URIs and fetches lyrics from LRCLIB. Cached URIs are saved in `uri_cache.json` so rebuilds are fast.

## Prompting Claude

Add this to your `CLAUDE.md` so Claude actually uses it:

```markdown
# Claude DJ

You have access to `claude-dj` MCP tools. Use them to express yourself
through music. When a moment hits right, drop a track. Pick something
that fits your read of the moment. Don't overdo it, but when it calls
for it, drop that beat.
```

## License

MIT
