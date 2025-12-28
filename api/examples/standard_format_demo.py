#!/usr/bin/env python3
# ruff: noqa: T201
"""
Demo script showing StandardFormatProcessor functionality.

This script demonstrates how the StandardFormatProcessor transforms responses
into the standardized format for both blocking and streaming responses.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

# Add the api directory to Python path
api_dir = Path(__file__).parent.parent
sys.path.insert(0, str(api_dir))

from flask import Flask, Response

from core.response_enhancement.context import ProcessingContext
from core.response_enhancement.processors.standard_format import StandardFormatProcessor
from models.model import App, EndUser


def create_mock_context(original_response=None):
    """Create a mock processing context."""
    mock_request = Mock()
    mock_app = Mock(spec=App)
    mock_user = Mock(spec=EndUser)

    return ProcessingContext(
        request=mock_request,
        app_model=mock_app,
        end_user=mock_user,
        endpoint_name="/completion-messages",
        method="POST",
        original_response=original_response or {},
        start_time=1234567890.0,
        response_type="dict",
    )


def demo_dict_response():
    """Demonstrate processing of dictionary responses."""
    print("=== Dictionary Response Demo ===")

    processor = StandardFormatProcessor()

    # Original response from API
    original_response = {"message": "Hello, world!", "data": {"key": "value"}, "status": "success"}

    print(f"Original response: {json.dumps(original_response, indent=2)}")

    # Process with standard format
    context = create_mock_context(original_response)
    result = processor.process(original_response, context)

    print(f"Standardized response: {json.dumps(result, indent=2)}")
    print()


def demo_flask_response_success():
    """Demonstrate processing of Flask Response with success status."""
    print("=== Flask Response (Success) Demo ===")

    with Flask(__name__).app_context():
        processor = StandardFormatProcessor()

        # Original Flask response with 200 status
        original_data = {"message": "Operation successful", "result": "data"}
        original_response = Response(response=json.dumps(original_data), status=200, mimetype="application/json")

        print(f"Original Flask response status: {original_response.status_code}")
        print(f"Original Flask response data: {original_data}")

        # Process with standard format
        context = create_mock_context(original_response)
        result = processor.process(original_response, context)

        print(f"Standardized response status: {result.status_code}")
        response_data = json.loads(result.get_data(as_text=True))
        print(f"Standardized response data: {json.dumps(response_data, indent=2)}")
        print()


def demo_flask_response_error():
    """Demonstrate processing of Flask Response with error status."""
    print("=== Flask Response (Error) Demo ===")

    with Flask(__name__).app_context():
        processor = StandardFormatProcessor()

        # Original Flask response with 500 status
        original_data = {"error": "Internal server error", "code": "E001"}
        original_response = Response(response=json.dumps(original_data), status=500, mimetype="application/json")

        print(f"Original Flask response status: {original_response.status_code}")
        print(f"Original Flask response data: {original_data}")

        # Process with standard format
        context = create_mock_context(original_response)
        result = processor.process(original_response, context)

        print(f"Standardized response status: {result.status_code}")
        response_data = json.loads(result.get_data(as_text=True))
        print(f"Standardized response data: {json.dumps(response_data, indent=2)}")
        print()


def demo_streaming_response():
    """Demonstrate processing of streaming responses."""
    print("=== Streaming Response Demo ===")

    processor = StandardFormatProcessor()

    # Mock streaming generator
    def mock_stream():
        yield "data: chunk1\n\n"
        yield "data: chunk2\n\n"
        yield "data: chunk3\n\n"

    original_response = mock_stream()

    print("Original streaming response chunks:")
    print("- data: chunk1")
    print("- data: chunk2")
    print("- data: chunk3")

    # Process with standard format
    context = create_mock_context(original_response)
    result = processor.process(original_response, context)

    print("\nStandardized streaming response:")
    chunks = list(result)
    for i, chunk in enumerate(chunks):
        if chunk.startswith("data: "):
            chunk_data = json.loads(chunk.replace("data: ", "").strip())
            print(f"Chunk {i + 1}: {json.dumps(chunk_data, indent=2)}")
        else:
            print(f"Chunk {i + 1}: {chunk}")
    print()


def main():
    """Run all demos."""
    print("StandardFormatProcessor Demo")
    print("=" * 50)
    print()

    demo_dict_response()
    demo_flask_response_success()
    demo_flask_response_error()
    demo_streaming_response()

    print("Demo completed!")


if __name__ == "__main__":
    main()
