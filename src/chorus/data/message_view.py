
from typing import List
from pydantic import BaseModel

from chorus.data.dialog import Message


class MessageView(BaseModel):
    """
    A message view is a collection of messages that are selected from the entire message history.
    """
    view_id: str
    messages: List[Message]
