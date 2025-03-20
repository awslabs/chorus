import json
import logging
import re
from multiprocessing.managers import SyncManager
from typing import Dict, Optional
from typing import List
from typing import Set
from typing import Union

from pydantic import BaseModel
from pydantic import Field

from chorus.communication.message_service import MessageService
from chorus.communication.message_service import MultiAgentMessageService
from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.data.context import AgentContext
from chorus.util.status_manager import MultiAgentStatusManager
from chorus.data.channel import Channel

logger = logging.getLogger(__name__)

DEFAULT_CHANNEL = "general"
DEFAULT_HUMAN_IDENTIFIER = "human"


class ChorusGlobalContext(BaseModel):
    """Global context for the Chorus system.

    Maintains global state and provides access to shared resources and services
    across the system.
    """

    agent_context_map: Dict[str, AgentContext] = Field(default_factory=dict)
    message_service: MessageService = Field(default_factory=MessageService)
    global_message_ids: Set = Field(default_factory=set)
    channels: Dict[str, Channel] = Field(default_factory=dict)
    human_identifier: str = Field(default=DEFAULT_HUMAN_IDENTIFIER)

    def __init__(self, process_manager: SyncManager):
        """Initialize the global context.

        Args:
            process_manager: Optional process manager for multiprocessing support.
        """
        super().__init__()
        self._proc_manager = process_manager
        self._status_manager = MultiAgentStatusManager(process_manager)

    def _collect_messages(self, agent_id: str) -> List[Message]:
        agent_channels = {DEFAULT_CHANNEL}
        for channel in self.channels.values():
            if agent_id in channel.members:
                agent_channels.add(channel.name)
        relevant_messages = []
        for msg in self.message_service.fetch_all_messages():
            if msg.channel is None:
                if msg.source == agent_id or msg.destination == agent_id:
                    relevant_messages.append(msg)
            elif msg.channel in agent_channels:
                relevant_messages.append(msg)
        return relevant_messages

    def _prepare_agent_context(self, context: AgentContext):
        if not isinstance(context.message_service, MultiAgentMessageService):
            context.set_message_service(MultiAgentMessageService(self._proc_manager))
        if context.status_manager is None:
            context.status_manager = self._status_manager

    def register_agent_context(self, context: AgentContext):
        """Register an agent context with the global context.

        Args:
            context: The AgentContext to register.

        Raises:
            AssertionError: If an agent with the same ID is already registered.
        """
        agent_id = context.agent_id
        assert agent_id not in self.agent_context_map, f"Agent {agent_id} already registered"
        self.agent_context_map[agent_id] = context
        self._prepare_agent_context(context)
    
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
        if agent_id not in self.agent_context_map:
            return None
        context: AgentContext = self.agent_context_map[agent_id]
        # Update agent context with messages
        self.sync_agent_messages(agent_id)
        return context

    def sync_agent_messages(self, agent_id: str):
        """Synchronize messages between an agent's local context and the global context.

        Args:
            agent_id: The ID of the agent whose messages to sync.
        """
        if agent_id not in self.agent_context_map:
            return
        context: AgentContext = self.agent_context_map[agent_id]
        relevant_messages = self._collect_messages(agent_id)
        message_service = context.message_service
        assert isinstance(message_service, MultiAgentMessageService)
        agent_messages = message_service.fetch_all_messages()
        existing_message_ids = set()
        for msg in agent_messages:
            existing_message_ids.add(msg.message_id)
        # Receive messages
        for msg in agent_messages:
            if msg.message_id not in self.global_message_ids:
                if msg.source is None:
                    msg.source = agent_id
                message_service.update_message(msg.message_id, msg)
                self.message_service.send_message(msg)
                self.global_message_ids.add(msg.message_id)
                channel_name = msg.channel if msg.channel is not None else "DM"
                content = msg.content
                if msg.event_type == EventType.INTERNAL_EVENT and msg.actions:
                    action_thought_content = msg.content if msg.content is not None else ""
                    action_thought_content = re.sub(
                        r"<function_calls>.*?</function_calls>",
                        "",
                        action_thought_content,
                        flags=re.DOTALL,
                    )
                    content = (
                        "[ACTION]\n"
                        + action_thought_content
                        + "\n---\n"
                        + str(
                            json.dumps(
                                [
                                    act.model_dump(exclude_none=True, exclude_unset=True)
                                    for act in msg.actions
                                ],
                                indent=2,
                            )
                        )
                    )
                if msg.event_type == EventType.INTERNAL_EVENT and msg.observations:
                    content = "[OBSERVATION]\n" + str(msg.observations)
                logger.info(f"==== Received message from {agent_id} to global context ====")
                logger.info(msg.model_dump_json(indent=2))
                logger.info(f"==== *** =====")
                if msg.event_type != EventType.INTERNAL_EVENT:
                    print("===========================================")
                    if msg.actions:
                        content = ""
                        if msg.content is not None:
                            content += msg.content
                        for action in msg.actions:
                            content += f"\nACTION: {action.model_dump_json(indent=2)}"
                    print(
                        f"\033[1m[{channel_name}] {msg.source} -> {msg.destination}:\033[0m\n{content}"
                    )
        # Push new global messages
        for msg in relevant_messages:
            if msg.message_id not in existing_message_ids:
                logger.info(f"==== Pushing message from global context to {agent_id} ====")
                logger.info(msg.model_dump_json(indent=2))
                logger.info(f"==== *** =====")
                message_service.send_message(msg)

    def update_agent_context(self, agent_id: str, context: AgentContext):
        """Update an agent's context and synchronize messages.

        Args:
            agent_id: The ID of the agent whose context to update.
            context: The new AgentContext to set.
        """
        self.agent_context_map[agent_id] = context
        # Update global messages
        self.sync_agent_messages(agent_id)

    def send_message(
        self, message: Optional[Message] = None , source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None, content: Optional[str] = None
    ):
        """Send a message through the global context.

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
        self.message_service.send_message(message)
        self.global_message_ids.add(message.message_id)
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
        return self.message_service.fetch_all_messages()
    
    def filter_messages(self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None) -> List[Message]:
        """Filter messages based on source, destination, and channel.

        Args:
            source: Optional source agent ID to filter by.
            destination: Optional destination agent ID to filter by.
            channel: Optional channel name to filter by.

        Returns:
            List of filtered Message objects.
        """
        return self.message_service.filter_messages(source, destination, channel)

    def status_manager(self) -> MultiAgentStatusManager:
        """Get the global status manager.

        Returns:
            The MultiAgentStatusManager instance.
        """
        return self._status_manager
    
    def get_message_service(self) -> MessageService:
        """Get the global message service.

        Returns:
            The MessageService instance.
        """
        return self.message_service