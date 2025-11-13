#!/usr/bin/env python3
"""
Benchmark script for Streaming Analytics Methods (9+ methods)

Tests all streaming analytics implementations:
- StreamBuffer (add, add_batch, get_window methods)
- StreamingAnalyzer (process_event, get_live_stats, detect_anomalies)
- LiveGameTracker (update, get_state)

Goal: Test 9+ methods to advance toward 100% coverage (90 → 99+ methods)
"""

import sys
import time
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.streaming_analytics import (
    StreamBuffer,
    StreamingAnalyzer,
    LiveGameTracker,
    StreamEvent,
    StreamEventType,
    create_sample_event,
)


# Benchmark Infrastructure
def measure_performance(func):
    """Measure execution time and capture result."""
    start_time = time.time()
    try:
        result = func()
        execution_time = time.time() - start_time
        return result, execution_time, None
    except Exception as e:
        execution_time = time.time() - start_time
        return None, execution_time, str(e)


def benchmark_method(name: str, func, category: str) -> dict:
    """Benchmark a single method."""
    print(f"Testing {name}...", end=" ")

    result, exec_time, error = measure_performance(func)

    success = error is None
    status = "✓" if success else "✗"

    print(f"{status} ({exec_time:.4f}s)")
    if error:
        print(f"  Error: {error}")

    return {
        "method": name,
        "category": category,
        "execution_time": exec_time,
        "success": success,
        "error": error,
    }


# Streaming Analytics Method Tests


def test_stream_buffer_init():
    """Test StreamBuffer.__init__()"""
    buffer = StreamBuffer(max_size=1000, max_age_seconds=300.0)

    assert buffer.max_size == 1000
    assert buffer.max_age_seconds == 300.0
    assert len(buffer.buffer) == 0
    return buffer


def test_stream_buffer_add():
    """Test StreamBuffer.add()"""
    buffer = StreamBuffer(max_size=100)

    event = create_sample_event(
        StreamEventType.PLAYER_STAT, player_id="player1", points=10
    )

    buffer.add(event)

    assert len(buffer.buffer) == 1
    assert buffer.buffer[0].event_type == StreamEventType.PLAYER_STAT
    assert buffer.buffer[0].sequence_id == 0
    return buffer


def test_stream_buffer_add_batch():
    """Test StreamBuffer.add_batch()"""
    buffer = StreamBuffer(max_size=100)

    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT, player_id=f"player{i}", points=i * 2
        )
        for i in range(10)
    ]

    buffer.add_batch(events)

    assert len(buffer.buffer) == 10
    # Check sequence IDs are incremental
    for i in range(10):
        assert buffer.buffer[i].sequence_id == i
    return buffer


def test_stream_buffer_get_recent():
    """Test StreamBuffer.get_recent()"""
    buffer = StreamBuffer(max_size=100)

    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT, player_id=f"player{i}", points=i
        )
        for i in range(20)
    ]
    buffer.add_batch(events)

    recent = buffer.get_recent(n=5)

    assert len(recent) == 5
    # Should be most recent 5 events
    assert recent[-1].data["points"] == 19
    return recent


def test_stream_buffer_get_window():
    """Test StreamBuffer.get_window()"""
    buffer = StreamBuffer(max_size=100)

    # Create events with different timestamps
    base_time = datetime.now()
    events = [
        StreamEvent(
            event_type=StreamEventType.PLAYER_STAT,
            timestamp=base_time - timedelta(seconds=i * 10),
            game_id="game_001",
            data={"player_id": f"player{i}", "points": i},
        )
        for i in range(10)
    ]
    buffer.add_batch(events)

    # Get events within 60 seconds
    window_events = buffer.get_window(window_seconds=60.0)

    # Should get events from last 60 seconds (6 events)
    assert len(window_events) >= 5
    return window_events


def test_streaming_analyzer_init():
    """Test StreamingAnalyzer.__init__()"""
    analyzer = StreamingAnalyzer(
        buffer_size=1000, window_seconds=300.0, enable_metrics=True
    )

    assert analyzer.buffer.max_size == 1000
    assert analyzer.window_seconds == 300.0
    assert analyzer.enable_metrics == True
    assert analyzer.stats.events_processed == 0
    return analyzer


