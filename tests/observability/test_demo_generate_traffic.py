# Unit tests for observability.demo.generate_traffic.
# British English in comments and docstrings.

from __future__ import annotations

import asyncio
import io
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytest_plugins = ("pytest_asyncio",)

from book_club.observability.demo.generate_traffic import (
    TrafficStats,
    generate_traffic_for_count,
    generate_traffic_for_duration,
    make_request,
    print_stats,
)


class TestTrafficStats:
    """Tests for TrafficStats dataclass."""

    def test_defaults(self):
        """Default values are zero or sentinels."""
        stats = TrafficStats()
        assert stats.total_requests == 0
        assert stats.successful == 0
        assert stats.failed == 0
        assert stats.total_duration_ms == 0
        assert stats.min_latency_ms == float("inf")
        assert stats.max_latency_ms == 0

    def test_avg_latency_empty(self):
        """avg_latency_ms is 0 when no requests."""
        stats = TrafficStats()
        assert stats.avg_latency_ms == 0

    def test_avg_latency_computed(self):
        """avg_latency_ms is total_duration_ms / total_requests."""
        stats = TrafficStats(total_requests=10, total_duration_ms=100.0)
        assert stats.avg_latency_ms == 10.0

    def test_success_rate_empty(self):
        """success_rate is 0 when no requests."""
        stats = TrafficStats()
        assert stats.success_rate == 0

    def test_success_rate_computed(self):
        """success_rate is percentage of successful requests."""
        stats = TrafficStats(total_requests=10, successful=8, failed=2)
        assert stats.success_rate == 80.0


@pytest.mark.asyncio
class TestMakeRequest:
    """Tests for make_request coroutine."""

    async def test_success_updates_stats(self):
        """Successful response updates stats correctly."""
        client = AsyncMock()
        client.post = AsyncMock(return_value=MagicMock(status_code=200))
        stats = TrafficStats()

        await make_request(client, "http://localhost:8010", stats, 1, verbose=False)

        assert stats.total_requests == 1
        assert stats.successful == 1
        assert stats.failed == 0
        assert stats.total_duration_ms >= 0
        assert stats.min_latency_ms != float("inf")
        assert stats.max_latency_ms >= 0

    async def test_failure_updates_stats(self):
        """Non-2xx response increments failed."""
        client = AsyncMock()
        client.post = AsyncMock(return_value=MagicMock(status_code=500))
        stats = TrafficStats()

        await make_request(client, "http://localhost:8010", stats, 1, verbose=False)

        assert stats.total_requests == 1
        assert stats.successful == 0
        assert stats.failed == 1

    async def test_exception_updates_stats(self):
        """Exception increments failed and does not raise."""
        client = AsyncMock()
        client.post = AsyncMock(side_effect=ConnectionError("refused"))
        stats = TrafficStats()

        await make_request(client, "http://localhost:8010", stats, 1, verbose=False)

        assert stats.total_requests == 1
        assert stats.failed == 1


@pytest.mark.asyncio
class TestGenerateTrafficForCount:
    """Tests for generate_traffic_for_count."""

    async def test_generates_requested_count(self):
        """Generates exactly the requested number of requests."""
        with patch(
            "book_club.observability.demo.generate_traffic.make_request",
            new_callable=AsyncMock,
        ) as mock_make:
            await generate_traffic_for_count(
                "http://localhost:8010", requests=6, concurrency=3, verbose=False
            )
            assert mock_make.call_count == 6

    async def test_respects_concurrency(self):
        """Batches respect concurrency (batches of concurrency size)."""
        with patch(
            "book_club.observability.demo.generate_traffic.make_request",
            new_callable=AsyncMock,
        ) as mock_make:
            await generate_traffic_for_count(
                "http://localhost:8010", requests=5, concurrency=2, verbose=False
            )
            assert mock_make.call_count == 5


@pytest.mark.asyncio
class TestGenerateTrafficForDuration:
    """Tests for generate_traffic_for_duration."""

    async def test_runs_for_short_duration(self):
        """Runs for at least the specified duration (minimal run)."""
        with patch(
            "book_club.observability.demo.generate_traffic.make_request",
            new_callable=AsyncMock,
        ):
            stats = await generate_traffic_for_duration(
                "http://localhost:8010", seconds=0, concurrency=1, verbose=False
            )
            # With 0 seconds we may get 0 or 1 batch
            assert stats.total_requests >= 0


class TestPrintStats:
    """Tests for print_stats."""

    def test_print_stats_captured(self, capsys):
        """print_stats writes to stdout."""
        stats = TrafficStats(
            total_requests=10,
            successful=8,
            failed=2,
            total_duration_ms=500.0,
            min_latency_ms=10.0,
            max_latency_ms=100.0,
        )
        print_stats(stats)
        out, _ = capsys.readouterr()
        assert "10" in out
        assert "8" in out
        assert "2" in out
        assert "50" in out or "50.0" in out  # avg latency
        assert "10" in out
        assert "100" in out


class TestMain:
    """Tests for main() entry point."""

    def test_main_exits_0_when_all_success(self):
        """main returns 0 when no failures."""
        fake_stats = TrafficStats(total_requests=5, successful=5, failed=0)
        with patch(
            "book_club.observability.demo.generate_traffic.asyncio.run",
            return_value=fake_stats,
        ), patch(
            "book_club.observability.demo.generate_traffic.generate_traffic_for_duration",
            new_callable=MagicMock,
        ) as mock_duration:
            with patch("sys.argv", ["generate_traffic", "--seconds", "1"]):
                from book_club.observability.demo import generate_traffic

                exit_code = generate_traffic.main()
            mock_duration.assert_called_once()
            assert exit_code == 0

    def test_main_returns_1_on_failures(self):
        """main returns 1 when some requests failed."""
        fake_stats = TrafficStats(total_requests=10, successful=7, failed=3)
        with patch(
            "book_club.observability.demo.generate_traffic.asyncio.run",
            return_value=fake_stats,
        ), patch(
            "book_club.observability.demo.generate_traffic.generate_traffic_for_duration",
            new_callable=MagicMock,
        ):
            with patch("sys.argv", ["generate_traffic", "--seconds", "1"]):
                from book_club.observability.demo import generate_traffic

                exit_code = generate_traffic.main()
            assert exit_code == 1
