"""Registry for managing post-processors."""

import logging
from typing import Any, Optional

from .context import ProcessingContext
from .processor import PostProcessor

logger = logging.getLogger(__name__)


class PostProcessorRegistry:
    """Registry for managing and executing post-processors.

    This class maintains a registry of available post-processors and provides
    methods to register new processors, retrieve them by name, and execute
    processing pipelines with error handling.
    """

    def __init__(self):
        """Initialize the registry with an empty processor dictionary."""
        self._processors: dict[str, PostProcessor] = {}

    def register(self, name: str, processor: PostProcessor) -> None:
        """Register a post-processor with the given name.

        Args:
            name: Unique name for the processor
            processor: The PostProcessor instance to register

        Raises:
            ValueError: If name is empty or processor is None
            TypeError: If processor doesn't implement PostProcessor interface
        """
        if not name or not name.strip():
            raise ValueError("Processor name cannot be empty")

        if processor is None:
            raise ValueError("Processor cannot be None")

        if not isinstance(processor, PostProcessor):
            raise TypeError("Processor must implement PostProcessor interface")

        self._processors[name] = processor
        logger.debug("Registered post-processor: %s", name)

    def get(self, name: str) -> Optional[PostProcessor]:
        """Retrieve a post-processor by name.

        Args:
            name: Name of the processor to retrieve

        Returns:
            The PostProcessor instance if found, None otherwise
        """
        return self._processors.get(name)

    def execute_pipeline(self, processors: list[str], response: Any, context: ProcessingContext) -> Any:
        """Execute a pipeline of post-processors in order.

        This method executes the specified processors in sequence, where each
        processor receives the output of the previous processor. If any processor
        fails, the error is handled by the error handler and the pipeline continues
        with the next processor.

        Args:
            processors: List of processor names to execute in order
            response: The initial response to process
            context: Processing context containing request information

        Returns:
            The final processed response after all processors have run
        """
        if not processors:
            return response

        current_response = response

        # Import here to avoid circular imports
        from .decorator import get_error_handler

        error_handler = get_error_handler()

        for processor_name in processors:
            try:
                # Check if processor is disabled due to previous errors
                if error_handler.is_processor_disabled(processor_name):
                    logger.debug("Processor '%s' is disabled, skipping", processor_name)
                    continue

                processor = self.get(processor_name)
                if processor is None:
                    logger.warning("Processor '%s' not found in registry, skipping", processor_name)
                    continue

                # Check if processor can handle this response
                if not processor.can_process(current_response, context):
                    logger.debug("Processor '%s' cannot process response, skipping", processor_name)
                    continue

                # Process the response
                logger.debug("Executing processor: %s", processor_name)
                current_response = processor.process(current_response, context)

            except Exception as e:
                # Use error handler for comprehensive error handling
                current_response = error_handler.handle_processor_error(e, processor_name, context, current_response)
                # Continue with next processor - don't let one failure break the pipeline
                continue

        return current_response

    def list_processors(self) -> list[str]:
        """Get a list of all registered processor names.

        Returns:
            List of processor names currently registered
        """
        return list(self._processors.keys())

    def unregister(self, name: str) -> bool:
        """Unregister a processor by name.

        Args:
            name: Name of the processor to unregister

        Returns:
            True if processor was found and removed, False otherwise
        """
        if name in self._processors:
            del self._processors[name]
            logger.debug("Unregistered post-processor: %s", name)
            return True
        return False

    def clear(self) -> None:
        """Clear all registered processors."""
        self._processors.clear()
        logger.debug("Cleared all registered processors")
