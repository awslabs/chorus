from typing import Optional
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema
from chorus.helpers.communication import CommunicationHelper


class AgentAsATool(SimpleExecutableTool):
    """A tool that represents an agent for multi-agent collaboration.

    This tool wraps an agent and exposes it as a tool that can be called by other agents.
    It provides a simple interface for sending messages to and receiving responses from
    the wrapped agent.

    Args:
        agent_name: The name of the agent to wrap.
        agent_description: A description of the agent's capabilities.
    """

    def __init__(self, agent_name: str, agent_description: str):
        self._agent_name = agent_name
        self._agent_description = agent_description
        schema = {
            "tool_name": f"agent_{agent_name}",
            "name": f"agent_{agent_name}",
            "description": f"This tool for triggering agent: {agent_name}",
            "actions": [
                {
                    "name": "call",
                    "description": f"Call agent {agent_name}: {agent_description}",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": f"A message to agent {agent_name}",
                            },
                        },
                        "required": ["message"],
                    },
                    "output_schema": {
                        "type": "string",
                    },
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def call(self, message: str) -> Optional[str]:
        """Sends a message to the wrapped agent and returns their response.

        Args:
            message: The message to send to the agent.

        Returns:
            The agent's response message.

        Raises:
            ValueError: If agent context is not set.
        """
        _context = self.get_context()
        if _context is None:
            raise ValueError("AgentAsATool requires agent context to be set.")
        verse = CommunicationHelper(_context)
        verse.send(destination=self._agent_name, content=message)
        return_message = verse.wait(source=self._agent_name)
        if return_message is None:
            return None
        return return_message.content


