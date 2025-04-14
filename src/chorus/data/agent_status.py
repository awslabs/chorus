from enum import Enum

from pydantic import BaseModel


class AgentStatus(str, Enum):
    """Enum representing the current status of an agent.

    This enum inherits from str to allow string comparison and serialization.

    Attributes:
        IDLE: Agent is ready to accept new tasks.
        BUSY: Agent is currently working on a task.
        DISABLED: Agent is not accepting any tasks.
        ERROR: Agent is in an error state.
        DISCONNECTED: Agent is not connected to the network.
    """
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"
    DISCONNECTED = "disconnected"

class AgentStatusRecord(BaseModel):
    status: AgentStatus
    last_active_timestamp: int