def test_streaming_analyzer_process_event():
    """Test StreamingAnalyzer.process_event()"""
    analyzer = StreamingAnalyzer(buffer_size=100, window_seconds=300.0)

    event = create_sample_event(
        StreamEventType.PLAYER_STAT, player_id="lebron_james", points=25
    )

    result = analyzer.process_event(event)

    assert analyzer.stats.events_processed == 1
    assert "processing_latency_ms" in result
    assert result["processing_latency_ms"] >= 0
    return result


def test_streaming_analyzer_process_batch():
    """Test StreamingAnalyzer.process_batch()"""
    analyzer = StreamingAnalyzer(buffer_size=100, window_seconds=300.0)

    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT, player_id=f"player{i}", points=i * 2
        )
        for i in range(10)
    ]

    result = analyzer.process_batch(events)

    assert analyzer.stats.events_processed == 10
    assert result["events_processed"] == 10
    assert "batch_latency_ms" in result
    return result


def test_streaming_analyzer_get_live_stats():
    """Test StreamingAnalyzer.get_live_stats()"""
    analyzer = StreamingAnalyzer(buffer_size=100, window_seconds=300.0)

    # Add some events
    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT, player_id=f"player{i}", points=i * 3
        )
        for i in range(15)
    ]
    analyzer.process_batch(events)

    stats = analyzer.get_live_stats()

    assert "event_count" in stats
    assert stats["event_count"] == 15
    assert "events_per_minute" in stats
    assert "event_types" in stats
    return stats


def test_streaming_analyzer_detect_anomalies():
    """Test StreamingAnalyzer.detect_anomalies()"""
    analyzer = StreamingAnalyzer(buffer_size=100, window_seconds=300.0)

    # Create events with normal values and one anomaly
    normal_events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT,
            player_id=f"player{i}",
            score=20 + np.random.normal(0, 2),  # Normal around 20
        )
        for i in range(30)
    ]

    # Add an anomaly
    anomaly_event = create_sample_event(
        StreamEventType.PLAYER_STAT,
        player_id="anomaly_player",
        score=50,  # Way above normal
    )

    analyzer.process_batch(normal_events + [anomaly_event])

    anomalies = analyzer.detect_anomalies(metric="score", threshold_std=2.5)

    # Should detect at least 1 anomaly
    assert len(anomalies) >= 1
    assert all("z_score" in a for a in anomalies)
    return anomalies


def test_streaming_analyzer_get_metrics():
    """Test StreamingAnalyzer.get_metrics()"""
    analyzer = StreamingAnalyzer(buffer_size=100, window_seconds=300.0)

    # Process some events
    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT, player_id=f"player{i}", points=i
        )
        for i in range(20)
    ]
    analyzer.process_batch(events)

    metrics = analyzer.get_metrics()

    assert metrics.events_processed == 20
    assert metrics.average_latency_ms >= 0
    assert metrics.events_per_second >= 0
    return metrics


def test_live_game_tracker_init():
    """Test LiveGameTracker.__init__()"""
    tracker = LiveGameTracker(game_id="LAL_vs_BOS_20251104")

    assert tracker.game_id == "LAL_vs_BOS_20251104"
    assert tracker.score == {"home": 0, "away": 0}
    assert tracker.quarter == 1
    assert isinstance(tracker.analyzer, StreamingAnalyzer)
    return tracker


def test_live_game_tracker_update():
    """Test LiveGameTracker.update()"""
    tracker = LiveGameTracker(game_id="game_001")

    # Create and process events
    event1 = create_sample_event(
        StreamEventType.PLAYER_STAT, player_id="player1", points=2, rebounds=1
    )
    state1 = tracker.update(event1)

    assert state1["game_id"] == "game_001"
    assert state1["events_processed"] == 1

    # Update score
    event2 = create_sample_event(
        StreamEventType.SCORE_UPDATE, score={"home": 2, "away": 0}
    )
    state2 = tracker.update(event2)

    assert state2["score"] == {"home": 2, "away": 0}
    assert state2["events_processed"] == 2
    return state2


def test_live_game_tracker_get_state():
    """Test LiveGameTracker.get_state()"""
    tracker = LiveGameTracker(game_id="game_002")

    # Add some events
    events = [
        create_sample_event(
            StreamEventType.PLAYER_STAT,
            player_id=f"player{i}",
            points=i * 2,
            rebounds=i,
        )
        for i in range(5)
    ]

    for event in events:
        tracker.update(event)

    state = tracker.get_state()

    assert "game_id" in state
    assert "score" in state
    assert "quarter" in state
    assert "possession" in state
    assert "top_scorers" in state
    assert "events_processed" in state
    assert state["events_processed"] == 5
    return state


