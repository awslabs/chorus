import json
import logging
import re
from typing import Dict, Optional, Any
from typing import List
from typing import Set
from typing import Union

from pydantic import BaseModel
from pydantic import Field

from chorus.communication.message_service import ChorusMessageRouter
from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.data.context import AgentContext
from chorus.util.status_manager import MultiAgentStatusManager
from chorus.data.channel import Channel

logger = logging.getLogger(__name__)

DEFAULT_CHANNEL = "general"
DEFAULT_HUMAN_IDENTIFIER = "human"


class ChorusGlobalContext:
    """Global context for the Chorus system.

    Maintains global state and provides access to shared resources and services
    across the system.
    """

    def __init__(self, zmq_router_port: int = 5555):
        """Initialize the global context.

        Args:
            zmq_router_port: Port for the ZMQ router socket
            process_manager: Legacy parameter for compatibility, not used in ZMQ implementation
        """
        # Initialize attributes with defaults
        self.global_message_ids = set()
        self.channels = {}
        self.human_identifier = DEFAULT_HUMAN_IDENTIFIER
        self.zmq_router_port = zmq_router_port
        
        # Initialize ZMQ router
        try:
            # Create a message router just for initialization, to check port availability
            self._message_router = ChorusMessageRouter(port=zmq_router_port)
            # Update with the actual port used (which might be different if the original was in use)
            self.zmq_router_port = self._message_router.port
            
            # Set up status manager
            self._status_manager = MultiAgentStatusManager()
            
            # Start the router
            self._message_router.start()
            
            # Store messages directly in context instead of in router
            self._message_history = []
            
            logger.info(f"ZMQ router started on port {self.zmq_router_port}")
        except Exception as e:
            logger.error(f"Failed to initialize ZMQ router: {e}")
            raise

    def register_channel(self, channel: Channel):
        """Register a communication channel.

        Args:
            channel: The Channel object to register.
        """
        self.channels[channel.name] = channel

    def get_agent_context(self, agent_id: str) -> Optional[AgentContext]:
        """Get the context for a specific agent.

        Args:
            agent_id: The ID of the agent whose context to retrieve.

        Returns:
            The agent's context if found, None otherwise.
        """
        return NotImplementedError


    def sync_agent_messages(self, agent_id: str):
        """Synchronize messages between an agent's local context and the global context.

        This method is not actively used with ZMQ as messages are automatically
        routed to relevant agents.

        Args:
            agent_id: The ID of the agent whose messages to sync.
        """
        # This method is not needed with ZMQ as messages are routed directly
        pass

    def update_agent_context(self, agent_id: str, context: AgentContext):
        """Update an agent's context.

        Args:
            agent_id: The ID of the agent whose context to update.
            context: The new AgentContext to set.
        """
        self.agent_context_map[agent_id] = context

    def send_message(
        self, message: Optional[Message] = None, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None, content: Optional[str] = None
    ):
        """Send a message through the global context.

        This method adds the message to the global message history and forwards it
        to the message router to be distributed to agents.

        Args:
            message: Optional Message object to send.
            source: Optional source agent ID.
            destination: Optional destination agent ID.
            channel: Optional channel name.
            content: Optional message content.

        Raises:
            ValueError: If neither message nor content is provided.
        """
        if message is None and content is None:
            raise ValueError("Message or content must be provided when sending a message")
        if message is None:
            message = Message()
        if source is not None:
            message.source = source
        if destination is not None:
            message.destination = destination
        if channel is not None:
            message.channel = channel
        if content is not None:
            message.content = content
            
        # Generate message ID if needed
        if message.message_id is None:
            import uuid
            message.message_id = str(uuid.uuid4().hex)
            
        # Add to global message history
        if message.message_id not in self.global_message_ids:
            self._message_history.append(message)
            self.global_message_ids.add(message.message_id)
            
        # Route through the ZMQ router
        self._message_router.send_message(message)
            
        # Log the message
        channel_name = message.channel if message.channel is not None else "DM"
        if message.actions:
            if message.content is None:
                content = ""
            else:
                content = message.content
            for action in message.actions:
                content += f"\nACTION: {action.model_dump_json(indent=2)}"
        else:
            content = message.content
        print("===========================================")
        print(
            f"\033[1m[{channel_name}] {message.source} -> {message.destination}:\033[0m\n{content}"
        )

    def fetch_all_messages(self) -> List[Message]:
        """Fetch all messages in the global context.

        Returns:
            List of all Message objects.
        """
        # Update with the latest messages from the router
        if hasattr(self, "_message_router"):
            router_messages = self._message_router.fetch_all_messages()
            for msg in router_messages:
                if msg.message_id not in self.global_message_ids:
                    self._message_history.append(msg)
                    self.global_message_ids.add(msg.message_id)
                    
        return self._message_history
    
    def filter_messages(self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None) -> List[Message]:
        """Filter messages based on source, destination, and channel.

        Args:
            source: Optional source agent ID to filter by.
            destination: Optional destination agent ID to filter by.
            channel: Optional channel name to filter by.

        Returns:
            List of filtered Message objects.
        """
        return [
            msg for msg in self._message_history
            if (source is None or msg.source == source)
            and (destination is None or msg.destination == destination)
            and (channel is None or msg.channel == channel)
        ]

    def status_manager(self) -> MultiAgentStatusManager:
        """Get the global status manager.

        Returns:
            The MultiAgentStatusManager instance.
        """
        return self._status_manager
    
    def is_agent_in_channel(self, agent_id: str, channel_name: str) -> bool:
        """Check if an agent is a member of a channel.
        
        Args:
            agent_id: The agent ID to check
            channel_name: The channel name to check
            
        Returns:
            True if the agent is in the channel, False otherwise
        """
        if channel_name == DEFAULT_CHANNEL:
            return True
            
        if channel_name in self.channels:
            channel = self.channels[channel_name]
            return agent_id in channel.members
            
        return False
    
    def request_agent_state(self, agent_id: str):
        """Request the current state from an agent.
        
        Args:
            agent_id: The agent ID to request state from
        """
        if hasattr(self, "_message_router"):
            self._message_router.request_agent_state(agent_id)
    
    def stop_agent(self, agent_id: str):
        """Send a stop signal to an agent.
        
        Args:
            agent_id: The agent ID to stop
        """
        if hasattr(self, "_message_router"):
            self._message_router.stop_agent(agent_id)
            
    def shutdown(self):
        """Shutdown the global context, stopping all services."""
        logger.info("Shutting down ChorusGlobalContext")
        try:
            if hasattr(self, "_message_router"):
                self._message_router.stop()
                logger.info("ZMQ router successfully stopped")
        except Exception as e:
            logger.error(f"Error during global context shutdown: {e}")
            # Continue with shutdown even if there are errors
            
    def get_message_router(self):
        """Get the message router for backward compatibility.
        
        Returns:
            The ZMQMessageRouter instance
        """
        return self._message_router