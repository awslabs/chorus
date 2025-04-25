import unittest
from unittest.mock import patch

from chorus.agents.conversational_task_agent import ConversationalTaskAgent
from chorus.collaboration.centralized import CentralizedCollaboration
from chorus.teams.agent_team import Team
from chorus.teams.services.team_scratchpad import TeamScratchpad
from chorus.teams.toolbox.team_scratchpad import TeamScratchpadClient
from tests.testing_util import MockMessageClient
from chorus.data.data_types import ActionData


class TestTeamScratchpad(unittest.TestCase):
    def setUp(self):
        self.team_scratching_tool_1 = TeamScratchpadClient()
        self.team_scratching_tool_2 = TeamScratchpadClient()
        self.team_scratching_tool_3 = TeamScratchpadClient()
        self.team_scratching_service = TeamScratchpad()
        self.scratcher_1 = ConversationalTaskAgent(tools=[self.team_scratching_tool_1])
        self.scratcher_2 = ConversationalTaskAgent(tools=[self.team_scratching_tool_2])
        self.scratcher_3 = ConversationalTaskAgent(tools=[self.team_scratching_tool_3])
        self.team = Team(
            name="ScratchingTeam",
            agents=[
                self.scratcher_1,
                self.scratcher_2,
                self.scratcher_3,
            ],
            collaboration=CentralizedCollaboration(
                coordinator=self.scratcher_1.get_name()
            ),
            services=[
                self.team_scratching_service
            ],
        )
        self.team_context = self.team.init_context()
        self.team_state = self.team.init_state()
        self.team_scratching_tool_1.set_context(self.team_context)
        self.team_scratching_tool_1._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_scratching_tool_2.set_context(self.team_context)
        self.team_scratching_tool_2._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_scratching_tool_3.set_context(self.team_context)
        self.team_scratching_tool_3._agent_context.message_client = MockMessageClient("VotingTeam")

    def test_scratch(self):
        with patch.object(self.team_scratching_tool_1._agent_context.message_client, "send_message") as mock_send_message, \
            patch.object(self.team_scratching_tool_1._agent_context.message_client, "wait_for_response") as mock_wait_for_response:
            # client create scratchpad
            print("=== client create scratchpad ===")
            self.team_scratching_tool_1.create_scratchpad("hello world")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "ScratchingTeam"

            # service create scratchpad
            print("=== service create scratchpad ===")
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == "Created scratchpad hello world"

            # client get scratchpad
            print("=== client get scratchpad ===")
            self.team_scratching_tool_2.get_scratchpad("hello world")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "ScratchingTeam"
            assert message.actions == [ActionData(tool_name='team_scratchpad', action_name='get_scratchpad', parameters={'scratchpad_id': 'hello world'}, tool_use_id=None, async_execution_id=None)]

            # service get scratchpad
            print("=== service get scratchpad ===")
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == {'lines': []}

            # client edit lines
            print("=== client edit lines ===")
            self.team_scratching_tool_3.edit_lines("hello world", 0, 0, "foo")
            message = mock_send_message.call_args[0][0]
            print(message)

            # service edit lines
            print("=== service edit lines ===")
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == {'message': 'Updated lines 0 to 0', 'lines': ['L0: foo']}

            # another client edit lines
            print("=== another client edit lines ===")
            self.team_scratching_tool_3.edit_lines("hello world", 1, 1, "bar")
            message = mock_send_message.call_args[0][0]
            print(message)

            # service edit lines
            print("=== service edit lines ===")
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == {'message': 'Updated lines 1 to 1', 'lines': ['L0: foo', 'L1: bar']}

            # client attempt invalid edits
            print("=== client attempt invalid edits -- negative indices ===")
            self.team_scratching_tool_1.edit_lines("hello world", -1, 0, "baz")
            message = mock_send_message.call_args[0][0]
            print(message)
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "error" in message.observations[0].data

            print("=== client attempt invalid edits -- end line smaller than start line ===")
            self.team_scratching_tool_1.edit_lines("hello world", 1, 0, "baz")
            message = mock_send_message.call_args[0][0]
            print(message)
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "error" in message.observations[0].data

            print("=== client attempt invalid edits -- start line out of range ===")
            self.team_scratching_tool_1.edit_lines("hello world", 3, 3, "baz")
            message = mock_send_message.call_args[0][0]
            print(message)
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "error" in message.observations[0].data

            print("=== client attempt invalid edits -- content line count mismatch ===")
            self.team_scratching_tool_1.edit_lines("hello world", 0, 1, "baz")
            message = mock_send_message.call_args[0][0]
            print(message)
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "error" in message.observations[0].data

            # delete scratchpad
            print("=== delete scratchpad ===")
            self.team_scratching_tool_1.delete_scratchpad("hello world")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "ScratchingTeam"
            assert message.actions == [ActionData(tool_name='team_scratchpad', action_name='delete_scratchpad', parameters={'scratchpad_id': 'hello world'}, tool_use_id=None, async_execution_id=None)]
            self.team_scratching_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data == 'Deleted scratchpad hello world'