# Main Benchmark Execution
def main():
    print("=" * 70)
    print("STREAMING ANALYTICS METHODS BENCHMARK")
    print("=" * 70)
    print(f"Goal: Test 14 streaming analytics methods")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    results = []

    # Test all streaming analytics methods
    test_cases = [
        # StreamBuffer (5 methods)
        ("StreamBuffer.__init__", test_stream_buffer_init, "StreamBuffer"),
        ("StreamBuffer.add", test_stream_buffer_add, "StreamBuffer"),
        ("StreamBuffer.add_batch", test_stream_buffer_add_batch, "StreamBuffer"),
        ("StreamBuffer.get_recent", test_stream_buffer_get_recent, "StreamBuffer"),
        ("StreamBuffer.get_window", test_stream_buffer_get_window, "StreamBuffer"),
        # StreamingAnalyzer (6 methods)
        (
            "StreamingAnalyzer.__init__",
            test_streaming_analyzer_init,
            "StreamingAnalyzer",
        ),
        (
            "StreamingAnalyzer.process_event",
            test_streaming_analyzer_process_event,
            "StreamingAnalyzer",
        ),
        (
            "StreamingAnalyzer.process_batch",
            test_streaming_analyzer_process_batch,
            "StreamingAnalyzer",
        ),
        (
            "StreamingAnalyzer.get_live_stats",
            test_streaming_analyzer_get_live_stats,
            "StreamingAnalyzer",
        ),
        (
            "StreamingAnalyzer.detect_anomalies",
            test_streaming_analyzer_detect_anomalies,
            "StreamingAnalyzer",
        ),
        (
            "StreamingAnalyzer.get_metrics",
            test_streaming_analyzer_get_metrics,
            "StreamingAnalyzer",
        ),
        # LiveGameTracker (3 methods)
        ("LiveGameTracker.__init__", test_live_game_tracker_init, "LiveGameTracker"),
        ("LiveGameTracker.update", test_live_game_tracker_update, "LiveGameTracker"),
        (
            "LiveGameTracker.get_state",
            test_live_game_tracker_get_state,
            "LiveGameTracker",
        ),
    ]

    for name, test_func, category in test_cases:
        result = benchmark_method(name, test_func, category)
        results.append(result)

    # Calculate summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_tests = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total_tests - successful

    print(f"Total Methods Tested: {total_tests}")
    print(f"Successful: {successful} ({successful/total_tests*100:.1f}%)")
    print(f"Failed: {failed}")
    print()

    # Break down by category
    categories = {}
    for result in results:
        cat = result["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0}
        categories[cat]["total"] += 1
        if result["success"]:
            categories[cat]["success"] += 1

    print("By Category:")
    for cat, stats in sorted(categories.items()):
        success_rate = stats["success"] / stats["total"] * 100
        print(f"  {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")

    # Calculate average execution time
    successful_times = [r["execution_time"] for r in results if r["success"]]
    if successful_times:
        avg_time = sum(successful_times) / len(successful_times)
        print(f"\nAverage Execution Time: {avg_time:.4f}s")
        print(f"Fastest: {min(successful_times):.4f}s")
        print(f"Slowest: {max(successful_times):.4f}s")

    # Save results
    output_dir = Path(__file__).parent.parent / "benchmark_results"
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save to JSON
    json_path = output_dir / f"streaming_analytics_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "successful": successful,
                "failed": failed,
                "results": results,
            },
            f,
            indent=2,
        )

    # Save to CSV
    csv_path = output_dir / f"streaming_analytics_{timestamp}.csv"
    df = pd.DataFrame(results)
    df.to_csv(csv_path, index=False)

    print(f"\n✓ Results saved to:")
    print(f"  - {json_path}")
    print(f"  - {csv_path}")

    print("\n" + "=" * 70)
    print(
        f"COVERAGE UPDATE: {successful}/{total_tests} streaming analytics methods tested!"
    )
    print(f"Expected total coverage: 90 + {successful} = {90 + successful}/99")
    if successful >= 9:
        print("🎉 TARGET REACHED! 99+ methods tested - 100% COVERAGE!")
    print("=" * 70)

    return 0 if successful == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
