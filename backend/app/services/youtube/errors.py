"""Custom Exceptions for YouTube Ingestion and Comment Collection."""

from typing import Optional, Dict, Any


class YouTubeError(Exception):
    """Base exception for all YouTube ingestion errors."""

    def __init__(
        self,
        message: str,
        code: str = "YOUTUBE_API_ERROR",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class YouTubeConfigError(YouTubeError):
    """Raised when YouTube API key is missing or not configured."""

    def __init__(
        self,
        message: str = "YouTube API key is not configured. Please set YOUTUBE_API_KEY in the server environment.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_CONFIG_ERROR",
            status_code=503,
            details=details,
        )


class YouTubeInvalidVideoError(YouTubeError):
    """Raised when a video URL or identifier is structurally invalid or unsupported."""

    def __init__(
        self,
        message: str = "Invalid YouTube video URL or identifier.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_INVALID_VIDEO",
            status_code=400,
            details=details,
        )


class YouTubeVideoNotFoundError(YouTubeError):
    """Raised when a video does not exist or is marked private on YouTube."""

    def __init__(
        self,
        message: str = "The requested YouTube video was not found or is private.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_VIDEO_NOT_FOUND",
            status_code=404,
            details=details,
        )


class YouTubeCommentsDisabledError(YouTubeError):
    """Raised when comments are disabled on the requested YouTube video."""

    def __init__(
        self,
        message: str = "Comments are disabled on this YouTube video.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_COMMENTS_DISABLED",
            status_code=422,
            details=details,
        )


class YouTubeQuotaExceededError(YouTubeError):
    """Raised when YouTube Data API quota has been exhausted."""

    def __init__(
        self,
        message: str = "YouTube Data API daily quota has been exceeded. Please try again later.",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_QUOTA_EXCEEDED",
            status_code=429,
            details=details,
        )


class YouTubeAPIError(YouTubeError):
    """Raised on upstream YouTube Data API failures or transient network errors."""

    def __init__(
        self,
        message: str = "An error occurred while communicating with the YouTube Data API.",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=message,
            code="YOUTUBE_API_ERROR",
            status_code=status_code,
            details=details,
        )
