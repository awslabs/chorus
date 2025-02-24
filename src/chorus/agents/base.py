from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from chorus.config.registrable import Registrable
from chorus.data.context import AgentContext
from chorus.data.state import AgentState


class Agent(Registrable, metaclass=ABCMeta):
    """Base class for all agents in the Chorus framework.

    This abstract class defines the core interface that all agents must implement.
    It provides basic initialization methods and requires implementing an iterate method
    for the agent's main processing loop.
    """

    def init_context(self) -> AgentContext:
        """Initialize the agent's context.

        Creates a new AgentContext instance with a unique ID for this agent.

        Returns:
            AgentContext: A new context object for this agent.
        """
        return AgentContext(agent_id=str(id(self)))

    def init_state(self) -> AgentState:
        """Initialize the agent's state.

        Creates a new AgentState instance with default values.

        Returns:
            AgentState: A new state object for this agent.
        """
        return AgentState()

    @abstractmethod
    def iterate(self, context: AgentContext, state: AgentState) -> Optional[AgentState]:
        """Execute one iteration of the agent's processing loop.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.

        Returns:
            Optional[AgentState]: The updated agent state after processing,
                or None if no state update is needed.
        """
        pass
