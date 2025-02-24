from typing import Dict
from typing import List
from typing import Optional

from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message
from chorus.data.planner_output import PlannerOutput
from chorus.planners.base import MultiAgentPlanner

PLANNER_INSTRUCTION = """
Before calling a sub-agent, generate a plan for solving the task and wrap it in <plan></plan> tags.
In the plan, describe how to solve the problem through calling sub agents. Do not generate agent calls inside plan tag.
"""


@MultiAgentPlanner.register("SimpleMultiAgentPlanner")
class SimpleMultiAgentPlanner(MultiAgentPlanner):
    """A simple planner that generates text-based plans for multi-agent tasks.
    
    This planner generates plans for coordinating multiple agents before making agent
    calls. It requires agents to explicitly state their plans in XML-style tags.
    """

    def __init__(self, agent_description_map: Dict[str, str]):
        """Initialize the SimpleMultiAgentPlanner.

        Args:
            agent_description_map: Dictionary mapping agent IDs to their descriptions/capabilities.
        """
        self.agent_description_map = agent_description_map

    def plan(
        self,
        context: AgentContext,
        state: AgentState,
        history: List[Message],
    ) -> PlannerOutput:
        """Plans the next actions by generating a plan.

        Args:
            context: The agent's context containing configuration and services.
            state: The current state of the agent.
            history: List of previous message interactions.

        Returns:
            A PlannerOutput containing the planner instruction for plan generation.
        """
        return PlannerOutput(planner_instruction=PLANNER_INSTRUCTION)
