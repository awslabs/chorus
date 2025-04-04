from typing import List
from chorus.data.dialog import Message
from chorus.data.data_types import ObservationData
from chorus.data.executable_tool import ExecutableTool
from chorus.data.state import TeamState
from chorus.data.context import TeamContext
from chorus.teams.services.base import TeamService

TOOL_NAME_NOT_SPECIFIED_ERROR_MESSAGE = "Error: Tool name not specified in the action input."
TOOL_NAME_NOT_FOUND_ERROR_MESSAGE = "Error: Tool name not found in the toolbox."

@TeamService.register("TeamToolbox")
class TeamToolbox(TeamService):

    def __init__(self, tools: List[ExecutableTool]):
        self._tools = tools
        self._tool_map = {tool.get_schema().name: tool for tool in tools}
        super().__init__("team_toolbox")

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        if inbound_message.event_type != "team_service":
            return
        observations = []
        if inbound_message.actions is None:
            return
        for action in inbound_message.actions:
            if action.tool_name == "team_toolbox":
                if action.action_name == "execute_tool":
                    action_input = action.parameters if action.parameters is not None else {}
                    tool_name = action_input.get("tool_name", None)
                    action_name = action_input.get("action_name", None)
                    action_parameters = action_input.get("parameters", None)
                    tool_use_id = action_input.get("tool_use_id", None)
                    if tool_name is None:
                        return TOOL_NAME_NOT_SPECIFIED_ERROR_MESSAGE
                    if tool_name not in self._tool_map:
                        return TOOL_NAME_NOT_FOUND_ERROR_MESSAGE
                    tool = self._tool_map[tool_name]
                    try:
                        observation_data = tool.execute(action_name, action_parameters)
                    except Exception as e:
                        observation_data = f"Error: {str(e)}"
                    observations.append(ObservationData(data=observation_data, tool_use_id=tool_use_id, async_execution_id=action.async_execution_id))
                if action.action_name == "list_tools":
                    tool_schema_list = [tool.get_schema().model_dump(exclude_none=True, exclude_defaults=True) for tool in self._tools]
                    observations.append(ObservationData(data=tool_schema_list))
        if not observations:
            return
        outbound_event = Message(
            destination=inbound_message.source,
            observations=observations
        )
        team_context.message_client.send_message(outbound_event)
                    


