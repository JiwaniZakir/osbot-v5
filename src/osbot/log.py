from __future__ import annotations

import structlog

_configured = False


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    global _configured
    if not _configured:
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer() if _is_tty() else structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        _configured = True
    return structlog.get_logger(name)


def _is_tty() -> bool:
    import sys

    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
