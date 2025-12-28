"""Base post-processor interface for response enhancement."""

from abc import ABC, abstractmethod
from typing import Any

from .context import ProcessingContext


class PostProcessor(ABC):
    """Abstract base class for all response post-processors.

    Post-processors are responsible for enhancing API responses by adding
    additional fields, metadata, or transforming the response structure.
    Each processor should implement the process() and can_process() methods.
    """

    @abstractmethod
    def process(self, response: Any, context: ProcessingContext) -> Any:
        """Process the response and return enhanced version.

        This method receives the current response (which may have been processed
        by previous processors in the pipeline) and the processing context,
        and returns an enhanced version of the response.

        Args:
            response: The response to be processed (may be modified by previous processors)
            context: Processing context containing request information

        Returns:
            The enhanced response

        Raises:
            Exception: Any processing errors should be allowed to bubble up
                      for handling by the error recovery mechanism
        """
        pass

    @abstractmethod
    def can_process(self, response: Any, context: ProcessingContext) -> bool:
        """Check if this processor can handle the given response.

        This method allows processors to determine whether they should
        process a particular response based on its type, content, or context.

        Args:
            response: The response to check
            context: Processing context containing request information

        Returns:
            True if this processor can handle the response, False otherwise
        """
        pass
