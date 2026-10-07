"""Deterministic Unit and Integration Tests for YouTube Ingestion Service (Sections 38, 39, 40)."""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import pytest

from app.schemas.youtube import YouTubeComment, YouTubeVideo, YouTubeIngestionResult
from app.services.youtube.service import YouTubeIngestionService
from app.services.youtube.errors import (
    YouTubeCommentsDisabledError,
    YouTubeQuotaExceededError,
    YouTubeVideoNotFoundError,
)


class MockYouTubeClient:
    """Mock client returning controllable metadata and paginated comments."""

    def __init__(
        self,
        total_mock_comments: int = 150,
        page_size: int = 100,
        comments_disabled: bool = False,
        video_not_found: bool = False,
        quota_exceeded: bool = False,
        custom_comments: Optional[List[Dict[str, Any]]] = None,
    ):
        self.total_mock_comments = total_mock_comments
        self.page_size = page_size
        self.comments_disabled = comments_disabled
        self.video_not_found = video_not_found
        self.quota_exceeded = quota_exceeded
        self.custom_comments = custom_comments
        self.fetch_calls = 0

    async def fetch_video_metadata(self, video_id: str) -> YouTubeVideo:
        if self.video_not_found:
            raise YouTubeVideoNotFoundError(f"Video '{video_id}' not found.")
        if self.quota_exceeded:
            raise YouTubeQuotaExceededError("Quota exceeded.")
        return YouTubeVideo(
            video_id=video_id,
            title="Aavesham Official Trailer",
            channel_title="Fahadh Faasil and Friends",
            published_at=datetime(2024, 4, 1, 10, 0, 0, tzinfo=timezone.utc),
            description="Official trailer for Malayalam movie Aavesham",
            view_count=12000000,
            like_count=350000,
            comment_count=15000,
        )

    async def fetch_comment_threads(
        self,
        video_id: str,
        max_results: int = 100,
        page_token: Optional[str] = None,
        order: str = "time",
    ) -> Dict[str, Any]:
        self.fetch_calls += 1
        if self.comments_disabled:
            raise YouTubeCommentsDisabledError("Comments disabled.")
        if self.quota_exceeded:
            raise YouTubeQuotaExceededError("Quota exceeded.")

        # If custom comments provided, paginate through them
        if self.custom_comments is not None:
            start_idx = int(page_token) if page_token else 0
            end_idx = min(start_idx + max_results, len(self.custom_comments))
            slice_items = self.custom_comments[start_idx:end_idx]
            next_token = str(end_idx) if end_idx < len(self.custom_comments) else None
            return {"items": slice_items, "nextPageToken": next_token}

        # Otherwise generate synthetic items
        current_offset = int(page_token) if page_token else 0
        end_offset = min(current_offset + max_results, self.total_mock_comments)

        items = []
        base_time = datetime(2024, 4, 2, 0, 0, 0, tzinfo=timezone.utc)
        for i in range(current_offset, end_offset):
            items.append({
                "id": f"comment_{i}",
                "snippet": {
                    "topLevelComment": {
                        "id": f"comment_{i}",
                        "snippet": {
                            "authorDisplayName": f"User {i}",
                            "textOriginal": f"Comment text {i}",
                            "publishedAt": (base_time + timedelta(minutes=i)).isoformat(),
                            "updatedAt": (base_time + timedelta(minutes=i)).isoformat(),
                            "likeCount": i * 5,
                        },
                    }
                },
            })

        next_page = str(end_offset) if end_offset < self.total_mock_comments else None
        return {"items": items, "nextPageToken": next_page}

    def parse_comment_item(self, item: Dict[str, Any], video_id: str) -> YouTubeComment:
        snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        pub_str = snippet.get("publishedAt")
        pub_dt = datetime.fromisoformat(pub_str) if pub_str else None
        return YouTubeComment(
            comment_id=item.get("id", "c_id"),
            video_id=video_id,
            author_name=snippet.get("authorDisplayName", "Anon"),
            text=snippet.get("textOriginal", ""),
            published_at=pub_dt,
            updated_at=pub_dt,
            like_count=int(snippet.get("likeCount", 0)),
        )


