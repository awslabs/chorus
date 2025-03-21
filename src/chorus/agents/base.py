from abc import ABCMeta
from abc import abstractmethod
from typing import Optional

from chorus.config.registrable import Registrable
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.util.agent_naming import get_unique_agent_name

class Agent(Registrable, metaclass=ABCMeta):
    """Base class for all agents in the Chorus framework.

    This abstract class defines the core interface that all agents must implement.
    It provides basic initialization methods and requires implementing an iterate method
    for the agent's main processing loop.
    """
    def __init__(self, name: Optional[str] = None):
        """Initialize a new agent.

        Args:
            name (str, optional): The name of the agent. If not provided, defaults to None.
                The name is used to identify and refer to the agent.
        """
        if name is None:
            name = get_unique_agent_name()
        self._name = name
    
    def agent_name(self) -> str:
        """Get the name of the agent.

        Returns:
            str: The name of the agent.
        """
        return self._name
    
    def create_agent_context_id(self) -> str:
        """Create a unique context ID for the agent.

        Returns:
            str: An agent context ID.
        """
        return self._name

    def init_context(self) -> AgentContext:
        """Initialize the agent's context.

        Creates a new AgentContext instance with a unique ID for this agent.

        Returns:
            AgentContext: A new context object for this agent.
        """
        return AgentContext(agent_id=self.create_agent_context_id())

    def init_state(self) -> AgentState:
        """Initialize the agent's state.

        Creates a new AgentState instance with default values.

        Returns:
            AgentState: A new state object for this agent.
        """
        return AgentState()

    @abstractmethod
    def iterate(self, context: AgentContext, state: AgentState) -> AgentState:
        """Execute one iteration of the agent's processing loop.

        Args:
            context: The agent's context containing environmental information.
            state: The current state of the agent.

        Returns:
            AgentState: The updated agent state after processing.
        """
        pass
