import json
import logging
from typing import Any, Dict


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entrypoint for Access Analyzer remediation events.

    This minimal implementation records the incoming event and returns a
    success response. Extend this function to perform automated remediation
    for findings emitted by AWS IAM Access Analyzer.
    """
    try:
        logger.info("Received event: %s", json.dumps(event, default=str))
    except Exception:
        # Fallback in case the event contains non-serializable types
        logger.info("Received event (non-serializable), keys: %s", list(event) if isinstance(event, dict) else type(event))

    return {
        "status": "ok",
        "message": "Event processed",
    }

