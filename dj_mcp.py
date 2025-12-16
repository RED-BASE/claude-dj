#!/usr/bin/env python3
"""
Claude DJ MCP - Musical Expression for Claude

Not just a music player - a way for Claude to EXPRESS things through music.
- Finish an epic hack? Drop a victory anthem
- Quote a specific bridge or chorus
- Play sequential clips to make a point
- Set the mood for the moment
"""

import subprocess
import time
import threading
import json
import re
import urllib.request
import urllib.parse
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("claude-dj")

# Track library path
TRACKS_FILE = Path(__file__).parent / "tracks.json"

SPOTIFY_DEST = "org.mpris.MediaPlayer2.spotify"
MPRIS_PATH = "/org/mpris/MediaPlayer2"
PLAYER_IFACE = "org.mpris.MediaPlayer2.Player"
PROPS_IFACE = "org.freedesktop.DBus.Properties"


def dbus_call(method: str, *args) -> str:
    """Call a D-Bus method on Spotify."""
    cmd = [
        "dbus-send", "--print-reply",
        f"--dest={SPOTIFY_DEST}",
        MPRIS_PATH,
        f"{PLAYER_IFACE}.{method}"
    ]
    cmd.extend(args)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout or result.stderr
    except subprocess.TimeoutExpired:
        return "Timeout waiting for Spotify"
    except Exception as e:
        return f"Error: {e}"


