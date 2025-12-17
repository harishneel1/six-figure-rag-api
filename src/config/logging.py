import logging
import sys
import os
from pathlib import Path
import socket
from contextvars import ContextVar
from typing import Optional
import structlog
from structlog.types import EventDict, WrappedLogger

# Datadog trace correlation
try:
    from ddtrace import tracer
    DD_TRACE_AVAILABLE = True
except ImportError:
    DD_TRACE_AVAILABLE = False

# Context variables
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

POD_NAME = os.getenv("POD_NAME", "local")
HOST_NAME = socket.gethostname()

def get_log_level() -> int:
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }.get(log_level_str, logging.INFO)


def add_context_info(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    request_id = request_id_var.get()
    if request_id:
        event_dict["request_id"] = request_id
    event_dict["pod_name"] = POD_NAME
    event_dict["host_name"] = HOST_NAME

    # Add Datadog trace correlation
    if DD_TRACE_AVAILABLE:
        from ddtrace import tracer
        span = tracer.current_span()
        if span:
            event_dict["dd.trace_id"] = str(span.trace_id)
            event_dict["dd.span_id"] = str(span.span_id)
            event_dict["dd.service"] = os.getenv("DD_SERVICE", "rag-api")
            event_dict["dd.env"] = os.getenv("DD_ENV", "development")
            event_dict["dd.version"] = os.getenv("DD_VERSION", "1.0.0")

    return event_dict


def rename_event_to_message(logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
    if "event" in event_dict:
        event_dict["message"] = event_dict.pop("event")
    return event_dict

def configure_std_out_handler(root_logger) -> logging.Handler:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(stdout_handler)

def configure_file_handler(root_logger, log_filename: str) -> logging.Handler:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / log_filename, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(file_handler)


def configure_logging(log_filename: str = "application.log") -> None:
    log_level = get_log_level() # priority 

    # 1) Setting Log Handlers: stdout + file
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Configure handlers
    configure_std_out_handler(root_logger)
    configure_file_handler(root_logger, log_filename)

    # Optional: reduce noisy libs i.e dependent packages logs are not needed
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.WARNING)

    # 2) structlog: used for OUR app logs
    # Force JSON output even in development (no console renderer)
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,  # skip below log level
            structlog.contextvars.merge_contextvars,  # pull in request_id, user_id
            structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
            structlog.processors.CallsiteParameterAdder(
                [
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                    structlog.processors.CallsiteParameter.LINENO
                ]
            ),
            structlog.stdlib.add_log_level,  # adds "level"
            structlog.stdlib.add_logger_name,  # adds "logger"
            add_context_info,  # request/user/pod/host
            rename_event_to_message,  # event -> message
            structlog.processors.StackInfoRenderer(),  # render stack traces
            structlog.processors.format_exc_info,  # exception info if exc_info=True
            structlog.processors.JSONRenderer(),  # dict -> JSON string
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,  # Use stdlib logger wrapper
        cache_logger_on_first_use=True, #singleton optimization
    )

def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

def set_request_id(request_id: str) -> None:
    request_id_var.set(request_id)

def clear_context() -> None:
    request_id_var.set(None)