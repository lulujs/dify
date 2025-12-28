"""Standard format processor for adding standardized response structure."""

import json
from collections.abc import Generator
from typing import Any, override

from flask import Response
from werkzeug.wrappers import Response as WerkzeugResponse

from ..context import ProcessingContext
from ..processor import PostProcessor


class StandardFormatProcessor(PostProcessor):
    """Post-processor that adds standardized response format.

    This processor transforms responses into a standardized format:

    For blocking responses (dict/JSON):
    {
        "returnCode": "SUC0000",  # SUC0000 for HTTP 200, FAIL000 for others
        "errorMsg": null,
        "body": {}  # Empty object as specified
    }

    For streaming responses:
    - Data chunks: {"returnCode": "SUC0000", "errorMsg": null, "data": {}, "type": "DATA"}
    - Final chunk: {"returnCode": "SUC0000", "errorMsg": null, "data": null, "type": "DONE"}
    """

    @override
    def can_process(self, response: Any, context: ProcessingContext) -> bool:
        """Check if this processor can handle the given response.

        This processor handles:
        - Dictionary responses (JSON objects)
        - Flask Response objects with JSON content
        - Streaming responses (generators)

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
            return mimetype in ("application/json", "text/event-stream")

        # Handle streaming responses (generators)
        if isinstance(response, Generator):
            return True

        return False

    @override
    def process(self, response: Any, context: ProcessingContext) -> Any:
        """Transform response into standardized format.

        Args:
            response: The response to transform
            context: Processing context containing request information

        Returns:
            The transformed response with standardized format
        """
        if not self.can_process(response, context):
            return response

        # Determine HTTP status code
        status_code = self._get_status_code(response, context)
        return_code = "SUC0000" if status_code == 200 else "FAIL000"

        # Handle different response types
        if isinstance(response, dict):
            return self._process_dict_response(response, return_code)

        elif isinstance(response, (Response, WerkzeugResponse)):
            return self._process_flask_response(response, return_code, status_code)

        elif isinstance(response, Generator):
            return self._process_streaming_response(response, return_code, context)

        return response

    def _get_status_code(self, response: Any, context: ProcessingContext) -> int:
        """Extract HTTP status code from response or context.

        Args:
            response: The response object
            context: Processing context

        Returns:
            HTTP status code (defaults to 200)
        """
        # For Flask Response objects, get status code directly
        if isinstance(response, (Response, WerkzeugResponse)):
            return response.status_code

        # For other responses, assume 200 (success) unless we can determine otherwise
        # In a real implementation, you might want to check Flask's g object or other context
        return 200

    def _process_dict_response(self, response: dict, return_code: str) -> dict:
        """Process dictionary responses into standardized format.

        Args:
            response: Original dictionary response
            return_code: Return code based on HTTP status

        Returns:
            Standardized response format
        """
        return {
            "returnCode": return_code,
            "errorMsg": None,
            "body": response,  # Include original data in body
        }

    def _process_flask_response(
        self, response: Response | WerkzeugResponse, return_code: str, status_code: int
    ) -> Response:
        """Process Flask Response objects into standardized format.

        Args:
            response: Original Flask Response
            return_code: Return code based on HTTP status
            status_code: HTTP status code

        Returns:
            New Flask Response with standardized format
        """
        try:
            # Parse the JSON content from the response to preserve original data
            original_data = json.loads(response.get_data(as_text=True))

            # Create standardized format while preserving original data in body
            standardized_data = {
                "returnCode": return_code,
                "errorMsg": None,
                "body": original_data,  # Include original data in body
            }
        except (json.JSONDecodeError, AttributeError):
            # If we can't parse the JSON, use empty body
            standardized_data = {
                "returnCode": return_code,
                "errorMsg": None,
                "body": {},  # Empty object as fallback
            }

        return Response(
            response=json.dumps(standardized_data),
            status=status_code,
            mimetype="application/json",
            headers=dict(response.headers),  # Preserve original headers
        )

    def _process_streaming_response(
        self, response: Generator, return_code: str, context: ProcessingContext
    ) -> Generator:
        """Process streaming responses into standardized format.

        Args:
            response: Original generator response
            return_code: Return code based on HTTP status
            context: Processing context

        Returns:
            Generator yielding standardized streaming format
        """

        def standardized_stream():
            """Generator that yields standardized streaming format."""
            try:
                # Process each chunk from the original stream
                for chunk in response:
                    # Data chunk with standardized format
                    data_chunk = {
                        "returnCode": return_code,
                        "errorMsg": None,
                        "data": chunk
                        if not isinstance(chunk, str) or not chunk.startswith("data: ")
                        else {},  # Include chunk data
                        "type": "DATA",
                    }

                    # Yield as SSE format if needed
                    if isinstance(chunk, str) and chunk.startswith("data: "):
                        yield f"data: {json.dumps(data_chunk)}\n\n"
                    else:
                        yield json.dumps(data_chunk)

                # Send final DONE chunk
                done_chunk = {
                    "returnCode": return_code,
                    "errorMsg": None,
                    "data": None,  # null for DONE type as specified
                    "type": "DONE",
                }

                # Yield final chunk in appropriate format
                yield f"data: {json.dumps(done_chunk)}\n\n"

            except Exception as e:
                # Send error chunk if something goes wrong
                error_chunk = {"returnCode": "FAIL000", "errorMsg": str(e), "data": None, "type": "DONE"}
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return standardized_stream()
