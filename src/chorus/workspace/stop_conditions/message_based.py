from typing import Optional

from chorus.workspace.stop_conditions.base import MultiAgentStopCondition


class MessageBasedStopper(MultiAgentStopCondition):
    """Stop condition based on detecting a specific message pattern.

    This stopper will check for messages matching the specified source agent,
    destination agent, and channel criteria.
    """

    def __init__(
        self,
        source: Optional[str] = None,
        destination: Optional[str] = None,
        channel: Optional[str] = None,
    ):
        """Initialize the message-based stopper.

        Args:
            source (Optional[str]): Source agent ID to match. If None, matches any source.
            destination (Optional[str]): Destination agent ID to match. If None, matches any destination.
            channel (Optional[str]): Channel name to match. If None, matches any channel.
        """
        super().__init__()
        self._source = source
        self._destination = destination
        self._channel = channel

    def stop(self) -> bool:
        """Check if a message matching the specified criteria has been sent.

        Returns:
            bool: True if a matching message is found, False otherwise.
        """
        runner = self.runner()
        global_context = runner.get_global_context()
        
        # Get messages matching our criteria
        messages = global_context.filter_messages(
            source=self._source,
            destination=self._destination,
            channel=self._channel
        )
        
        # If we found any matching messages, stop
        return len(messages) > 0 