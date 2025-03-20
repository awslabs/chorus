from typing import Optional
from chorus.data.executable_tool import SimpleExecutableTool
from chorus.data.toolschema import ToolSchema
from chorus.helpers.communication import CommunicationHelper


class AgentCommunicationTool(SimpleExecutableTool):
    """A tool for asynchronous multi-agent collaboration.

    This tool provides functionality for agents to communicate with each other
    asynchronously through messages. Agents can send messages to specific recipients
    or channels, and wait for responses.

    Args:
        allow_waiting: Whether to include the wait action in the tool schema.
    """

    TOOL_NAME = "agent_communication"

    def __init__(self, allow_waiting: bool = True):
        schema = {
            "tool_name": "agent_communication",
            "name": "agent_communication",
            "description": """
Tool for asynchronized multi-agent communication. Notes:
- The recipient_agent parameter must be an agent name or "all".
- The channel parameter is optional but must be a channel name.
- If you want to send a direct message to an agent, use the recipient_agent parameter and leave the channel parameter empty.
- If you want to send a message to an agent on a channel, you must specify both the recipient_agent and the channel parameters.
- If you want to send a message to all agents in the team, you must specify "all" as the recipient_agent and also specify a channel name.
            """.strip(),
            "actions": [
                {
                    "name": "send",
                    "description": "Send a message to an agent.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "recipient_agent": {
                                "type": "string",
                                "description": "The name of the agent to send the message to.",
                            },
                            "content": {
                                "type": "string",
                                "description": "The content of the message to send.",
                            },
                            "channel": {
                                "type": "string",
                                "description": "The channel name to send the message on.",
                            },
                        },
                        "required": ["recipient_agent", "content"],
                    },
                    "output_schema": {},
                },
                {
                    "name": "wait",
                    "description": "Wait for a message from an agent.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "The name of the agent to wait for the message from.",
                            },
                            "channel": {
                                "type": "string",
                                "description": "The channel to wait for the message on.",
                            },
                            "timeout": {
                                "type": "integer",
                                "description": "The maximum time to wait for the message in seconds.",
                            },
                        },
                        "required": ["source"],
                    },
                    "output_schema": {},
                },
            ],
        }
        if not allow_waiting:
            schema["actions"].pop(1)
        super().__init__(ToolSchema.model_validate(schema))

    def send(self, recipient_agent: Optional[str] = None, content: str="", channel: Optional[str] = None):
        """Sends a message to a specific agent or channel.

        Args:
            recipient_agent: The name of the agent to send the message to.
            content: The content of the message.
            channel: The channel to send the message on.

        Raises:
            ValueError: If neither recipient_agent nor channel is provided, or if agent context is not set.
        """
        if self.get_context() is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        if recipient_agent is None and channel is None:
            raise ValueError("Either recipient_agent or channel must be provided.")
        if recipient_agent is None and channel is not None:
            recipient_agent = "all"
        verse = CommunicationHelper(self.get_context())
        verse.send(destination=recipient_agent, content=content, channel=channel)
        return None

    def wait(self, source: str, channel: Optional[str] = None, timeout: Optional[int] = None):
        """Waits for a message from a specific agent or channel.

        Args:
            source: The name of the agent to wait for a message from.
            channel: The channel to wait for a message on.
            timeout: Maximum time to wait in seconds. Defaults to 60.

        Raises:
            ValueError: If agent context is not set.
        """
        if timeout is None:
            timeout = 60
        if self.get_context() is None:
            raise ValueError("MultiAgentTool requires agent context to be set.")
        verse = CommunicationHelper(self.get_context())
        verse.wait(source=source, channel=channel, timeout=timeout)
        return None