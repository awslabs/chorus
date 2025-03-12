from enum import Enum

from pydantic import BaseModel


class ResourceType(str, Enum):
    """Enumeration of resource types.

    Attributes:
        FILE: Represents a file resource type
    """
    FILE = "file"


class Resource(BaseModel):
    """Base class for resources.

    A resource represents an entity that can be referenced and manipulated,
    such as a file.

    Attributes:
        type: The type of resource, defaults to FILE
        id: Unique identifier for the resource
    """
    type: ResourceType = ResourceType.FILE
    id: str
