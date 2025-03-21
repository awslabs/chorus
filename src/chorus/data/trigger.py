from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from abc import ABC, abstractmethod

from chorus.data.dialog import Message, EventType
from chorus.data.executable_tool import ExecutableTool
from chorus.data.resource import Resource

class BaseTrigger(BaseModel):

    @abstractmethod
    def matches(self, message: Message) -> bool:
        """Check if a message matches this trigger's criteria.
        By default returns False unless explicitly implemented.
        """
        return False


class MessageTrigger(BaseTrigger):
    event_type: Optional[str] = None
    event_name: Optional[str] = None
    source: Optional[str] = None
    destination: Optional[str] = None
    channel: Optional[str] = None

    @field_validator('channel')
    @classmethod
    def validate_at_least_one_condition(cls, v, info):
        """Validate that at least one condition is set."""
        conditions = [
            info.data.get('event_type'),
            info.data.get('event_name'),
            info.data.get('source'),
            info.data.get('destination'),
            v  # current channel value
        ]
        if not any(condition is not None for condition in conditions):
            raise ValueError("At least one condition must be set in MessageTrigger")
        return v

    def matches(self, message: Message) -> bool:
        """Check if a message matches this trigger's criteria.
        
        Args:
            message: The message to check against this trigger
            
        Returns:
            True if the message matches all specified criteria, False otherwise
        """
        # Check event_type
        if self.event_type is not None and message.event_type != self.event_type:
            return False
            
        # Check event_name if specified
        if self.event_name is not None and message.event_name != self.event_name:
            return False
            
        # Check source if specified
        if self.source is not None and message.source != self.source:
            return False
            
        # Check destination if specified
        if self.destination is not None and message.destination != self.destination:
            return False
            
        # Check channel if specified
        if self.channel is not None and message.channel != self.channel:
            return False
            
        return True