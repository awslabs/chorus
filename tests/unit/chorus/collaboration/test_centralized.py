import unittest
from unittest.mock import Mock, patch
from chorus.data.dialog import Message, EventType
from chorus.agents.conversational_task_agent import ConversationalTaskAgent
from chorus.collaboration.centralized import (
    TaskInfo,
    CentralizedCollaboration,
    CURRENT_TASK_KEY,
    TASK_QUEUE_KEY,
)
from chorus.teams.agent_team import Team


class TestCentralizedCollaboration(unittest.TestCase):
    def setUp(self):
        self.coordinator_agent = ConversationalTaskAgent().name("coordinator_agent")
        self.requester_agent = ConversationalTaskAgent().name("requester_agent")
        self.collaboration = CentralizedCollaboration(coordinator=self.coordinator_agent.get_name())
        self.team = Team(
            name="CentralizedTeam",
            agents=[self.coordinator_agent, self.requester_agent],
            collaboration=CentralizedCollaboration(coordinator="coordinator_agent"),
        )
        self.team_context = self.team.init_context()
        self.team_state = self.team.init_state()

    def test_initialization(self):
        assert self.collaboration.get_coordinator() == "coordinator_agent"
        assert self.collaboration.get_name() == "centralized"

    @patch("chorus.collaboration.centralized.CommunicationHelper")
    def test_process_team_service_message(self, mock_CommunicationHelper):
        mock_CommunicationHelper.return_value = Mock()
        mock_CommunicationHelper.return_value.send_raw_message.return_value = Mock()

        # test team service message; should be ignored
        message = Message(
            event_type=EventType.TEAM_SERVICE,
        )
        self.collaboration.process_message(self.team_context, self.team_state, message)
        assert mock_CommunicationHelper.return_value.send_raw_message.call_count == 0
        assert self.team_state.get_collaboration_data_store() == {}

        # test requester agent demanding task 1
        message = Message(
            event_type=EventType.MESSAGE,
            source="requester_agent",
            destination="coordinator_agent",
            content="task 1",
        )
        self.collaboration.process_message(self.team_context, self.team_state, message)
        assert mock_CommunicationHelper.return_value.send_raw_message.call_count == 1
        assert self.team_state.get_collaboration_data_store()[CURRENT_TASK_KEY] == TaskInfo(
            content=message.content, requester="requester_agent"
        )

        # test requester agent demanding task 2
        message = Message(
            event_type=EventType.MESSAGE,
            source="requester_agent",
            destination="coordinator_agent",
            content="task 2",
        )
        self.collaboration.process_message(self.team_context, self.team_state, message)
        assert mock_CommunicationHelper.return_value.send_raw_message.call_count == 2
        assert self.team_state.get_collaboration_data_store()[TASK_QUEUE_KEY] == [
            TaskInfo(content=message.content, requester="requester_agent")
        ]

        # test coordinator process both tasks
        message = Message(
            event_type=EventType.MESSAGE,
            source="coordinator_agent",
            destination="requester_agent",
            content="done!",
        )
        self.collaboration.process_message(self.team_context, self.team_state, message)
        assert mock_CommunicationHelper.return_value.send_raw_message.call_count == 4
