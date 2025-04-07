from typing import Dict, List
from pydantic import BaseModel, Field
from typing import Any, Tuple

from chorus.data.state import AgentState

class AgentSnapshot(BaseModel):
    """Snapshot of an agent's configuration for checkpoint restoration.
    
    Contains all necessary information to recreate an agent instance,
    including its class name, agent name, ID, and initialization parameters.
    
    Attributes:
        class_name: The class name of the agent.
        agent_name: The name of the agent.
        agent_id: The unique identifier of the agent.
        init_args: Positional arguments used to initialize the agent.
        init_kwargs: Keyword arguments used to initialize the agent.
    """
    class_name: str
    agent_name: str
    agent_id: str
    init_args: Tuple[Any, ...]
    init_kwargs: Dict[str, Any]
    state_dump: dict

class ChorusCheckpoint(BaseModel):
    """Checkpoint for saving and restoring the state of a Chorus system.
    
    Stores agent configuration snapshots to allow recreation of agents
    with the same initialization parameters.
    
    Attributes:
        agent_snapshot_map: A dictionary mapping agent UUIDs to their respective snapshots.
    """
    agent_snapshot_map: Dict[str, AgentSnapshot] = Field(
        default_factory=dict,
        description="A map of agent UUIDs to their respective snapshots"
    )
