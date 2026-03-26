# Unit tests for observability.demo.verify_signals.
# British English in comments and docstrings.

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import httpx

from book_club.observability.demo.verify_signals import (
    VerificationResult,
    check_backend_health,
    check_grafana_health,
    check_loki_logs,
    check_prometheus_metrics,
    check_tempo_traces,
    print_result,
)


class TestVerificationResult:
    """Tests for VerificationResult dataclass."""

    def test_result_has_required_fields(self):
        """VerificationResult has name, passed, message, optional details."""
        r = VerificationResult(name="test", passed=True, message="ok", details=None)
        assert r.name == "test"
        assert r.passed is True
        assert r.message == "ok"
        assert r.details is None


class TestCheckBackendHealth:
    """Tests for check_backend_health."""

    def test_passes_when_200(self):
        """Returns passed when backend returns 200."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            result = check_backend_health("http://localhost:8010")
        assert result.passed is True
        assert "healthy" in result.message.lower()

    def test_fails_when_non_200(self):
        """Returns failed when backend returns non-200."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=503)
            result = check_backend_health("http://localhost:8010")
        assert result.passed is False
        assert "503" in result.message

    def test_fails_on_connect_error(self):
        """Returns failed on connection error."""
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = check_backend_health("http://localhost:8010")
        assert result.passed is False
        assert "connect" in result.message.lower() or "Cannot" in result.message


class TestCheckGrafanaHealth:
    """Tests for check_grafana_health."""

    def test_passes_when_200(self):
        """Returns passed when Grafana /api/health returns 200."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=200)
            result = check_grafana_health("http://localhost:3000")
        assert result.passed is True

    def test_fails_on_connect_error(self):
        """Returns failed on connection error."""
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = check_grafana_health("http://localhost:3000")
        assert result.passed is False


class TestCheckTempoTraces:
    """Tests for check_tempo_traces."""

    def test_passes_when_traces_found(self):
        """Returns passed when Tempo returns traces."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "traces": [{"traceID": "abc123def456"}],
                }),
            )
            result = check_tempo_traces(
                "http://localhost:3200", "bookclub-preprocessing-server"
            )
        assert result.passed is True
        assert "trace" in result.message.lower()

    def test_passes_when_reachable_but_no_traces(self):
        """Returns passed when Tempo is reachable but has no traces (lenient for demo-verify)."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"traces": []}),
            )
            result = check_tempo_traces(
                "http://localhost:3200", "bookclub-preprocessing-server"
            )
        assert result.passed is True
        assert "no trace" in result.message.lower() or "reachable" in result.message.lower()

    def test_fails_on_non_200(self):
        """Returns failed when Tempo returns non-200."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=500, text="error")
            result = check_tempo_traces(
                "http://localhost:3200", "bookclub-preprocessing-server"
            )
        assert result.passed is False
        assert "500" in result.message


class TestCheckLokiLogs:
    """Tests for check_loki_logs."""

    def test_passes_when_logs_with_trace_id_found(self):
        """Returns passed when Loki returns logs matching query."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "data": {"result": [{"values": [["1", "log line with trace_id"]]}]},
                }),
            )
            result = check_loki_logs(
                "http://localhost:3100", "bookclub-preprocessing-server"
            )
        assert result.passed is True

    def test_passes_when_reachable_but_no_results(self):
        """Returns passed when Loki is reachable but has no matching logs (lenient for demo-verify)."""
        with patch(
            "book_club.observability.demo.verify_signals._query_loki_logs",
            return_value=(200, {"data": {"result": []}}),
        ):
            result = check_loki_logs(
                "http://localhost:3100", "bookclub-preprocessing-server"
            )
        assert result.passed is True
        assert "no log" in result.message.lower() or "reachable" in result.message.lower()

    def test_fails_on_connect_error(self):
        """Returns failed on connection error."""
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            result = check_loki_logs(
                "http://localhost:3100", "bookclub-preprocessing-server"
            )
        assert result.passed is False


class TestCheckPrometheusMetrics:
    """Tests for check_prometheus_metrics."""

    def test_passes_when_metric_found(self):
        """Returns passed when Prometheus returns metric data."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "data": {"result": [{"value": [0, "42"]}]},
                }),
            )
            result = check_prometheus_metrics(
                "http://localhost:9090", "preprocessing_server_pdf_upload_requests_total"
            )
        assert result.passed is True
        assert "present" in result.message.lower()

    def test_fails_when_no_results(self):
        """Returns failed when metric has no series."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"data": {"result": []}}),
            )
            result = check_prometheus_metrics(
                "http://localhost:9090", "nonexistent_metric"
            )
        assert result.passed is False
        assert "not found" in result.message.lower()

    def test_fails_on_non_200(self):
        """Returns failed when Prometheus returns non-200."""
        with patch("httpx.get") as mock_get:
            mock_get.return_value = MagicMock(status_code=500)
            result = check_prometheus_metrics(
                "http://localhost:9090", "some_metric"
            )
        assert result.passed is False


class TestPrintResult:
    """Tests for print_result."""

    def test_print_result_pass(self, capsys):
        """print_result prints PASS for passed result."""
        result = VerificationResult(
            name="Backend health", passed=True, message="Backend is healthy"
        )
        print_result(result)
        out, _ = capsys.readouterr()
        assert "PASS" in out or "pass" in out.lower()
        assert "Backend health" in out

    def test_print_result_fail(self, capsys):
        """print_result prints FAIL for failed result."""
        result = VerificationResult(
            name="Tempo traces", passed=False, message="No traces found"
        )
        print_result(result)
        out, _ = capsys.readouterr()
        assert "FAIL" in out or "fail" in out.lower()
        assert "No traces" in out


class TestMain:
    """Tests for main() entry point."""

    def test_main_exits_0_when_all_pass(self):
        """main returns 0 when all checks pass."""
        with patch(
            "book_club.observability.demo.verify_signals.check_backend_health",
            return_value=VerificationResult("Backend", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_grafana_health",
            return_value=VerificationResult("Grafana", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_tempo_traces",
            return_value=VerificationResult("Tempo", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_loki_logs",
            return_value=VerificationResult("Loki", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_prometheus_metrics",
            return_value=VerificationResult("Prometheus", True, "ok"),
        ):
            with patch("sys.argv", ["verify_signals"]):
                from book_club.observability.demo import verify_signals

                exit_code = verify_signals.main()
        assert exit_code == 0

    def test_main_exits_1_when_any_fail(self):
        """main returns 1 when any check fails."""
        with patch(
            "book_club.observability.demo.verify_signals.check_backend_health",
            return_value=VerificationResult("Backend", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_grafana_health",
            return_value=VerificationResult("Grafana", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_tempo_traces",
            return_value=VerificationResult("Tempo", False, "No traces"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_loki_logs",
            return_value=VerificationResult("Loki", True, "ok"),
        ), patch(
            "book_club.observability.demo.verify_signals.check_prometheus_metrics",
            return_value=VerificationResult("Prometheus", True, "ok"),
        ):
            with patch("sys.argv", ["verify_signals"]):
                from book_club.observability.demo import verify_signals

                exit_code = verify_signals.main()
        assert exit_code == 1
