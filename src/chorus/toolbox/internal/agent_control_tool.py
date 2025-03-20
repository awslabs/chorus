from typing import Any, Dict, Optional
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema


class AgentControlTool(SimpleExecutableTool):
    """A tool for controlling agent workflow.

    This tool provides functionality for agents to control their workflow,
    such as signaling completion of tasks.
    """

    def __init__(self):
        schema = {
            "tool_name": "agent_control",
            "name": "agent_control",
            "description": "Tool for controlling agent workflow.",
            "actions": [
                {
                    "name": "finish",
                    "description": "Finish this round of agent actions. Trigger this function if there is nothing more to do.",
                    "input_schema": {"type": "object", "properties": {}, "required": []},
                    "output_schema": {},
                },
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))
    
    def get_finish_action_name(self) -> str:
        """Get the finish action name from the tool schema."""
        return "finish"

    def finish(self):
        """Signals completion of the current multi-agent communication round."""
        return None