def dbus_get_property(prop: str) -> str:
    """Get a property from Spotify via D-Bus."""
    cmd = [
        "dbus-send", "--print-reply",
        f"--dest={SPOTIFY_DEST}",
        MPRIS_PATH,
        f"{PROPS_IFACE}.Get",
        f"string:{PLAYER_IFACE}",
        f"string:{prop}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Error: {e}"


def parse_metadata(raw: str) -> dict:
    """Parse D-Bus metadata output into a dict."""
    info = {}
    lines = raw.split('\n')

    for i, line in enumerate(lines):
        if 'xesam:title' in line:
            for j in range(i+1, min(i+3, len(lines))):
                if 'string "' in lines[j]:
                    info['title'] = lines[j].split('string "')[1].rstrip('"')
                    break
        elif 'xesam:artist' in line:
            for j in range(i+1, min(i+5, len(lines))):
                if 'string "' in lines[j]:
                    info['artist'] = lines[j].split('string "')[1].rstrip('"')
                    break
        elif 'xesam:album' in line:
            for j in range(i+1, min(i+3, len(lines))):
                if 'string "' in lines[j]:
                    info['album'] = lines[j].split('string "')[1].rstrip('"')
                    break
        elif 'mpris:trackid' in line:
            for j in range(i+1, min(i+3, len(lines))):
                if 'string "' in lines[j]:
                    info['uri'] = lines[j].split('string "')[1].rstrip('"')
                    break
        elif 'mpris:length' in line:
            for j in range(i+1, min(i+3, len(lines))):
                if 'int64' in lines[j] or 'uint64' in lines[j]:
                    try:
                        # Length in microseconds
                        us = int(lines[j].split()[-1])
                        info['length_sec'] = us / 1_000_000
                    except:
                        pass
                    break
    return info


def parse_status(raw: str) -> str:
    """Parse playback status from D-Bus output."""
    if 'string "Playing"' in raw:
        return "Playing"
    elif 'string "Paused"' in raw:
        return "Paused"
    elif 'string "Stopped"' in raw:
        return "Stopped"
    return "Unknown"


def get_position_sec() -> float:
    """Get current playback position in seconds."""
    raw = dbus_get_property("Position")
    for line in raw.split('\n'):
        if 'int64' in line or 'uint64' in line:
            try:
                return int(line.split()[-1]) / 1_000_000
            except:
                pass
    return 0.0


def seek_to(seconds: float):
    """Seek to absolute position (seconds from start)."""
    microseconds = int(seconds * 1_000_000)
    # SetPosition needs trackid and position
    meta_raw = dbus_get_property("Metadata")
    info = parse_metadata(meta_raw)
    trackid = info.get('uri', '')

    if trackid:
        cmd = [
            "dbus-send", "--print-reply",
            f"--dest={SPOTIFY_DEST}",
            MPRIS_PATH,
            f"{PLAYER_IFACE}.SetPosition",
            f"objpath:{trackid}",
            f"int64:{microseconds}"
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)


def stop_after_delay(delay_sec: float):
    """Stop playback after a delay (runs in background thread)."""
    time.sleep(delay_sec)
    dbus_call("Pause")


# ============ BASIC CONTROLS ============

@mcp.tool()
def dj_play() -> str:
    """Start/resume playback."""
    result = dbus_call("Play")
    if "Error" in result or "not provided" in result:
        return "Failed - is Spotify running?"
    return "Playing!"


@mcp.tool()
def dj_pause() -> str:
    """Pause playback."""
    result = dbus_call("Pause")
    if "Error" in result or "not provided" in result:
        return "Failed - is Spotify running?"
    return "Paused"


@mcp.tool()
def dj_toggle() -> str:
    """Toggle between play and pause."""
    result = dbus_call("PlayPause")
    if "Error" in result or "not provided" in result:
        return "Failed - is Spotify running?"
    status_raw = dbus_get_property("PlaybackStatus")
    return f"Toggled! Now: {parse_status(status_raw)}"


@mcp.tool()
def dj_next() -> str:
    """Skip to next track."""
    dbus_call("Next")
    return "Skipped to next track"


@mcp.tool()
def dj_previous() -> str:
    """Go to previous track."""
    dbus_call("Previous")
    return "Back to previous track"


# ============ INFO ============

@mcp.tool()
def dj_now_playing() -> str:
    """Get info about the currently playing track including position."""
    raw = dbus_get_property("Metadata")
    if "Error" in raw or "not provided" in raw:
        return "Spotify is not running or no track loaded"

    info = parse_metadata(raw)
    if not info:
        return "No track info available"

    status_raw = dbus_get_property("PlaybackStatus")
    status = parse_status(status_raw)
    position = get_position_sec()

    parts = []
    if 'title' in info:
        parts.append(f"Track: {info['title']}")
    if 'artist' in info:
        parts.append(f"Artist: {info['artist']}")
    if 'album' in info:
        parts.append(f"Album: {info['album']}")

    length = info.get('length_sec', 0)
    if length:
        parts.append(f"Position: {position:.1f}s / {length:.1f}s")
    else:
        parts.append(f"Position: {position:.1f}s")

    parts.append(f"Status: {status}")

    if 'uri' in info:
        parts.append(f"URI: {info['uri']}")

    return "\n".join(parts)


# ============ EXPRESSIVE CONTROLS ============

@mcp.tool()
def dj_open(uri: str) -> str:
    """
    Open a Spotify URI to play a track, album, or playlist.

    Get URIs from Spotify: Right-click > Share > Copy Spotify URI
    Examples:
    - spotify:track:4cOdK2wGLETKBW3PvgPWqT (Never Gonna Give You Up)
    - spotify:album:xxx
    - spotify:playlist:xxx
    """
    cmd = [
        "dbus-send", "--print-reply",
        f"--dest={SPOTIFY_DEST}",
        MPRIS_PATH,
        f"{PLAYER_IFACE}.OpenUri",
        f"string:{uri}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if "Error" in result.stderr:
            return f"Failed: {result.stderr}"
        time.sleep(0.5)  # Let it load
        return f"Now playing: {uri}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def dj_seek(seconds: float) -> str:
    """
    Seek to a specific position in the current track.

    Args:
        seconds: Position to seek to (e.g., 45.5 for 45.5 seconds in)
    """
    seek_to(seconds)
    time.sleep(0.2)
    actual = get_position_sec()
    return f"Seeked to {actual:.1f}s"


@mcp.tool()
def dj_snippet(uri: str, start_sec: float, duration_sec: float) -> str:
    """
    Play a specific snippet of a song - perfect for quoting a chorus,
    bridge, or iconic moment!

    Args:
        uri: Spotify URI (e.g., spotify:track:xxx)
        start_sec: When to start playing (seconds into the track)
        duration_sec: How long to play (e.g., 10 for 10 seconds)

    Example: Play the chorus of a song starting at 1:30 for 15 seconds
        dj_snippet("spotify:track:xxx", 90, 15)
    """
    # Open the track
    cmd = [
        "dbus-send", "--print-reply",
        f"--dest={SPOTIFY_DEST}",
        MPRIS_PATH,
        f"{PLAYER_IFACE}.OpenUri",
        f"string:{uri}"
    ]
    subprocess.run(cmd, capture_output=True, timeout=5)
    time.sleep(1.0)  # Let track load

    # Seek to start position
    seek_to(start_sec)
    time.sleep(0.3)

    # Make sure we're playing
    dbus_call("Play")

    # Schedule stop after duration
    stop_thread = threading.Thread(target=stop_after_delay, args=(duration_sec,))
    stop_thread.daemon = True
    stop_thread.start()

    return f"Playing snippet: {start_sec}s to {start_sec + duration_sec}s ({duration_sec}s)"


@mcp.tool()
def dj_drop(uri: str, start_sec: float = 0, duration_sec: float = 8) -> str:
    """
    Drop a musical moment - like a mic drop but with music!
    Quick way to punctuate a moment. Defaults to 8 seconds from the start.

    Great for:
    - Victory anthems after completing a task
    - Dramatic reveals
    - Celebratory moments

    Args:
        uri: Spotify URI
        start_sec: Where to start (default: 0, beginning)
        duration_sec: How long (default: 8 seconds)
    """
    return dj_snippet(uri, start_sec, duration_sec)


@mcp.tool()
def dj_position() -> str:
    """Get current playback position in seconds."""
    pos = get_position_sec()
    return f"Position: {pos:.1f} seconds"


# ============ TRACK LIBRARY ============

def load_tracks() -> dict:
    """Load tracks from JSON file."""
    if TRACKS_FILE.exists():
        try:
            return json.loads(TRACKS_FILE.read_text())
        except:
            return {}
    return {}


def save_tracks(tracks: dict):
    """Save tracks to JSON file."""
    TRACKS_FILE.write_text(json.dumps(tracks, indent=2))


@mcp.tool()
def dj_find(query: str) -> str:
    """
    Find a track URI from your personal library.

    Searches your tracks.json for matching entries.
    Uses fuzzy matching - partial matches work.

    Args:
        query: Search term (e.g., "m83", "blinding", "outro")

    Returns the Spotify URI if found, or suggestions if not.
    """
    tracks = load_tracks()
    query_lower = query.lower()

    # Exact match
    if query_lower in tracks:
        return tracks[query_lower]

    # Fuzzy match - find keys containing query
    matches = [(k, v) for k, v in tracks.items() if query_lower in k]

    if len(matches) == 1:
        return matches[0][1]
    elif len(matches) > 1:
        options = "\n".join([f"  - {k}" for k, v in matches])
        return f"Multiple matches:\n{options}"
    else:
        available = ", ".join(list(tracks.keys())[:10])
        return f"Not found. Available: {available}..."


@mcp.tool()
def dj_save(name: str, uri: str) -> str:
    """
    Save a track to your personal library for quick access later.

    Args:
        name: A memorable name/key (e.g., "m83 outro", "victory song")
        uri: The Spotify URI (e.g., spotify:track:xxx)

    Example: dj_save("chill vibes", "spotify:track:xxx")
    """
    tracks = load_tracks()
    tracks[name.lower()] = uri
    save_tracks(tracks)
    return f"Saved '{name}' -> {uri}"


@mcp.tool()
def dj_library() -> str:
    """List all tracks in your personal library."""
    tracks = load_tracks()
    if not tracks:
        return "Library is empty. Use dj_save to add tracks!"

    lines = [f"  {k}: {v}" for k, v in sorted(tracks.items())]
    return f"Your library ({len(tracks)} tracks):\n" + "\n".join(lines)


@mcp.tool()
def dj_search(query: str) -> str:
    """
    Search for a track online and return Spotify URI.

    Uses DuckDuckGo to find the Spotify link, then converts to URI.
    Slower than dj_find but works for any track.

    Args:
        query: Search term (e.g., "M83 Outro", "Daft Punk Digital Love")
    """
    try:
        # Search DuckDuckGo HTML (no JS needed)
        search_query = urllib.parse.quote(f"{query} spotify track")
        url = f"https://html.duckduckgo.com/html/?q={search_query}"

        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')

        # Find Spotify track URLs
        pattern = r'open\.spotify\.com/track/([a-zA-Z0-9]+)'
        matches = re.findall(pattern, html)

        if matches:
            track_id = matches[0]
            uri = f"spotify:track:{track_id}"
            return uri
        else:
            return f"No Spotify track found for '{query}'"

    except Exception as e:
        return f"Search failed: {e}"


if __name__ == "__main__":
    mcp.run()
