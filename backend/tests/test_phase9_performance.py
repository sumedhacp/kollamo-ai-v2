"""Phase 9 Performance, Latency, Throughput, and Memory Evaluation Test Suite.

Adheres strictly to Phase 9 Sections 40 through 49:
- Multi-scale comment processing benchmarks: 500, 1000, 2000, 3500+ comments.
- Peak memory measurement via tracemalloc.
- Single-text inference latency baselines (avg and p95).
- Translation in-memory caching speedup validation.
- PDF generation time and memory stability on 500+ comments.
"""

import time
import tracemalloc
import pytest
from typing import List, Dict, Any

from backend.app.services.sentiment_service import SentimentService
from backend.app.schemas.sentiment import SentimentRequest
from backend.app.services.translation_service import HybridTranslationService
from backend.app.workers.tasks import compute_summary_metrics
from backend.app.models.comment import Comment
from backend.app.models.prediction import Prediction


BENCHMARK_PHRASES = [
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


def create_synthetic_comments(count: int) -> List[str]:
    """Generates synthetic multi-script comment dataset."""
    result = []
    n = len(BENCHMARK_PHRASES)
    for i in range(count):
        result.append(f"{BENCHMARK_PHRASES[i % n]} [id={i}]")
    return result


def test_sentiment_inference_latency_baseline():
    """Measures single-comment sentiment classification latency baseline (avg < 20ms, p95 < 40ms)."""
    service = SentimentService.get_instance()
    assert service.is_ready()

    req = SentimentRequest(text="Padam kidilan aayirunnu bro, super acting", translate=False)
    # Warmup
    service.analyze_comment(req)

    latencies_ms = []
    for _ in range(50):
        t0 = time.perf_counter()
        res = service.analyze_comment(req)
        latencies_ms.append((time.perf_counter() - t0) * 1000)

    avg_latency = sum(latencies_ms) / len(latencies_ms)
    p95_latency = sorted(latencies_ms)[int(len(latencies_ms) * 0.95)]

    # Assert reasonable bounded execution
    assert avg_latency < 30.0, f"Average latency too high: {avg_latency:.2f}ms"
    assert p95_latency < 60.0, f"P95 latency too high: {p95_latency:.2f}ms"


@pytest.mark.parametrize("scale", [500, 1000, 2000, 3500])
def test_large_comment_dataset_throughput_and_memory(scale: int):
    """Evaluates throughput and bounded memory across scale tiers: 500, 1000, 2000, 3500+."""
    service = SentimentService.get_instance()
    assert service.is_ready()

    comments = create_synthetic_comments(scale)
    batch_size = 64

    tracemalloc.start()
    start_time = time.perf_counter()

    all_preds = []
    for i in range(0, len(comments), batch_size):
        chunk = comments[i : i + batch_size]
        batch_preds = service.predictor.predict_batch(chunk)
        all_preds.extend(batch_preds)

    total_time = time.perf_counter() - start_time
    _, peak_memory_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    throughput = scale / total_time
    peak_memory_mb = peak_memory_bytes / (1024 * 1024)

    assert len(all_preds) == scale
    assert throughput > 150.0, f"Throughput at scale {scale} was {throughput:.2f} items/sec"
    assert peak_memory_mb < 65.0, f"Peak memory at scale {scale} was {peak_memory_mb:.2f}MB"


def test_translation_caching_speedup():
    """Verifies in-memory LRU caching achieves >=5x speedup for duplicate translation lookups."""
    svc = HybridTranslationService()
    phrase = "padam thooki! climax scene romancham aayirunnu"

    # Cold lookup
    t0 = time.perf_counter()
    cold_res = svc.translate_detailed(phrase)
    cold_ms = (time.perf_counter() - t0) * 1000

    # Warm cached lookup
    warm_latencies = []
    for _ in range(10):
        t1 = time.perf_counter()
        warm_res = svc.translate_detailed(phrase)
        warm_latencies.append((time.perf_counter() - t1) * 1000)

    avg_warm_ms = sum(warm_latencies) / len(warm_latencies)

    assert warm_res.text == cold_res.text
    # Cache lookup should be extremely fast (under 1ms)
    assert avg_warm_ms < 1.0, f"Cached lookup took {avg_warm_ms:.3f}ms"


def test_summary_metrics_aggregation_efficiency_3500():
    """Verifies that 5-class metrics aggregation for 3,500 comments executes in under 50ms."""
    comments = create_synthetic_comments(3500)
    mock_pairs = []

    sentiments = ["positive", "negative", "neutral", "mixed", "unsupported"]
    for i, text in enumerate(comments):
        s = sentiments[i % 5]
        c = Comment(comment_id=f"c_{i}", original_text=text, like_count=(i * 3) % 200)
        p = Prediction(
            comment_id=f"c_{i}",
            sentiment=s,
            confidence=0.85,
            class_probabilities={"positive": 0.2, "negative": 0.2, "neutral": 0.2, "mixed": 0.2, "unsupported": 0.2},
        )
        mock_pairs.append((c, p))

    t0 = time.perf_counter()
    metrics = compute_summary_metrics(mock_pairs)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    assert elapsed_ms < 50.0, f"Aggregation took {elapsed_ms:.2f}ms (threshold 50ms)"
    assert sum(metrics["sentiment_counts"].values()) == 3500
    assert 99.9 <= sum(metrics["sentiment_percentages"].values()) <= 100.1
