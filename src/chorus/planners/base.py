from abc import ABCMeta
from abc import abstractmethod
from datetime import datetime
from typing import List
from typing import Optional

from chorus.config import Registrable
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message
from chorus.data.planner_output import PlannerOutput


class MultiAgentPlanner(Registrable, metaclass=ABCMeta):
    """Base class for multi-agent planners that coordinate agent behaviors.

    This class provides the interface for planning and coordinating actions across
    multiple agents in an Chorus system. Subclasses implement specific planning
    strategies.
    """

    def prepare_agent_state(self, agent_state: AgentState) -> None:
        """Prepares the initial state for an agent before planning begins.

        Args:
            agent_state: The agent state to prepare.
        """
        pass

    def plan(
        self,
        context: AgentContext,
        state: AgentState,
        history: List[Message],
    ) -> PlannerOutput:
        """Plans the next actions for an agent based on context and history.

        Args:
            context: The agent's context containing configuration and services.
            state: The current state of the agent.
            history: List of previous message interactions.

        Returns:
            PlannerOutput containing the planned actions and any additional data.
        """
        return PlannerOutput()

    def process_output(
        self,
        context: AgentContext,
        state: AgentState,
        history: List[Message],
        output_messages: List[Message],
    ) -> List[Message]:
        """Processes and potentially modifies the output messages from an agent.

        Args:
            context: The agent's context containing configuration and services.
            state: The current state of the agent.
            history: List of previous message interactions.
            output_messages: The messages produced by the agent.

        Returns:
            The processed list of messages, potentially modified.
        """
        return output_messages
