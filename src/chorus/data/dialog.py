"""Dialog data models for Chorus.

This module defines the core data structures for representing dialogs, messages,
and dialog collections in Chorus. It includes models for individual messages,
complete dialogs, and sets of dialogs with associated tools.
"""

from enum import Enum
from pathlib import Path
import time
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
import uuid

from pydantic import BaseModel
from pydantic import Field
from pydantic import TypeAdapter
from pydantic import field_validator
from pydantic_core.core_schema import ValidationInfo

from chorus.data.data_types import ActionData
from chorus.data.data_types import ObservationData
from chorus.data.schema import JsonData
from chorus.data.toolschema import ToolDB
from chorus.data.utils import unique_hash_for_model


class EventType(str, Enum):
    """Enumeration of possible event types.

    Attributes:
        MESSAGE: Type identifier for message events
    """
    EVENT = "event"
    MESSAGE = "message"
    NOTIFICATION = "notification"
    INTERNAL_EVENT = "internal_event"

class BaseEvent(BaseModel):
    """Base class for all dialog events.

    Attributes:
        event_type: String identifier for the event type
        meta: Optional metadata dictionary for the event
    """
    event_type: EventType = EventType.EVENT
    meta: Dict[str, Dict] = Field(default_factory=dict)


class Message(BaseEvent):
    """Defines a message event in a dialog.

    Attributes:
        event_type: Type identifier, defaults to "message"
        event_name: Optional name for the event
        source: ID of message sender
        destination: ID of message recipient
        channel: Optional communication channel identifier
        actions: List of tool actions in the message
        observations: List of tool observations in the message
        message_id: Unique identifier for the message
        timestamp: Unix timestamp of the message
        content: Text content of the message
        structured_content: Optional structured data content
        content_type: Optional content type identifier
        artifacts: Optional dictionary of message artifacts
        speaker_id: ID used to look up speaker-specific metadata
        skip_for_inference: Whether to skip this turn during inference
        skip_all_but_latest: ID to keep only latest turn with this value
    """
    event_type: EventType = EventType.MESSAGE
    event_name: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    channel: Optional[str] = None
    actions: Optional[List[ActionData]] = None
    observations: Optional[List[ObservationData]] = None
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4().hex))
    timestamp: int = Field(default_factory=lambda: int(time.time()))
    # Artifacts
    content: Optional[str] = None
    structured_content: Optional[JsonData] = None
    content_type: Optional[str] = None
    artifacts: Optional[Dict[str, Dict]] = None

    def extract_actions(self) -> List[ActionData]:
        """Extract actions from this message turn.

        Currently only supports single actions, parallel action support pending.

        Returns:
            List of ActionData objects from this message.
        """
        return self.actions if self.actions else []

    def extract_observations(self) -> List[JsonData]:
        """Extract observations from this message turn.

        Returns:
            List of observation data if this is an observation message, empty list otherwise.
        """
        if self.event_type == EventType.INTERNAL_EVENT and self.observations:
            return self.observations
        return []

    def extract_action(self) -> Optional[ActionData]:
        """Extract a single action from this message turn.

        Returns:
            The first ActionData if this is an action message, None otherwise.
        """
        if self.event_type == EventType.INTERNAL_EVENT and self.actions:
            return self.actions[0]
        return None

    def extract_observation(self) -> JsonData:
        """Extract a single observation from this message turn.

        Returns:
            The first observation if this is an observation message, None otherwise.
        """
        if self.event_type == EventType.INTERNAL_EVENT and self.observations:
            return self.observations[0]
        return None
    
    def clone(self):
        """Clone the message.

        Returns:
            A new Message object with the same content and metadata.
        """
        new_message = Message(**self.model_dump())
        new_message.message_id = None
        new_message.timestamp = int(time.time())
        return new_message

    speaker_id: Optional[str] = None
    skip_for_inference: Optional[bool] = Field(default=False)
    skip_all_but_latest: Optional[str] = Field(default=None)

    @staticmethod
    def parse_turns(turns: List[Dict]) -> List["Message"]:
        """Parse a list of turn dictionaries into Message objects.

        Args:
            turns: List of dictionaries representing message turns

        Returns:
            List of parsed Message objects
        """
        adapter = TypeAdapter(List[Message])
        return adapter.validate_python(turns)

    @staticmethod
    def convert_to_dict(turns: List["Message"]) -> List[Dict]:
        """Convert a list of Message objects to dictionaries.

        Args:
            turns: List of Message objects to convert

        Returns:
            List of dictionary representations of the messages
        """
        adapter = TypeAdapter(List[Message])
        return adapter.dump_python(turns)


class Dialog(BaseModel):
    """A complete dialog consisting of turns and available tools.

    Attributes:
        dialog_id: Unique identifier for the dialog
        turns: List of message turns in the dialog
        toolbox: List of tool IDs available in this dialog
        meta: Optional dialog-level metadata
    """

    dialog_id: str
    turns: List[Message]
    toolbox: List[str]
    meta: Dict[str, Dict] = Field(default_factory=dict)

    def hash(self):
        """Generate a unique hash for this dialog.

        Returns:
            Hash string excluding dialog_id and meta fields
        """
        return unique_hash_for_model(self, excluded_fields={"dialog_id", "meta"})