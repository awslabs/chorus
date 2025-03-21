import time
import uuid
from multiprocessing.managers import SyncManager
from typing import List
from typing import Optional
from queue import Queue

from pydantic import BaseModel
from pydantic import Field

from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.data.channel import Channel


class MessageService(BaseModel):
    """
    A message service that manages the message history and queue for an agent.
    """

    message_history: List[Message] = Field(default_factory=list)

    def create_message_id(self) -> str:
        return uuid.uuid4().hex

    def fetch_all_messages(self) -> List[Message]:
        return self.message_history

    def filter_messages(
        self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None, exclude_actions_observations: bool = True
    ) -> List[Message]:
        return [
            msg
            for msg in self.message_history
            if (source is None or msg.source == source)
            and (destination is None or msg.destination == destination)
            and (channel is None or msg.channel == channel)
            and (not exclude_actions_observations or not msg.actions)
            and (not exclude_actions_observations or not msg.observations)
        ]

    def update_message(self, message_id: str, message: Message):
        for idx, msg in enumerate(self.message_history):
            if msg.message_id == message_id:
                self.message_history[idx] = message

    def send_messages(self, messages: List[Message]):
        for msg in messages:
            self.send_message(msg)

    def send_message(self, message: Message):
        if message.message_id is None:
            message.message_id = self.create_message_id()
        self.message_history.append(message)

    def refresh_history(self, messages: List[Message]):
        self.message_history = messages
    
    def wait_for_response(
        self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None, event_type: Optional[str] = None, timeout: int = 300
    ) -> Optional[Message]:
        """Wait for a response message matching the given criteria.
        
        Args:
            source: Optional source ID to filter messages by
            destination: Optional destination ID to filter messages by 
            channel: Optional channel to filter messages by
            event_type: Optional event type to filter messages by
            timeout: Maximum time in seconds to wait for response

        Returns:
            Message matching criteria if found within timeout, otherwise None
        """
        if source is None and channel is None:
            return None

        # Create set to track observed message IDs for this wait call
        observed_message_ids = set()
        # Add existing message IDs to observed set to avoid returning old messages
        for message in self.filter_messages(source=source, destination=destination, channel=channel):
            observed_message_ids.add(message.message_id)
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.filter_messages(source=source, destination=destination, channel=channel)
            # Look for unobserved messages
            for message in messages:
                if message.message_id not in observed_message_ids:
                    return message
                    
            time.sleep(0.1)
            
        return None


class MultiAgentMessageService(MessageService):
    """
    A message service that manages the message history and queue in multi-agent environment.
    """

    def __init__(self, proc_manager: SyncManager):
        super().__init__()
        self.message_history = list(proc_manager.list())

    def fetch_all_messages(self) -> List[Message]:
        return [Message.model_validate_json(msg) for msg in self.message_history]

    def filter_messages(
        self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None
    ) -> List[Message]:
        all_messages = self.fetch_all_messages()
        return [
            msg
            for msg in all_messages
            if (source is None or msg.source == source)
            and (destination is None or msg.destination == destination)
            and (channel is None or msg.channel == channel)
        ]

    def send_message(self, message: Message):
        if message.message_id is None:
            message.message_id = self.create_message_id()
        self.message_history.append(message.model_dump_json())

    def update_message(self, message_id: str, message: Message):
        for idx, msg in enumerate(self.fetch_all_messages()):
            if msg.message_id == message_id:
                self.message_history[idx] = message.model_dump_json()

    def refresh_history(self, messages: List[Message]):
        while self.message_history:
            self.message_history.pop()
        for msg in messages:
            self.send_message(msg)

    def wait_for_response(
        self, source: Optional[str] = None, destination: Optional[str] = None, channel: Optional[str] = None, event_type: Optional[str] = None, timeout: int = 300
    ) -> Optional[Message]:
        if source is None and channel is None:
            return None
        all_messages = self.fetch_all_messages()
        last_outbound_msg = None
        for msg in all_messages:
            if msg.source == destination and msg.channel == channel:
                last_outbound_msg = msg
        if last_outbound_msg is not None:
            all_messages = all_messages[: all_messages.index(last_outbound_msg)]
        observed_message_ids = set(msg.message_id for msg in all_messages)
        timestamp = time.time()
        while time.time() - timestamp < timeout:
            messages = self.fetch_all_messages()
            for msg in messages:
                if msg.message_id in observed_message_ids:
                    continue
                if msg.event_type == EventType.INTERNAL_EVENT:
                    continue
                if (
                    msg.source == source
                    and msg.destination == destination
                    and msg.channel == channel
                    and (event_type is None or msg.event_type == event_type)
                ):
                    return msg
            time.sleep(1)
        return None
