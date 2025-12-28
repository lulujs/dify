"""Processing context for response enhancement."""

from dataclasses import dataclass
from typing import Any, Optional

from flask import Request

from models.model import App, EndUser


@dataclass
class ProcessingContext:
    """Context information provided to post-processors.

    This dataclass contains all the contextual information that post-processors
    need to make decisions about how to enhance responses.

    Attributes:
        request: The Flask request object
        app_model: The application model being accessed
        end_user: The end user making the request (optional)
        endpoint_name: Name of the API endpoint being called
        method: HTTP method (GET, POST, etc.)
        original_response: The original response before enhancement
        start_time: Timestamp when request processing started
        response_type: Type of response (json, dict, streaming, binary, text, etc.)
    """

    request: Request
    app_model: Optional[App]
    end_user: Optional[EndUser]
    endpoint_name: str
    method: str
    original_response: Any
    start_time: float
    response_type: Optional[str] = None
