"""
Simple progress logging utility to capture internal agent actions.
"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProgressEvent:
    timestamp: str
    component: str  # e.g., LangGraph, Tavily, Gemini
    action: str     # e.g., analyze_query, web_search, generate_report
    status: str     # started|completed|error
    message: str
    meta: Dict[str, Any] = field(default_factory=dict)


class ProgressLogger:
    def __init__(self):
        self.events: List[ProgressEvent] = []

    def emit(self, component: str, action: str, status: str, message: str, meta: Optional[Dict[str, Any]] = None):
        self.events.append(
            ProgressEvent(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                component=component,
                action=action,
                status=status,
                message=message,
                meta=meta or {},
            )
        )

# Module-level current logger handle
_current_logger: Optional[ProgressLogger] = None

def set_current_logger(logger: Optional[ProgressLogger]):
    global _current_logger
    _current_logger = logger


def get_current_logger() -> Optional[ProgressLogger]:
    return _current_logger


def log_event(component: str, action: str, status: str, message: str, meta: Optional[Dict[str, Any]] = None):
    logger = get_current_logger()
    if logger:
        logger.emit(component, action, status, message, meta)
