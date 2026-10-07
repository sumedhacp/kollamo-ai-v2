"""YouTube URL and Video Identifier Parser."""

import re
from urllib.parse import parse_qs, urlparse
from app.services.youtube.errors import YouTubeInvalidVideoError

# Standard YouTube 11-character alphanumeric, underscore, hyphen ID pattern
YOUTUBE_VIDEO_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def extract_video_id(value: str) -> str:
    """Extracts and validates a canonical 11-character YouTube video ID from a URL or raw ID.

    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - Raw 11-character video ID

    Args:
        value: Input string containing a YouTube URL or video ID.

    Returns:
        The canonical 11-character YouTube video ID.

    Raises:
        YouTubeInvalidVideoError: If the input is empty, malformed, or not a recognized YouTube URL.
    """
    if not isinstance(value, str):
        raise YouTubeInvalidVideoError("Video URL or identifier must be a string.")

    cleaned = value.strip()
    if not cleaned:
        raise YouTubeInvalidVideoError("Video URL or identifier cannot be empty.")

    # Check if input is already a direct 11-character video ID
    if YOUTUBE_VIDEO_ID_REGEX.match(cleaned):
        return cleaned

    # Parse as URL
    try:
        parsed = urlparse(cleaned)
    except Exception as exc:
        raise YouTubeInvalidVideoError(f"Malformed URL: {exc}") from exc

    hostname = (parsed.hostname or "").lower()

    # Reject non-YouTube domains
    if hostname not in (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
        "www.youtu.be",
    ):
        raise YouTubeInvalidVideoError(
            f"Unsupported domain '{hostname}'. Expected a valid YouTube URL."
        )

    video_id: str | None = None

    # Handle youtu.be shortlinks: https://youtu.be/VIDEO_ID
    if hostname in ("youtu.be", "www.youtu.be"):
        path_segments = [seg for seg in parsed.path.split("/") if seg]
        if path_segments:
            candidate = path_segments[0]
            if YOUTUBE_VIDEO_ID_REGEX.match(candidate):
                video_id = candidate

    # Handle standard watch URLs: https://www.youtube.com/watch?v=VIDEO_ID
    elif parsed.path == "/watch":
        query_params = parse_qs(parsed.query)
        v_candidates = query_params.get("v", [])
        if v_candidates:
            candidate = v_candidates[0]
            if YOUTUBE_VIDEO_ID_REGEX.match(candidate):
                video_id = candidate

    # Handle shorts: https://www.youtube.com/shorts/VIDEO_ID
    elif parsed.path.startswith("/shorts/"):
        path_segments = [seg for seg in parsed.path.split("/") if seg]
        if len(path_segments) >= 2 and path_segments[0] == "shorts":
            candidate = path_segments[1]
            if YOUTUBE_VIDEO_ID_REGEX.match(candidate):
                video_id = candidate

    # Handle embed URLs: https://www.youtube.com/embed/VIDEO_ID
    elif parsed.path.startswith("/embed/"):
        path_segments = [seg for seg in parsed.path.split("/") if seg]
        if len(path_segments) >= 2 and path_segments[0] == "embed":
            candidate = path_segments[1]
            if YOUTUBE_VIDEO_ID_REGEX.match(candidate):
                video_id = candidate

    if not video_id:
        raise YouTubeInvalidVideoError(
            f"Could not extract a valid 11-character video ID from '{cleaned}'."
        )

    return video_id
