import os
import unittest
from unittest.mock import patch

from chorus.agents.conversational_task_agent import ConversationalTaskAgent
from chorus.collaboration.centralized import CentralizedCollaboration
from chorus.teams.agent_team import Team
from chorus.teams.services.team_storage import TeamStorage
from chorus.teams.toolbox.team_storage import TeamStorageClient
from tests.testing_util import MockMessageClient
from chorus.data.data_types import ActionData


class TestTeamStorage(unittest.TestCase):
    def setUp(self):
        self.team_storage_tool_1 = TeamStorageClient()
        self.team_storage_tool_2 = TeamStorageClient()
        self.team_storage_tool_3 = TeamStorageClient()
        self.team_storage_service = TeamStorage()
        self.scratcher_1 = ConversationalTaskAgent(tools=[self.team_storage_tool_1])
        self.scratcher_2 = ConversationalTaskAgent(tools=[self.team_storage_tool_2])
        self.scratcher_3 = ConversationalTaskAgent(tools=[self.team_storage_tool_3])
        self.team = Team(
            name="StorageTeam",
            agents=[
                self.scratcher_1,
                self.scratcher_2,
                self.scratcher_3,
            ],
            collaboration=CentralizedCollaboration(
                coordinator=self.scratcher_1.get_name()
            ),
            services=[
                self.team_storage_service
            ],
        )
        self.team_context = self.team.init_context()
        self.team_state = self.team.init_state()
        self.team_storage_tool_1.set_context(self.team_context)
        self.team_storage_tool_1._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_storage_tool_2.set_context(self.team_context)
        self.team_storage_tool_2._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_storage_tool_3.set_context(self.team_context)
        self.team_storage_tool_3._agent_context.message_client = MockMessageClient("VotingTeam")

    def test_storage(self):
        with patch.object(self.team_storage_tool_1._agent_context.message_client, "send_message") as mock_send_message, \
            patch.object(self.team_storage_tool_1._agent_context.message_client, "wait_for_response") as mock_wait_for_response:
            # client list storage
            print("=== client list storage ===")
            self.team_storage_tool_1.list_files()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "StorageTeam"
            assert message.actions == [ActionData(tool_name='team_storage', action_name='list_files', parameters={'prefix': None}, tool_use_id=None, async_execution_id=None)]

            # service list storage (empty)
            print("=== service list storage (empty) ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == []

            # client write file
            print("=== client write file ===")
            self.team_storage_tool_2.write_file(file_path="foo.bar", content="hello world")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "StorageTeam"
            assert message.actions == [ActionData(tool_name='team_storage', action_name='write_file', parameters={'file_path': 'foo.bar', 'content': 'hello world'}, tool_use_id=None, async_execution_id=None)]

            # service write file
            print("=== service write file ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == 'Wrote file foo.bar'

            # another client list storage
            print("=== another client list storage ===")
            self.team_storage_tool_3.list_files()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "StorageTeam"
            assert message.actions == [ActionData(tool_name='team_storage', action_name='list_files', parameters={'prefix': None}, tool_use_id=None, async_execution_id=None)]

            # service list storage (non-empty)
            print("=== service list storage (non-empty) ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert len(message.observations[0].data) == 1
            assert message.observations[0].data[0].endswith("foo.bar")
            assert os.path.isfile(message.observations[0].data[0])
            assert open(message.observations[0].data[0]).read() == "hello world"

            # client read file
            print("=== client read file ===")
            self.team_storage_tool_1.read_file(file_path="foo.bar")
            message = mock_send_message.call_args[0][0]
            print(message)

            # service read file
            print("=== service read file ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == 'hello world'

            # client delete file
            print("=== client delete file ===")
            self.team_storage_tool_2.delete_file(file_path="foo.bar")
            message = mock_send_message.call_args[0][0]
            print(message)

            # service delete file
            print("=== service delete file ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == 'Deleted file foo.bar'

            # client attempt invalid read
            print("=== client attempt invalid read ===")
            self.team_storage_tool_3.read_file(file_path="foo.bar")
            message = mock_send_message.call_args[0][0]
            print(message)
            with self.assertRaises(FileNotFoundError):
                self.team_storage_service.process_message(self.team_context, self.team_state, message)

            # client list storage
            print("=== client list storage ===")
            self.team_storage_tool_1.list_files()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "StorageTeam"
            assert message.actions == [ActionData(tool_name='team_storage', action_name='list_files', parameters={'prefix': None}, tool_use_id=None, async_execution_id=None)]

            # service list storage (empty)
            print("=== service list storage (empty) ===")
            self.team_storage_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == []