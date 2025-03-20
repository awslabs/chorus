from abc import ABC, abstractmethod
from typing import List

from chorus.data.dialog import Message, EventType
from chorus.data.message_view import MessageView


class MessageViewSelector(ABC):
    """
    A class that selects the appropriate message view for a given message.
    """

    @abstractmethod
    def select(self, message_history: List[Message], incoming_message: Message) -> MessageView:
        """
        Selects the appropriate message view for a given message.

        Args:
            message_history: The message history to select the message view from.

        Returns:
            The selected message view.
        """

class DirectMessageViewSelector(MessageViewSelector):
    """
    A message view selector that selects the direct messages between the other parties.
    """

    def __init__(self, include_internal_events: bool = False):
        self.include_internal_events = include_internal_events

    def select(self, message_history: List[Message], incoming_message: Message) -> MessageView:
        """
        Selects direct messages between the source and destination of the incoming message
        that are in the same channel.

        Args:
            message_history: The complete message history to filter from.
            incoming_message: The message that triggered this selection.

        Returns:
            A MessageView containing relevant direct messages.
        """
        source = incoming_message.source
        destination = incoming_message.destination
        channel = incoming_message.channel
        
        # Filter messages that are direct communications between these parties in the same channel
        filtered_messages = []
        for msg in message_history:
            # Skip internal events if include_internal_events is False
            if not self.include_internal_events and msg.event_type == EventType.INTERNAL_EVENT:
                continue
                
            if ((msg.source == source and msg.destination == destination) or
                (msg.source == destination and msg.destination == source)) and \
               msg.channel == channel:
                filtered_messages.append(msg)
                
            # Stop once we reach the incoming message
            if msg.message_id == incoming_message.message_id:
                break
        
        # Return the filtered messages
        return MessageView(view_id=f"direct_message:{source}", messages=filtered_messages)

class ChannelMessageViewSelector(MessageViewSelector):
    """
    A message view selector that selects the messages in the same channel as the incoming message.
    If the incoming message is a direct message, the message view will contain direct messages between
    the source and destination of the incoming message.
    """

    def __init__(self, include_internal_events: bool = False):
        self.include_internal_events = include_internal_events

    def select(self, message_history: List[Message], incoming_message: Message) -> MessageView:
        """
        Selects messages in the same channel as the incoming message.
        """
        channel = incoming_message.channel
        source = incoming_message.source
        destination = incoming_message.destination
        
        # Check if this is a direct message
        if source and destination and source != destination:
            # For direct messages, use the DirectMessageViewSelector logic
            filtered_messages = []
            for msg in message_history:
                if ((msg.source == source and msg.destination == destination) or
                    (msg.source == destination and msg.destination == source)) and \
                   msg.channel == channel:
                    filtered_messages.append(msg)
                
                # Stop once we reach the incoming message
                if msg.message_id == incoming_message.message_id:
                    break
            view_id = f"direct_message:{source}"
        else:
            # For channel messages, include all messages in the same channel
            filtered_messages = []
            for msg in message_history:
                if msg.channel == channel:
                    filtered_messages.append(msg)
                
                # Stop once we reach the incoming message
                if msg.message_id == incoming_message.message_id:
                    break
            view_id = f"channel:{channel}"
            
        return MessageView(view_id=view_id, messages=filtered_messages)

class GlobalMessageViewSelector(MessageViewSelector):
    """
    A message view selector that selects all messages in the message history.
    """

    def __init__(self, include_internal_events: bool = False):
        self.include_internal_events = include_internal_events

    def select(self, message_history: List[Message], incoming_message: Message) -> MessageView:
        """
        Selects all messages in the message history.
        """
        filtered_messages = []
        for msg in message_history:
            filtered_messages.append(msg)
            # Stop once we reach the incoming message
            if msg.message_id == incoming_message.message_id:
                break

        return MessageView(view_id="global", messages=filtered_messages)
