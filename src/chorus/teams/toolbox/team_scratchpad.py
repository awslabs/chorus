from typing import List, Optional
from datetime import datetime
from datetime import timedelta

from chorus.data import ExecutableTool
from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.data import Message
from chorus.data.data_types import ActionData
from chorus.helpers import CommunicationHelper

NOT_IN_A_TEAM_ERROR_MESSAGE = "Error: This agent is not part of a team."
TIMEOUT = 10

@ExecutableTool.register("TeamScratchpadClient")
class TeamScratchpadClient(SimpleExecutableTool):
    """
    A tool for interacting with the team scratchpad service, allowing collaborative document editing.
    """

    def __init__(self):
        schema = {
            "tool_name": "TeamScratchpadClient",
            "name": "TeamScratchpadClient",
            "description": "A tool for collaborative document editing in team scratchpads, with line-by-line tracking of modifications.",
            "actions": [
                {
                    "name": "create_scratchpad",
                    "description": "Create a new team scratchpad",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "scratchpad_id": {"type": "string", "description": "Unique identifier for the scratchpad"}
                        },
                        "required": ["scratchpad_id"],
                    }
                },
                {
                    "name": "get_scratchpad",
                    "description": "Get the current content of a scratchpad with line modification history",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "scratchpad_id": {"type": "string", "description": "ID of the scratchpad to retrieve"}
                        },
                        "required": ["scratchpad_id"],
                    }
                },
                {
                    "name": "edit_lines",
                    "description": "Edit specific lines in a scratchpad. The new_content string will replace the lines from start_line_number to end_line_number (inclusive).",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "scratchpad_id": {"type": "string", "description": "ID of the scratchpad to edit"},
                            "start_line_number": {"type": "integer", "description": "Starting line number (0-based)"},
                            "end_line_number": {"type": "integer", "description": "Ending line number (0-based, inclusive)"},
                            "new_content": {"type": "string", "description": "New content to replace the specified lines"},
                        },
                        "required": ["scratchpad_id", "start_line_number", "end_line_number", "new_content"],
                    }
                },
                {
                    "name": "delete_scratchpad",
                    "description": "Delete a team scratchpad",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "scratchpad_id": {"type": "string", "description": "ID of the scratchpad to delete"}
                        },
                        "required": ["scratchpad_id"],
                    }
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))
    
    def create_scratchpad(self, scratchpad_id: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_scratchpad", action_name="create_scratchpad", parameters={"scratchpad_id": scratchpad_id})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None
    
    def get_scratchpad(self, scratchpad_id: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_scratchpad", action_name="get_scratchpad", parameters={"scratchpad_id": scratchpad_id})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None
    
    def edit_lines(self, scratchpad_id: str, start_line_number: int, end_line_number: int, new_content: str):
        """
        Edit lines in a scratchpad from start_line_number to end_line_number (inclusive) with new_content.
        The content will be split into lines by the service to replace the specified range.
        """
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        agent_name = context.agent_id
        
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(
                    tool_name="team_scratchpad",
                    action_name="edit_lines",
                    parameters={
                        "scratchpad_id": scratchpad_id,
                        "start_line_number": start_line_number,
                        "end_line_number": end_line_number,
                        "new_content": new_content,
                        "editor": agent_name
                    }
                )]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None
    
    def delete_scratchpad(self, scratchpad_id: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_scratchpad", action_name="delete_scratchpad", input={"scratchpad_id": scratchpad_id})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None
