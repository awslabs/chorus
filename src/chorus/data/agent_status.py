from enum import Enum


class AgentStatus(str, Enum):
    """Enum representing the current status of an agent.

    This enum inherits from str to allow string comparison and serialization.

    Attributes:
        AVAILABLE: Agent is ready to accept new tasks.
        BUSY: Agent is currently working on a task.
        DISABLED: Agent is not accepting any tasks.
    """
    AVAILABLE = "available"
    BUSY = "busy"
    DISABLED = "disabled"