@pytest.mark.asyncio
async def test_service_limit_50():
    """Service requests at most 50 comments and makes exactly 1 page call."""
    mock_client = MockYouTubeClient(total_mock_comments=200)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=50, sort_by="newest")

    assert result.returned_count == 50
    assert len(result.comments) == 50
    assert result.requested_limit == 50
    assert mock_client.fetch_calls == 1


@pytest.mark.asyncio
async def test_service_limit_100():
    """Service returns 100 comments with 1 page call."""
    mock_client = MockYouTubeClient(total_mock_comments=200)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=100, sort_by="newest")

    assert result.returned_count == 100
    assert len(result.comments) == 100
    assert mock_client.fetch_calls == 1


@pytest.mark.asyncio
async def test_service_limit_250_pagination():
    """Service paginates across 3 pages to collect 250 comments."""
    mock_client = MockYouTubeClient(total_mock_comments=500)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=250, sort_by="newest")

    assert result.returned_count == 250
    assert len(result.comments) == 250
    assert mock_client.fetch_calls == 3


@pytest.mark.asyncio
async def test_service_limit_500():
    """Service paginates across 5 pages to collect 500 comments."""
    mock_client = MockYouTubeClient(total_mock_comments=600)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=500, sort_by="newest")

    assert result.returned_count == 500
    assert len(result.comments) == 500
    assert mock_client.fetch_calls == 5


@pytest.mark.asyncio
async def test_service_limit_all():
    """Service exhausts all available comments when limit is 'ALL'."""
    mock_client = MockYouTubeClient(total_mock_comments=120)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit="ALL", sort_by="newest")

    assert result.returned_count == 120
    assert len(result.comments) == 120
    assert result.requested_limit == "ALL"


@pytest.mark.asyncio
async def test_service_fewer_comments_than_requested():
    """Service gracefully returns fewer comments if video has less than requested limit."""
    mock_client = MockYouTubeClient(total_mock_comments=15)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=100, sort_by="newest")

    assert result.returned_count == 15
    assert len(result.comments) == 15


@pytest.mark.asyncio
async def test_service_empty_comments():
    """Service returns empty comment list if video has 0 comments."""
    mock_client = MockYouTubeClient(total_mock_comments=0)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=100)

    assert result.returned_count == 0
    assert result.comments == []


@pytest.mark.asyncio
async def test_service_language_and_unicode_preservation():
    """Verifies that Malayalam, English, Manglish, Code-mixed, and Emojis are preserved verbatim (Section 39)."""
    test_texts = [
        "ഇത് വളരെ നല്ല സിനിമയാണ്",  # Malayalam
        "This movie was excellent.",  # English
        "Ithu poli movie aanu",  # Manglish
        "ഇത് really നല്ല movie ആണ്",  # Code-mixed
        "സൂപ്പർ സിനിമ 🔥❤️🎉",  # Emojis + Malayalam
    ]

    custom_items = [
        {
            "id": f"lang_{idx}",
            "snippet": {
                "topLevelComment": {
                    "id": f"lang_{idx}",
                    "snippet": {
                        "authorDisplayName": f"User {idx}",
                        "textOriginal": txt,
                        "publishedAt": "2024-04-02T12:00:00Z",
                        "likeCount": idx * 10,
                    },
                }
            },
        }
        for idx, txt in enumerate(test_texts)
    ]

    mock_client = MockYouTubeClient(custom_comments=custom_items)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", comment_limit=50)

    assert result.returned_count == 5
    collected_texts = [c.text for c in result.comments]
    for orig in test_texts:
        assert orig in collected_texts


