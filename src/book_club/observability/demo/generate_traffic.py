#!/usr/bin/env python3
"""Generate traffic for OTEL tracing demos.

This script sends requests to the backend to generate traces, logs, and metrics.
Used by the demo-*-trace-signal Make targets.

Usage:
    python -m src.book_club.observability.demo.generate_traffic --seconds 20 --concurrency 5
    python -m src.book_club.observability.demo.generate_traffic --requests 50 --concurrency 10
"""

import argparse
import asyncio
import io
import sys
import time
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class TrafficStats:
    """Statistics from a traffic generation run."""

    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    total_duration_ms: float = 0
    min_latency_ms: float = float("inf")
    max_latency_ms: float = 0
    first_error: Optional[str] = None  # First failure reason for diagnostics

    @property
    def avg_latency_ms(self) -> float:
        """Average latency in milliseconds."""
        if self.total_requests == 0:
            return 0
        return self.total_duration_ms / self.total_requests

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        if self.total_requests == 0:
            return 0
        return (self.successful / self.total_requests) * 100


# Minimal valid PDF content
MINIMAL_PDF = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj
xref
0 4
0000000000 65535 f
0000000009 00000 n
0000000052 00000 n
0000000101 00000 n
trailer<</Size 4/Root 1 0 R>>
startxref
170
%%EOF
"""


async def make_request(
    client: httpx.AsyncClient,
    backend_url: str,
    stats: TrafficStats,
    request_id: int,
    verbose: bool = False,
) -> None:
    """Make a single request to the backend and update stats."""
    start = time.perf_counter()

    try:
        # Create a file-like object for the PDF
        files = {"file": ("demo.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")}

        response = await client.post(
            f"{backend_url}/upload-pdf",
            files=files,
            timeout=30.0,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000
        stats.total_requests += 1
        stats.total_duration_ms += elapsed_ms
        stats.min_latency_ms = min(stats.min_latency_ms, elapsed_ms)
        stats.max_latency_ms = max(stats.max_latency_ms, elapsed_ms)

        if response.status_code == 200:
            stats.successful += 1
            if verbose:
                print(f"  [{request_id}] OK ({elapsed_ms:.0f}ms)")
            else:
                print(".", end="", flush=True)
        else:
            stats.failed += 1
            if stats.first_error is None:
                body = (response.text or "")[:150].replace("\n", " ")
                stats.first_error = f"HTTP {response.status_code}: {body}"
            if verbose:
                print(
                    f"  [{request_id}] FAIL {response.status_code} ({elapsed_ms:.0f}ms)"
                )
            else:
                print("x", end="", flush=True)

    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        stats.total_requests += 1
        stats.total_duration_ms += elapsed_ms
        stats.failed += 1
        if stats.first_error is None:
            stats.first_error = f"{type(e).__name__}: {e}"
        if verbose:
            print(f"  [{request_id}] ERROR: {e} ({elapsed_ms:.0f}ms)")
        else:
            print("E", end="", flush=True)


async def generate_traffic_for_duration(
    backend_url: str,
    seconds: int,
    concurrency: int,
    verbose: bool = False,
) -> TrafficStats:
    """Generate traffic for a specified duration."""
    stats = TrafficStats()
    request_id = 0
    end_time = time.time() + seconds

    async with httpx.AsyncClient() as client:
        while time.time() < end_time:
            # Fire off concurrent requests
            tasks = []
            for _ in range(concurrency):
                request_id += 1
                tasks.append(
                    make_request(client, backend_url, stats, request_id, verbose)
                )

            await asyncio.gather(*tasks)

            # Small delay between batches
            await asyncio.sleep(0.1)

    return stats


async def generate_traffic_for_count(
    backend_url: str,
    requests: int,
    concurrency: int,
    verbose: bool = False,
) -> TrafficStats:
    """Generate a specific number of requests."""
    stats = TrafficStats()

    async with httpx.AsyncClient() as client:
        # Process in batches
        for batch_start in range(0, requests, concurrency):
            batch_end = min(batch_start + concurrency, requests)
            tasks = []

            for request_id in range(batch_start + 1, batch_end + 1):
                tasks.append(
                    make_request(client, backend_url, stats, request_id, verbose)
                )

            await asyncio.gather(*tasks)

    return stats


def print_stats(stats: TrafficStats) -> None:
    """Print traffic generation statistics."""
    print("\n")
    print("Traffic generation complete:")
    print(f"  Total requests: {stats.total_requests}")
    print(f"  Successful:     {stats.successful} ({stats.success_rate:.1f}%)")
    print(f"  Failed:         {stats.failed}")
    if stats.total_requests > 0:
        print(f"  Avg latency:    {stats.avg_latency_ms:.0f}ms")
        if stats.min_latency_ms != float("inf"):
            print(f"  Min latency:    {stats.min_latency_ms:.0f}ms")
            print(f"  Max latency:    {stats.max_latency_ms:.0f}ms")
    if stats.failed > 0 and stats.first_error:
        print()
        print(f"  First failure:  {stats.first_error}")
        print(
            "  Ensure backend is running: docker compose up -d bookclub-preprocessing-server"
        )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate traffic for OTEL tracing demos"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8010",
        help="Backend URL (default: http://localhost:8010)",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=None,
        help="Generate traffic for this many seconds",
    )
    parser.add_argument(
        "--requests",
        type=int,
        default=None,
        help="Generate this many requests",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent requests (default: 5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output (show each request)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.seconds is None and args.requests is None:
        args.seconds = 20  # Default to 20 seconds

    if args.seconds is not None and args.requests is not None:
        print("Error: Specify either --seconds or --requests, not both")
        return 1

    print(f"Generating traffic to {args.backend_url}")
    if args.seconds:
        print(f"Duration: {args.seconds} seconds, concurrency: {args.concurrency}")
    else:
        print(f"Requests: {args.requests}, concurrency: {args.concurrency}")
    print()

    # Run traffic generation
    if args.seconds:
        stats = asyncio.run(
            generate_traffic_for_duration(
                args.backend_url, args.seconds, args.concurrency, args.verbose
            )
        )
    else:
        stats = asyncio.run(
            generate_traffic_for_count(
                args.backend_url, args.requests, args.concurrency, args.verbose
            )
        )

    print_stats(stats)

    return 0 if stats.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
