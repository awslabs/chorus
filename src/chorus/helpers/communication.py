from typing import Optional, Union
import time

from chorus.communication.message_service import ChorusMessageClient, ChorusMessageRouter
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
        channel: Optional[str] = None,
        source: Optional[str] = None,
        timeout: int = 300,
    ) -> Optional[Message]:
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
        # Just use the separate send and wait methods which handle both types of contexts
        self.send(destination, content, channel, source)
        return self.wait(source=destination, destination=source, channel=channel, timeout=timeout)

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
        if isinstance(context, ChorusGlobalContext):
            # If this is a global context, use send_message directly
            return context.send_message(
                source=source or context.human_identifier,
                destination=destination,
                channel=channel,
                content=content
            )
        else:
            # If this is an agent context, use the message client
            message_service = context.get_message_client()
            if source is None:
                source = self.get_agent_id()
            return message_service.send_message(
                Message(destination=destination, content=content, channel=channel, source=source)
            )

    def wait(
        self, source: str, destination: Optional[str] = None, channel: Optional[str] = None, timeout: int = 300
    ) -> Optional[Message]:
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
                
        if isinstance(context, ChorusGlobalContext):
            # For global context, we get all messages and filter
            start_time = time.time()
            seen_message_ids = set()
            
            # Get initial messages
            messages = context.filter_messages(
                source=source, destination=destination, channel=channel
            )
            
            # Record IDs of messages we've already seen
            for msg in messages:
                seen_message_ids.add(msg.message_id)
                
            while time.time() - start_time < timeout:
                # Get latest messages
                messages = context.filter_messages(
                    source=source, destination=destination, channel=channel
                )
                
                # Look for new messages
                for msg in messages:
                    if msg.message_id not in seen_message_ids:
                        return msg
                        
                # Sleep briefly to avoid busy waiting
                time.sleep(0.5)
                
            return None
        else:
            # If this is an agent context, use the message client
            message_service = context.get_message_client()
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
        message_service = context.get_message_client()
        return message_service.send_message(message)