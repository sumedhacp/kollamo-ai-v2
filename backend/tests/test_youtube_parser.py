"""Unit Tests for YouTube Video URL and ID Parser (Section 37)."""

import pytest
from app.services.youtube.parser import extract_video_id
from app.services.youtube.errors import YouTubeInvalidVideoError


def test_parser_standard_watch_url():
    """Extracts video ID from standard desktop watch URLs."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_mobile_watch_url():
    """Extracts video ID from mobile YouTube URLs."""
    url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_short_url():
    """Extracts video ID from youtu.be shortlinks."""
    url = "https://youtu.be/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_shorts_url():
    """Extracts video ID from YouTube Shorts URLs."""
    url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_embed_url():
    """Extracts video ID from embedded YouTube URLs."""
    url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_raw_video_id():
    """Accepts a canonical raw 11-character video ID."""
    raw_id = "dQw4w9WgXcQ"
    assert extract_video_id(raw_id) == "dQw4w9WgXcQ"


def test_parser_url_with_unrelated_query_parameters():
    """Ensures extra query parameters do not corrupt extracted video ID."""
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=43s&feature=shared&list=PL123"
    assert extract_video_id(url) == "dQw4w9WgXcQ"

    short_url = "https://youtu.be/dQw4w9WgXcQ?si=abcde12345&t=10"
    assert extract_video_id(short_url) == "dQw4w9WgXcQ"


def test_parser_whitespace_stripping():
    """Ensures leading and trailing whitespace is stripped."""
    url = "   \n\t https://youtu.be/dQw4w9WgXcQ \t  \n"
    assert extract_video_id(url) == "dQw4w9WgXcQ"


def test_parser_empty_string_rejected():
    """Rejects empty string input."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("")


def test_parser_whitespace_only_rejected():
    """Rejects whitespace-only input."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("   \n\t  ")


def test_parser_non_string_rejected():
    """Rejects non-string inputs."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id(12345)


def test_parser_random_non_youtube_url_rejected():
    """Rejects URLs from arbitrary non-YouTube domains."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("https://www.google.com")

    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("https://vimeo.com/123456789")


def test_parser_malformed_youtube_url_rejected():
    """Rejects YouTube URLs without a video ID."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("https://www.youtube.com/watch")

    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("https://www.youtube.com/watch?other=123")


def test_parser_invalid_length_id_rejected():
    """Rejects IDs that do not conform to canonical 11-character length."""
    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("short")

    with pytest.raises(YouTubeInvalidVideoError):
        extract_video_id("this_video_id_is_way_too_long_to_be_valid")
