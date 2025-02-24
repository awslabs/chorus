from typing import List
from pydantic import BaseModel, Field


class Channel(BaseModel):
    """A communication channel that can have multiple members.

    This class represents a named channel that multiple members can join to communicate
    with each other. It uses Pydantic for data validation.

    Attributes:
        name: The name of the channel.
        members: List of member identifiers who are part of this channel. Defaults to empty list.
    """
    name: str
    members: List[str] = Field(default_factory=list)