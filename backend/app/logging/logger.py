import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs records in structured JSON.
    Useful for production log aggregators (Elasticsearch, Datadog, CloudWatch).
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Merge extra context dict if provided in logging call (e.g. logger.info("msg", extra={...}))
        if hasattr(record, "extra_context") and isinstance(record.extra_context, dict): # type: ignore
            log_record.update(record.extra_context)
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_record)

def get_logger(name: str = "CandidateCore") -> logging.Logger:
    """
    Returns a configured structured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Prevent handler duplication
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False
        
    return logger

# Shared singleton logger
logger = get_logger("CandidateCore")
