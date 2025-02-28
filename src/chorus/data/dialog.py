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


class Role(str, Enum):
    """Enumeration of possible roles in a dialog.

    Attributes:
        USER: Role for user messages
        BOT: Role for bot/assistant messages
        SYSTEM: Role for system messages
        THOUGHT: Role for thought/reasoning steps
        ACTION: Role for tool action calls
        OBSERVATION: Role for tool observations/results
    """
    USER = "User"
    BOT = "Bot"
    SYSTEM = "System"
    THOUGHT = "Thought"
    ACTION = "Action"
    OBSERVATION = "Observation"


class BaseEvent(BaseModel):
    """Base class for all dialog events.

    Attributes:
        event_type: String identifier for the event type
        meta: Optional metadata dictionary for the event
    """
    event_type: str = "event"
    meta: Optional[Dict[str, Dict]] = Field(default_factory=dict)


class Message(BaseEvent):
    """Defines a message event in a dialog.

    Attributes:
        event_type: Type identifier, defaults to "message"
        event_name: Optional name for the event
        role: Role of the message sender
        source: ID of message sender
        destination: ID of message recipient
        channel: Optional communication channel identifier
        actions: List of tool actions in the message
        observations: List of tool observations in the message
        message_id: Unique identifier for the message
        message_timestamp: Unix timestamp of the message
        content: Text content of the message
        structured_content: Optional structured data content
        content_type: Optional content type identifier
        artifacts: Optional dictionary of message artifacts
        speaker_id: ID used to look up speaker-specific metadata
        skip_for_inference: Whether to skip this turn during inference
        skip_all_but_latest: ID to keep only latest turn with this value
    """
    event_type: str = "message"
    event_name: Optional[str] = None
    role: Optional[Role] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    channel: Optional[str] = None
    actions: Optional[List[ActionData]] = None
    observations: Optional[List[ObservationData]] = None
    message_id: Optional[str] = None
    message_timestamp: Optional[int] = Field(default_factory=lambda: int(time.time()))
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
        if self.role == Role.OBSERVATION:
            return self.observations if self.observations else []

    def extract_action(self) -> ActionData:
        """Extract a single action from this message turn.

        Returns:
            The first ActionData if this is an action message, None otherwise.
        """
        if self.role == Role.ACTION:
            return self.actions[0] if self.actions else None
        else:
            return None

    def extract_observation(self) -> JsonData:
        """Extract a single observation from this message turn.

        Returns:
            The first observation if this is an observation message, None otherwise.
        """
        if self.role == Role.OBSERVATION:
            return self.observations[0] if self.observations else None
        else:
            return None
    
    def clone(self):
        """Clone the message.

        Returns:
            A new Message object with the same content and metadata.
        """
        new_message = Message(**self.model_dump())
        new_message.message_id = None
        new_message.message_timestamp = int(time.time())
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
    meta: Optional[Dict[str, Dict]] = Field(default_factory=dict)

    def hash(self):
        """Generate a unique hash for this dialog.

        Returns:
            Hash string excluding dialog_id and meta fields
        """
        return unique_hash_for_model(self, excluded_fields={"dialog_id", "meta"})


class DialogSet(BaseModel):
    """Collection of dialogs with associated tools.

    Attributes:
        dialogset_id: Unique identifier for the dialog set
        dialogs: List of Dialog objects in the set
        tool_db: Optional database of tools available for these dialogs
        meta: Optional dataset-level metadata
    """

    dialogset_id: str
    dialogs: List[Dialog]
    tool_db: Optional[ToolDB] = None
    meta: Optional[Dict[str, Dict]] = Field(default_factory=dict)


def read_dialogset(dialogset_path: Path):
    """Read a DialogSet from a JSON file.

    Args:
        dialogset_path: Path to the JSON file

    Returns:
        Parsed DialogSet object
    """
    return DialogSet.model_validate_json(dialogset_path.read_text(encoding="utf-8"))


def write_dialogset(dialogset: DialogSet, dialogset_path: Path):
    """Write a DialogSet to a JSON file.

    Args:
        dialogset: DialogSet object to write
        dialogset_path: Path to write the JSON file
    """
    dialogset_path.parent.mkdir(exist_ok=True, parents=True)
    dialogset_path.write_text(
        dialogset.model_dump_json(
            indent=4, by_alias=True, exclude_none=True, exclude_defaults=True
        ),
        encoding="utf-8",
    )
