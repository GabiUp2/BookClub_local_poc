# Gunicorn config for BookClub preprocessing server.
# Ensures OpenTelemetry is initialised in each worker after fork (fork-safe tracing).

import os


def post_fork(server, worker):
    """Re-initialise OTEL in each worker after fork so traces are exported correctly.

    BatchSpanProcessor is not fork-safe: child workers inherit broken state from the
    parent. Initialising here gives each worker its own TracerProvider and exporter.
    """
    os.environ["OTEL_INIT_IN_POST_FORK"] = "1"
    from server_main import _init_otel  # noqa: PLC0415

    _init_otel()
