from typing import Dict, Optional

from pydantic import BaseModel
from pydantic import Field

from chorus.data.state import AgentState


class RunnerState(BaseModel):
    """Manages the state of agents in Chorus runner.

    This class tracks and updates the state of multiple agents using a dictionary mapping
    agent IDs to their corresponding states.

    """

    agent_state_map: Dict[str, AgentState] = Field(default_factory=dict)

    def get_agent_state(self, agent_id: str) -> Optional[AgentState]:
        """Gets the state of a specific agent.

        Args:
            agent_id: The ID of the agent whose state to retrieve.

        Returns:
            The AgentState object for the specified agent if it exists,
            None otherwise.
        """
        if agent_id not in self.agent_state_map:
            return None
        return self.agent_state_map.get(agent_id)

    def update_agent_state(self, agent_id: str, state: AgentState):
        """Updates the state of a specific agent.

        Args:
            agent_id: The ID of the agent whose state to update.
            state: The new AgentState to associate with the agent.
        """
        self.agent_state_map[agent_id] = state
