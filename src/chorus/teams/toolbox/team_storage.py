import os
from datetime import datetime
from datetime import timedelta
from typing import Optional

from chorus.data import ExecutableTool
from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.data import Message
from chorus.data.data_types import ActionData
from chorus.helpers import CommunicationHelper

NOT_IN_A_TEAM_ERROR_MESSAGE = "Error: This agent is not part of a team."
TIMEOUT = 10


@ExecutableTool.register("TeamStorageClient")
class TeamStorageClient(SimpleExecutableTool):
    """
    A tool for connecting to the team storage service.
    """

    def __init__(self):
        schema = {
            "tool_name": "TeamStorageClient",
            "name": "TeamStorageClient",
            "description": "A tool for managing files in team storage, allowing listing, reading, writing and deleting files.",
            "actions": [
                {
                    "name": "list_files",
                    "description": "List all files in the team storage",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "prefix": {"type": "string", "description": "Optional prefix to filter files"}
                        },
                        "required": [],
                    }
                },
                {
                    "name": "read_file",
                    "description": "Read the contents of a file from team storage",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to read"}
                        },
                        "required": ["file_path"],
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write content to a file in team storage",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path where the file should be written"},
                            "content": {"type": "string", "description": "Content to write to the file"}
                        },
                        "required": ["file_path", "content"],
                    }
                },
                {
                    "name": "delete_file",
                    "description": "Delete a file from team storage",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the file to delete"}
                        },
                        "required": ["file_path"],
                    }
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))
    
    def list_files(self, prefix: Optional[str] = None):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_storage", action_name="list_files", parameters={"prefix": prefix})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        else:
            return None
    
    def read_file(self, file_path: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_storage", action_name="read_file", parameters={"file_path": file_path})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        else:
            return None
    
    def write_file(self, file_path: str, content: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_storage", action_name="write_file", parameters={"file_path": file_path, "content": content})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        return observation_message is not None
    
    def delete_file(self, file_path: str):
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[ActionData(tool_name="team_storage", action_name="delete_file", parameters={"file_path": file_path})]
            )
        )
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        return observation_message is not None

        

   