@pytest.mark.asyncio
async def test_service_sorting_most_liked():
    """Verifies most_liked sorting places highest like_count first (Section 40)."""
    comments_data = [
        {"id": "c1", "likes": 10, "time": "2024-04-01T12:00:00Z"},
        {"id": "c2", "likes": 500, "time": "2024-04-02T12:00:00Z"},
        {"id": "c3", "likes": 50, "time": "2024-04-03T12:00:00Z"},
        {"id": "c4", "likes": 500, "time": "2024-04-04T12:00:00Z"},  # Tie: newer wins
    ]
    custom_items = [
        {
            "id": d["id"],
            "snippet": {
                "topLevelComment": {
                    "id": d["id"],
                    "snippet": {
                        "authorDisplayName": "User",
                        "textOriginal": f"Text {d['id']}",
                        "publishedAt": d["time"],
                        "likeCount": d["likes"],
                    },
                }
            },
        }
        for d in comments_data
    ]

    mock_client = MockYouTubeClient(custom_comments=custom_items)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", sort_by="most_liked")
    ids = [c.comment_id for c in result.comments]

    assert ids[0] == "c4"  # 500 likes, 2024-04-04
    assert ids[1] == "c2"  # 500 likes, 2024-04-02
    assert ids[2] == "c3"  # 50 likes
    assert ids[3] == "c1"  # 10 likes


@pytest.mark.asyncio
async def test_service_sorting_newest():
    """Verifies newest sorting places latest published_at first."""
    comments_data = [
        {"id": "old", "likes": 100, "time": "2024-04-01T10:00:00Z"},
        {"id": "newest", "likes": 0, "time": "2024-04-03T10:00:00Z"},
        {"id": "middle", "likes": 50, "time": "2024-04-02T10:00:00Z"},
    ]
    custom_items = [
        {
            "id": d["id"],
            "snippet": {
                "topLevelComment": {
                    "id": d["id"],
                    "snippet": {
                        "authorDisplayName": "User",
                        "textOriginal": f"Text {d['id']}",
                        "publishedAt": d["time"],
                        "likeCount": d["likes"],
                    },
                }
            },
        }
        for d in comments_data
    ]

    mock_client = MockYouTubeClient(custom_comments=custom_items)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", sort_by="newest")
    ids = [c.comment_id for c in result.comments]

    assert ids == ["newest", "middle", "old"]


@pytest.mark.asyncio
async def test_service_sorting_oldest():
    """Verifies oldest sorting places earliest published_at first."""
    comments_data = [
        {"id": "old", "likes": 100, "time": "2024-04-01T10:00:00Z"},
        {"id": "newest", "likes": 0, "time": "2024-04-03T10:00:00Z"},
        {"id": "middle", "likes": 50, "time": "2024-04-02T10:00:00Z"},
    ]
    custom_items = [
        {
            "id": d["id"],
            "snippet": {
                "topLevelComment": {
                    "id": d["id"],
                    "snippet": {
                        "authorDisplayName": "User",
                        "textOriginal": f"Text {d['id']}",
                        "publishedAt": d["time"],
                        "likeCount": d["likes"],
                    },
                }
            },
        }
        for d in comments_data
    ]

    mock_client = MockYouTubeClient(custom_comments=custom_items)
    service = YouTubeIngestionService(client=mock_client)

    result = await service.ingest("https://youtu.be/dQw4w9WgXcQ", sort_by="oldest")
    ids = [c.comment_id for c in result.comments]

    assert ids == ["old", "middle", "newest"]


@pytest.mark.asyncio
async def test_service_comments_disabled_bubbles_up():
    """Service propagates YouTubeCommentsDisabledError without masking."""
    mock_client = MockYouTubeClient(comments_disabled=True)
    service = YouTubeIngestionService(client=mock_client)

    with pytest.raises(YouTubeCommentsDisabledError):
        await service.ingest("https://youtu.be/dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_service_video_not_found_bubbles_up():
    """Service propagates YouTubeVideoNotFoundError without masking."""
    mock_client = MockYouTubeClient(video_not_found=True)
    service = YouTubeIngestionService(client=mock_client)

    with pytest.raises(YouTubeVideoNotFoundError):
        await service.ingest("https://youtu.be/dQw4w9WgXcQ")


@pytest.mark.asyncio
async def test_service_quota_exceeded_bubbles_up():
    """Service propagates YouTubeQuotaExceededError without masking."""
    mock_client = MockYouTubeClient(quota_exceeded=True)
    service = YouTubeIngestionService(client=mock_client)

    with pytest.raises(YouTubeQuotaExceededError):
        await service.ingest("https://youtu.be/dQw4w9WgXcQ")
