"""Metadata processor for adding common fields to responses."""

import json
import time
import uuid
from typing import Any, override

from flask import Response
from werkzeug.wrappers import Response as WerkzeugResponse

from ..context import ProcessingContext
from ..processor import PostProcessor


class MetadataProcessor(PostProcessor):
    """Post-processor that adds common metadata fields to JSON responses.

    This processor adds the following fields to JSON responses:
    - timestamp: Current timestamp in ISO format
    - request_id: Unique identifier for the request
    - api_version: API version information

    The processor only operates on JSON responses (dict objects) and will
    skip other response types to avoid breaking non-JSON responses.
    """

    api_version: str

    def __init__(self, api_version: str = "1.0"):
        """Initialize the metadata processor.

        Args:
            api_version: The API version to include in responses
        """
        self.api_version = api_version

    @override
    def can_process(self, response: Any, context: ProcessingContext) -> bool:
        """Check if this processor can handle the given response.

        This processor handles:
        - Dictionary responses (JSON objects)
        - Flask Response objects with JSON content

        Args:
            response: The response to check
            context: Processing context containing request information

        Returns:
            True if response can be processed, False otherwise
        """
        # Handle dict responses
        if isinstance(response, dict):
            return True

        # Handle Flask Response objects with JSON content
        if isinstance(response, (Response, WerkzeugResponse)):
            mimetype = getattr(response, "mimetype", "")
            return mimetype == "application/json"

        return False

    @override
    def process(self, response: Any, context: ProcessingContext) -> Any:
        """Add metadata fields to the response.

        Adds timestamp, request_id, and api_version fields to the response.
        If any of these fields already exist, they will not be overwritten
        unless explicitly configured to do so.

        Args:
            response: The response dictionary or Flask Response to enhance
            context: Processing context containing request information

        Returns:
            The enhanced response with metadata fields added
        """
        if not self.can_process(response, context):
            return response

        # Handle Flask Response objects
        if isinstance(response, (Response, WerkzeugResponse)):
            return self._process_flask_response(response, context)

        # Handle dictionary responses
        if isinstance(response, dict):
            return self._process_dict_response(response, context)

        return response

    def _process_dict_response(self, response: dict, context: ProcessingContext) -> dict:
        """Process dictionary responses into enhanced format.

        Args:
            response: Original dictionary response
            context: Processing context

        Returns:
            Enhanced response with metadata fields
        """
        # Create a copy to avoid modifying the original response
        enhanced_response = response.copy()

        # Add timestamp if not already present
        if "timestamp" not in enhanced_response:
            enhanced_response["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())

        # Add request ID if not already present
        if "request_id" not in enhanced_response:
            # Try to get request ID from Flask request headers or generate one
            request_id = self._get_or_generate_request_id(context)
            enhanced_response["request_id"] = request_id

        # Add API version if not already present
        if "api_version" not in enhanced_response:
            enhanced_response["api_version"] = self.api_version

        return enhanced_response

    def _process_flask_response(self, response: Response | WerkzeugResponse, context: ProcessingContext) -> Response:
        """Process Flask Response objects into enhanced format.

        Args:
            response: Original Flask Response
            context: Processing context

        Returns:
            New Flask Response with enhanced JSON content
        """
        try:
            # Parse the JSON content from the response
            response_data = json.loads(response.get_data(as_text=True))

            # Enhance the parsed data
            enhanced_data = self._process_dict_response(response_data, context)

            # Create new response with enhanced data
            return Response(
                response=json.dumps(enhanced_data),
                status=response.status_code,
                mimetype=response.mimetype,
                headers=dict(response.headers),  # Preserve original headers
            )
        except (json.JSONDecodeError, AttributeError) as e:
            # If we can't parse the JSON, return the original response
            return response

    def _get_or_generate_request_id(self, context: ProcessingContext) -> str:
        """Get request ID from headers or generate a new one.

        First tries to get the request ID from common headers like:
        - X-Request-ID
        - X-Request-Id
        - Request-ID

        If no request ID is found in headers, generates a new UUID.

        Args:
            context: Processing context containing the Flask request

        Returns:
            Request ID string
        """
        # Common request ID header names
        request_id_headers = ["X-Request-ID", "X-Request-Id", "Request-ID", "Request-Id"]

        # Try to get request ID from headers
        for header_name in request_id_headers:
            request_id = context.request.headers.get(header_name)
            if request_id:
                return request_id

        # Generate a new UUID if no request ID found
        return str(uuid.uuid4())
