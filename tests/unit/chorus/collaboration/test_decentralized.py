import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from chorus.data.dialog import Message, EventType
from chorus.agents.conversational_task_agent import ConversationalTaskAgent
from chorus.collaboration.decentralized import DecentralizedCollaboration, TaskInfo
from chorus.teams.agent_team import Team
from chorus.teams.services.team_voting import TeamVoting


class TestDecentralizedCollaboration(unittest.TestCase):
    def setUp(self):
        self.initiative_taker = ConversationalTaskAgent().name("initiative_taker")
        self.requester_agent = ConversationalTaskAgent().name("requester_agent")
        self.voter_agent = ConversationalTaskAgent().name("voter_agent")

        self.collaboration = DecentralizedCollaboration(
            initiative_takers=["initiative_taker"], time_limit=60
        )

        self.voting_service = TeamVoting()
        self.team = Team(
            name="DecentralizedTeam",
            agents=[self.initiative_taker, self.requester_agent, self.voter_agent],
            collaboration=self.collaboration,
            services=[self.voting_service],
        )
        self.team_context = self.team.init_context()
        self.team_state = self.team.init_state()

        # Register team info and services
        self.collaboration.register_team(self.team._team_info, [self.voting_service])

    def test_initialization(self):
        assert self.collaboration.initiative_takers == ["initiative_taker"]
        assert self.collaboration.time_limit == 60
        assert self.collaboration.get_name() == "decentralized"

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_process_team_service_message(self, mock_CommunicationHelper):
        mock_CommunicationHelper.return_value = Mock()

        # Test team service message; should be ignored
        message = Message(event_type=EventType.TEAM_SERVICE)
        self.collaboration.process_message(self.team_context, self.team_state, message)
        assert mock_CommunicationHelper.return_value.send.call_count == 0

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_process_message_without_voting_service(self, mock_CommunicationHelper):
        mock_helper = Mock()
        mock_CommunicationHelper.return_value = mock_helper

        # Remove voting service
        self.collaboration._voting_service = None

        message = Message(
            event_type=EventType.MESSAGE, source="requester_agent", content="test task"
        )

        self.collaboration.process_message(self.team_context, self.team_state, message)
        mock_helper.send.assert_called_once_with(
            "requester_agent", "Error: Team voting service is not configured"
        )

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_process_new_task(self, mock_CommunicationHelper):
        mock_helper = Mock()
        mock_CommunicationHelper.return_value = mock_helper

        message = Message(
            event_type=EventType.MESSAGE,
            source="requester_agent",
            content="test task",
            message_id="task1",
        )

        self.collaboration.process_message(self.team_context, self.team_state, message)

        # Verify task was started
        data_store = self.team_state.get_collaboration_data_store()
        assert data_store["current_task_id"] == "task1"
        assert data_store["current_requester"] == "requester_agent"

        # Verify message was sent to initiative taker
        mock_helper.send.assert_called_with(
            "initiative_taker", "test task", source="requester_agent"
        )

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_process_queued_task(self, mock_CommunicationHelper):
        mock_helper = Mock()
        mock_CommunicationHelper.return_value = mock_helper

        # Set up existing task
        data_store = self.team_state.get_collaboration_data_store()
        data_store.update(
            {
                "current_task_id": "task1",
                "current_requester": "requester_agent",
                "task_start_time": datetime.now().isoformat(),
                "task_queue": [],
            }
        )

        # Send new task
        message = Message(
            event_type=EventType.MESSAGE,
            source="voter_agent",
            content="queued task",
            message_id="task2",
        )

        self.collaboration.process_message(self.team_context, self.team_state, message)

        # Verify task was queued
        assert len(data_store["task_queue"]) == 1
        queued_task = TaskInfo.from_dict(data_store["task_queue"][0])
        assert queued_task.task_id == "task2"

        # Verify queue position message
        mock_helper.send.assert_called_with(
            "voter_agent",
            "Your task has been queued. Current queue position: 1",
            source="team:DecentralizedTeam",
        )

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_iterate_time_limit_exceeded(self, mock_CommunicationHelper):
        mock_helper = Mock()
        mock_CommunicationHelper.return_value = mock_helper

        # Set up task that exceeds time limit
        data_store = self.team_state.get_collaboration_data_store()
        data_store.update(
            {
                "current_task_id": "task1",
                "current_requester": "requester_agent",
                "task_start_time": (datetime.now() - timedelta(seconds=61)).isoformat(),
                "last_check_time": (datetime.now() - timedelta(seconds=4)).isoformat(),
            }
        )

        self.collaboration.iterate(self.team_context, self.team_state)

        # Verify timeout messages
        mock_helper.send.assert_any_call(
            "requester_agent",
            "No decision was reached within the time limit.",
            source="team:DecentralizedTeam",
        )

        # Verify task was cleared
        assert data_store["current_task_id"] is None

    @patch("chorus.collaboration.decentralized.CommunicationHelper")
    def test_majority_decision_reached(self, mock_CommunicationHelper):
        mock_helper = Mock()
        mock_CommunicationHelper.return_value = mock_helper

        # Set up current task
        data_store = self.team_state.get_collaboration_data_store()
        data_store.update(
            {
                "current_task_id": "task1",
                "current_requester": "requester_agent",
                "task_start_time": datetime.now().isoformat(),
                "last_check_time": (datetime.now() - timedelta(seconds=4)).isoformat(),
            }
        )

        # Mock voting service to return a decision
        self.voting_service.get_decision = Mock(return_value="Agreed solution")

        self.collaboration.iterate(self.team_context, self.team_state)

        # Verify decision was sent
        mock_helper.send.assert_any_call(
            "requester_agent", "Agreed solution", source="team:DecentralizedTeam"
        )

        # Verify collaboration end notification
        mock_helper.send.assert_any_call(
            "initiative_taker",
            "Collaboration ended: Majority decision reached\nWinning proposal: Agreed solution",
            source="team:DecentralizedTeam",
        )

        # Verify task was cleared
        assert data_store["current_task_id"] is None
