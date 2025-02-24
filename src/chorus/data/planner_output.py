from typing import List
from typing import Optional

from pydantic import BaseModel

from chorus.data.dialog import Message
from chorus.data.toolschema import ToolSchema


class PlannerOutput(BaseModel):
    """Output data model for the planner component.

    This class represents the output produced by a planner, including instructions,
    messages, and tool schemas.

    Attributes:
        planner_instruction: Optional instruction string for the planner itself.
        agent_instruction: Optional instruction string for the agent.
        messages: Optional list of Message objects representing planned messages.
        tool_schemas: Optional list of ToolSchema objects defining available tools.
    """
    planner_instruction: Optional[str] = None
    agent_instruction: Optional[str] = None
    messages: Optional[List[Message]] = None
    tool_schemas: Optional[List[ToolSchema]] = None
