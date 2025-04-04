from typing import List, Optional

from chorus.data.state import TeamState
from chorus.data.data_types import ObservationData
from chorus.data.dialog import Message
from chorus.data.context import TeamContext
from chorus.teams.services.base import TeamService
import tempfile
import glob
import os

@TeamService.register("TeamStorage")
class TeamStorage(TeamService):

    def __init__(self):
        super().__init__("team_storage")

    def initialize_service(self, team_state: TeamState):
        # Create a temporary folder
        data_store = team_state.get_service_data_store(self.get_name())
        data_store["temp_folder"] = tempfile.TemporaryDirectory().name

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        if inbound_message.event_type != "team_service":
            return
        data_store = team_state.get_service_data_store(self.get_name())
        observations = []
        if inbound_message.actions is None:
            return
        for action in inbound_message.actions:
            if action.tool_name == self.get_name():
                if action.action_name == "list_files":
                    observations.append(
                        ObservationData(
                            data=self.list_files(data_store["temp_folder"], action.parameters.get("prefix", None))
                        )
                    )
                elif action.action_name == "read_file":
                    observations.append(
                        ObservationData(
                            data=self.read_file(data_store["temp_folder"], action.parameters.get("file_path", None))
                        )
                    )
                elif action.action_name == "write_file":
                    self.write_file(
                        data_store["temp_folder"],
                        action.parameters.get("file_path", None),
                            action.parameters.get("content", None)
                    )
                    observations.append(
                        ObservationData(
                            data=f"Wrote file {action.parameters.get('file_path', None)}"
                        )
                    )
                elif action.action_name == "delete_file":
                    self.delete_file(
                        data_store["temp_folder"],
                        action.parameters.get("file_path", None)
                    )
                    observations.append(
                        ObservationData(
                            data=f"Deleted file {action.parameters.get('file_path', None)}"
                        )
                    )
        if not observations:
            return
        outbound_event = Message(
            destination=inbound_message.source,
            observations=observations
        )
        team_context.message_client.send_message(outbound_event)


    def list_files(self, temp_folder: str, prefix: Optional[str] = None) -> List:
        """
        List all files in the team storage, return a list of file paths.
        """
        if prefix is None:
            return glob.glob(f"{temp_folder}/*")
        else:
            return glob.glob(f"{temp_folder}/{prefix}*")

    def read_file(self, temp_folder: str, file_path: str) -> str:
        """
        Read the contents of a file in the team storage.
        """
        temp_path = os.path.join(temp_folder, file_path)
        with open(temp_path, "r") as f:
            return f.read()

    def write_file(self, temp_folder: str, file_path: str, content: str):
        """
        Write the contents of a file in the team storage.
        """
        # Create the parent directory if it doesn't exist
        temp_path = os.path.join(temp_folder, file_path)
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "w") as f:
            f.write(content)

    def delete_file(self, temp_folder: str, file_path: str):
        """
        Delete a file from the team storage.
        """
        temp_path = os.path.join(temp_folder, file_path)
        os.remove(temp_path)


