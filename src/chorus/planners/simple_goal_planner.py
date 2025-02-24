from typing import Dict
from typing import List
from typing import Optional

from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message
from chorus.data.planner_output import PlannerOutput
from chorus.planners.base import MultiAgentPlanner

PLANNER_INSTRUCTION = """
Before calling a sub-agent, generate goal statement in <goal></goal> tag, then generate a plan for reaching this goal and wrap it in <plan></plan> tag.
In the plan, describe how to reach the goal through calling sub agents. Do not generate agent calls inside plan tag.
"""


@MultiAgentPlanner.register("SimpleMultiAgentGoalPlanner")
class SimpleMultiAgentGoalPlanner(MultiAgentPlanner):
    """A simple planner that generates text-based plans for multi-agent tasks.
    
    This planner generates goal statements and plans for coordinating multiple agents
    before making agent calls. It requires agents to explicitly state goals and plans
    in XML-style tags.

    Args:
        reachable_agents: Dictionary mapping agent IDs to their descriptions/capabilities.
    """

    def __init__(self, reachable_agents: Dict[str, str]):
        self.reachable_agents = reachable_agents

    def plan(
        self,
        context: AgentContext,
        state: AgentState,
        history: List[Message],
    ) -> PlannerOutput:
        """Plans the next actions by generating goal statements and plans.

        Args:
            context: The agent's context containing configuration and services.
            state: The current state of the agent.
            history: List of previous message interactions.

        Returns:
            A PlannerOutput containing the planner instruction for goal/plan generation.
        """
        return PlannerOutput(planner_instruction=PLANNER_INSTRUCTION)
