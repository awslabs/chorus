import os
from datetime import datetime
from datetime import timedelta
from typing import Optional

from chorus.data import ExecutableTool
from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.data import Message
from chorus.data.data_types import ActionData
from chorus.data.schema import JsonData
from chorus.helpers import CommunicationHelper
from chorus.util.async_actions import make_async_observation_data

NOT_IN_A_TEAM_ERROR_MESSAGE = "Error: This agent is not part of a team."
TIMEOUT = 10


class TeamToolClient(ExecutableTool):
    """
    A client for executing tools in the team's toolbox.
    """

    def __init__(self, tool: ExecutableTool):
        self._tool_schema = tool.get_schema()
        super().__init__(self._tool_schema)
    
    def execute(self, action_name: Optional[str] = None, parameters: Dict = None) -> JsonData:
        if action_name is None:
            raise ValueError("Action name needs to be specified.")
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        message = Message(
            event_type="team_service",
            destination=team_name,
            actions=[
                ActionData(
                    tool_name="team_toolbox",
                    action_name="execute_tool",
                    parameters={
                        "tool_name": self._tool_schema.tool_name,
                        "action_name": action_name,
                        "parameters": parameters
                    }
                )
            ]
        )
        context.message_service.send_message(message)
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        return observation_message.observations[0].data


class AsyncTeamToolClient(TeamToolClient):
    """
    A client for executing tools in the team's toolbox asynchronously.
    """

    def execute(self, action_name: Optional[str] = None, parameters: Dict = None) -> JsonData:
        if action_name is None:
            raise ValueError("Action name needs to be specified.")
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_id = context.team_info.get_identifier()
        async_response = make_async_observation_data(
            action_name=action_name,
            tool_name=self._tool_schema.tool_name,
            expected_source=team_id
        )
        message = Message(
            event_type="team_service",
            source=context.agent_id,
            destination=team_id,
            actions=[
                ActionData(
                    tool_name="team_toolbox",
                    action_name="execute_tool",
                    parameters={
                        "tool_name": self._tool_schema.tool_name,
                        "action_name": action_name,
                        "parameters": parameters
                    },
                    async_execution_id=async_response.get("async_execution_id", None)
                )
            ]
        )
        context.message_service.send_message(message)
        return async_response


@ExecutableTool.register("TeamToolboxClient")
class TeamToolboxClient(SimpleExecutableTool):
    """
    A toolbox for team tools.
    """

    def __init__(self):
        schema = {
            "tool_name": "TeamToolbox",
            "name": "TeamToolbox", 
            "description": "A tool for executing other tools in the team's toolbox",
            "actions": [
                {
                    "name": "execute_tool",
                    "description": "Execute a tool from the team's toolbox",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "Name of the tool to execute"},
                            "action_name": {"type": "string", "description": "Name of the action to execute"},
                            "parameters": {"type": "object", "description": "Parameters to pass to the action"},
                            "async_mode": {"type": "boolean", "description": "Whether to execute asynchronously"},
                            "tool_use_id": {"type": "string", "description": "Optional ID to track tool usage"}
                        },
                        "required": ["tool_name", "action_name", "parameters"]
                    }
                },
                {
                    "name": "list_tools",
                    "description": "List all tools in the team's toolbox",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def execute_tool(self, action_name: str, tool_name: Optional[str] = None, parameters: Optional[Dict] = None, async_mode: bool = False, tool_use_id: Optional[str] = None) -> JsonData:
        """
        Execute a tool from the team's toolbox.
        """
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        message = Message(
            event_type="team_service",
            destination=team_name,
            actions=[ActionData(tool_name="TeamToolbox", action_name="execute_tool", parameters={
                "tool_name": tool_name,
                "action_name": action_name,
                "parameters": parameters,
                "async_mode": async_mode,
                "tool_use_id": tool_use_id
            })]
        )
        context.message_service.send_message(message)
        if not async_mode:
            observation_message = context.message_service.wait_for_response(
                source=team_name,
                timeout=TIMEOUT
            )
            if observation_message is not None:
                return observation_message.observations[0].data
        return None
    
    def list_tools(self) -> JsonData:
        """
        List all tools in the team's toolbox.
        """
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        message = Message(
            event_type="team_service",
            destination=team_name,
            actions=[ActionData(tool_name="TeamToolbox", action_name="list_tools")]
        )
        context.message_service.send_message(message)
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        return observation_message.observations[0].data