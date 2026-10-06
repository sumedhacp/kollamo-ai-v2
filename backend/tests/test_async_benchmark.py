"""Large-Scale Asynchronous Micro-Batching Benchmark (3,500+ Comments Fixture)."""

import time
import pytest
from backend.app.services.sentiment_service import SentimentService
from backend.app.models.comment import Comment
from backend.app.models.prediction import Prediction
from backend.app.workers.tasks import compute_summary_metrics

# Base template snippets representing Malayalam, Manglish, Code-mixed, and English
COMMENT_TEMPLATES = [
    "ഈ സിനിമ തിയേറ്ററിൽ തന്നെ കാണണം, അതിഗംഭീര ദൃശ്യാനുഭവം!",
    "Padam kidilan aayirunnu bro, Fahadh Faasil vere level performance",
    "Average watch, first half kollam but second half valare lag aayi",
    "Worst movie experience, time and money wasted completely",
    "Music and BGM was good, but story and screenplay super weak",
    "ithu kandu njan shock aayi poyi, verum mass item!",
    "Bore padam, directing and acting disappointing",
    "Nalla cinema, family aayi koodi kandu enjoy cheyyaan pattiya padam",
    "Super climax twist, loved every moment of this film!",
    "Nothing special, just ordinary storytelling with no novelty",
]


def generate_benchmark_comments(count: int = 3500) -> list[str]:
    """Generates synthetic multi-script comment fixture with variation."""
    comments = []
    num_templates = len(COMMENT_TEMPLATES)
    for i in range(count):
        template = COMMENT_TEMPLATES[i % num_templates]
        comments.append(f"{template} [ref-{i}]")
    return comments


def test_micro_batch_3500_comments_benchmark():
    """Benchmarks sentiment prediction throughput and memory stability on 3,500+ comments."""
    service = SentimentService.get_instance()
    assert service.is_ready()

    fixture_comments = generate_benchmark_comments(3500)
    assert len(fixture_comments) == 3500

    start_time = time.perf_counter()

    # Process in micro-batches of 64
    batch_size = 64
    all_predictions = []
    for i in range(0, len(fixture_comments), batch_size):
        chunk = fixture_comments[i : i + batch_size]
        batch_preds = service.predictor.predict_batch(chunk)
        all_predictions.extend(batch_preds)

    elapsed_time = time.perf_counter() - start_time
    throughput = len(fixture_comments) / elapsed_time

    assert len(all_predictions) == 3500
    # Throughput benchmark: must exceed 100 comments/sec on baseline CPU
    assert throughput > 100.0, f"Throughput was {throughput:.2f} comments/sec"

    # Simulate metrics computation on all 3,500 predictions
    mock_pairs = []
    for i, pred in enumerate(all_predictions):
        comm = Comment(comment_id=f"bench_{i}", original_text=fixture_comments[i], like_count=(i % 50))
        p_obj = Prediction(
            comment_id=comm.comment_id,
            sentiment=pred["sentiment"],
            confidence=pred["confidence"],
            class_probabilities=pred["class_probabilities"],
        )
        mock_pairs.append((comm, p_obj))

    metrics = compute_summary_metrics(mock_pairs)
    total_count = sum(metrics["sentiment_counts"].values())
    total_pct = sum(metrics["sentiment_percentages"].values())

    assert total_count == 3500
    assert 99.8 <= total_pct <= 100.2
    assert metrics["engagement_metrics"]["total_likes"] > 0
    print(f"\n[BENCHMARK] 3,500 comments processed in {elapsed_time:.3f}s ({throughput:.1f} comments/sec)")
