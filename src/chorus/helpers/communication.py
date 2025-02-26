from typing import Optional, Union

from chorus.environment.communication import MessageService, MultiAgentMessageService
from chorus.data.dialog import Message
from chorus.data.context import AgentContext
from chorus.environment.global_context import ChorusGlobalContext
from chorus.helpers.base import AgentHelper


class CommunicationHelper(AgentHelper):
    """Helper class for sending and receiving messages between agents."""

    def __init__(self, context: Union[AgentContext, ChorusGlobalContext]):
        """Initialize the CommunicationHelper.
        
        Args:
            context: The agent context containing message service and agent info.
        """
        super().__init__(context)

    def send_and_wait(
        self,
        destination: str,
        content: str,
        channel: str = None,
        source: str = None,
        timeout: int = 300,
    ) -> Message:
        """Send a message and wait for a response.
        
        Args:
            destination: The ID of the agent to send the message to.
            content: The content of the message.
            channel: Optional channel to send the message on.
            source: Optional source ID, defaults to current agent ID.
            timeout: Maximum time in seconds to wait for response.

        Returns:
            Message: The response message received.
        """
        self.send(destination, content, channel, source)
        return self.wait(destination, source, channel, timeout)

    def send(self, destination: str, content: str, channel: Optional[str] = None, source: Optional[str] = None):
        """Send a message to another agent.
        
        Args:
            destination: The ID of the agent to send the message to.
            content: The content of the message.
            channel: Optional channel to send the message on.
            source: Optional source ID, defaults to current agent ID.

        Returns:
            The result of sending the message.
        """
        context = self.get_context()
        message_service = context.get_message_service()
        assert isinstance(message_service, MultiAgentMessageService) or isinstance(message_service, MessageService)
        if source is None:
            if isinstance(context, ChorusGlobalContext):
                source = context.human_identifier
            else:
                source = self.get_agent_id()
        return message_service.send_message(
            Message(destination=destination, content=content, channel=channel, source=source)
        )

    def wait(
        self, source: str, destination: Optional[str] = None, channel: Optional[str] = None, timeout: int = 300
    ) -> Message:
        """Wait for a response message from another agent.
        
        Args:
            source: The ID of the agent to wait for a message from.
            destination: Optional destination ID, defaults to current agent ID.
            channel: Optional channel to wait on.
            timeout: Maximum time in seconds to wait.

        Returns:
            Message: The received response message.
        """
        context = self.get_context()
        if destination is None:
            if isinstance(context, ChorusGlobalContext):
                destination = context.human_identifier
            else:
                destination = self.get_agent_id()
        message_service = context.get_message_service()
        assert isinstance(message_service, MultiAgentMessageService) or isinstance(message_service, MessageService)
        response = message_service.wait_for_response(
            source=source, destination=destination, channel=channel, timeout=timeout
        )
        return response
    

    def send_raw_message(self, message: Message):
        """Send a raw message to another agent.
        
        Args:
            message: The message to send.
        """
        context = self.get_context()
        message_service = context.get_message_service()
        return message_service.send_message(message)