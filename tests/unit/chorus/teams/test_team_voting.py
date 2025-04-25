import unittest
from unittest.mock import patch

from chorus.data import EventType
from chorus.agents.conversational_task_agent import ConversationalTaskAgent
from chorus.collaboration.centralized import CentralizedCollaboration
from chorus.teams.agent_team import Team
from chorus.teams.services.team_voting import TeamVoting
from chorus.teams.toolbox.team_voting import TeamVotingClient
from chorus.data.collaboration_strategies import DecisionMakingStrategy
from tests.testing_util import MockMessageClient
from chorus.data.data_types import ActionData


class TestTeamVoting(unittest.TestCase):
    def setUp(self):
        self.team_voting_tool_1 = TeamVotingClient("voter_1")
        self.team_voting_tool_2 = TeamVotingClient("voter_2")
        self.team_voting_tool_3 = TeamVotingClient("voter_3")
        self.team_voting_service = TeamVoting()
        self.voter_1 = ConversationalTaskAgent(tools=[self.team_voting_tool_1])
        self.voter_2 = ConversationalTaskAgent(tools=[self.team_voting_tool_2])
        self.voter_3 = ConversationalTaskAgent(tools=[self.team_voting_tool_3])
        self.team = Team(
            name="VotingTeam",
            agents=[
                self.voter_1,
                self.voter_2,
                self.voter_3,
            ],
            collaboration=CentralizedCollaboration(
                coordinator=self.voter_1.get_name()
            ),
            services=[
                self.team_voting_service
            ],
        )
        self.team_context = self.team.init_context()
        self.team_state = self.team.init_state()
        self.team_voting_tool_1.set_context(self.team_context)
        self.team_voting_tool_1._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_voting_tool_2.set_context(self.team_context)
        self.team_voting_tool_2._agent_context.message_client = MockMessageClient("VotingTeam")
        self.team_voting_tool_3.set_context(self.team_context)
        self.team_voting_tool_3._agent_context.message_client = MockMessageClient("VotingTeam")

    def test_majority_vote(self):
        """Test majority vote -- proposal needs more than 50% of votes"""
        self.team_voting_service.decision_making_strategy = DecisionMakingStrategy.MAJORITY_VOTE
        self.team_voting_service.initialize_service(self.team_state)
        
        with patch.object(self.team_voting_tool_1._agent_context.message_client, "send_message") as mock_send_message, \
            patch.object(self.team_voting_tool_1._agent_context.message_client, "wait_for_response") as mock_wait_for_response:
            # client propose
            print("=== client propose ===")
            self.team_voting_tool_1.propose("Let's vote")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="propose",
                    parameters={"proposal_content": "Let's vote", "reasoning": ""}
                )
            ]

            # service create proposal
            print("=== service create proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal_id'] == "proposal_0"
            assert message.observations[0].data['proposal']['id'] == "proposal_0"
            assert message.observations[0].data['proposal']['content'] == "Let's vote"

            # client list active proposals
            print("=== client list active proposals ===")
            self.team_voting_tool_1.list_active_proposals()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="list_active_proposals",
                )
            ]

            # service list active proposals
            print("=== service list active proposals ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "proposal_0" in message.observations[0].data['active_proposals']
            assert message.observations[0].data['active_proposals']["proposal_0"]['id'] == "proposal_0"
            assert message.observations[0].data['active_proposals']["proposal_0"]['content'] == "Let's vote"

            # client get one proposal
            print("=== client get one proposal ===")
            self.team_voting_tool_1.get_proposal("proposal_0")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="get_proposal",
                    parameters={"proposal_id": "proposal_0"}
                )
            ]

            # service get one proposal
            print("=== service get one proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal']['id'] == "proposal_0"
            assert message.observations[0].data['proposal']['content'] == "Let's vote"

            # client vote
            print("=== client vote ===")
            self.team_voting_tool_1.vote("proposal_0")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="vote",
                    parameters={"proposal_id": "proposal_0"}
                )
            ]
            
            # service cast vote
            print("=== service cast vote ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['current_results'] == {'has_majority': False, 'total_votes': 3, 'votes_in_favor': 1}

            # service get decision -- inconclusive
            print("=== service get decision -- inconclusive ===")
            decision = self.team_voting_service.get_decision(self.team_state)
            assert decision == None

            # (another) client vote
            print("=== (another) client vote ===")
            self.team_voting_tool_2.vote("proposal_0")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="vote",
                    parameters={"proposal_id": "proposal_0"}
                )
            ]

            # service cast vote
            print("=== service cast vote ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['current_results'] == {'has_majority': True, 'total_votes': 3, 'votes_in_favor': 2}

            # service get decision -- majority wins
            print("=== service get decision -- majority wins ===")
            decision = self.team_voting_service.get_decision(self.team_state)
            assert decision == "Let's vote"

    
    def test_first_come_first_serve_vote(self):
        """Test first-come-first-serve vote -- first proposal is automatically selected"""
        self.team_voting_service.decision_making_strategy = DecisionMakingStrategy.FIRST_COME_FIRST_SERVE
        self.team_voting_service.initialize_service(self.team_state)
        
        with patch.object(self.team_voting_tool_1._agent_context.message_client, "send_message") as mock_send_message, \
            patch.object(self.team_voting_tool_1._agent_context.message_client, "wait_for_response") as mock_wait_for_response:
            # client propose
            print("=== client propose ===")
            self.team_voting_tool_1.propose("Let's vote", "Here's why")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="propose",
                    parameters={"proposal_content": "Let's vote", "reasoning": "Here's why"}
                )
            ]

            # service create proposal
            print("=== service create proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal_id'] == "proposal_0"
            assert message.observations[0].data['proposal']['id'] == "proposal_0"
            assert message.observations[0].data['proposal']['content'] == "Let's vote"
            assert message.observations[0].data['proposal']['reasoning'] == "Here's why"

            # client list active proposals
            print("=== client list active proposals ===")
            self.team_voting_tool_1.list_active_proposals()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="list_active_proposals",
                )
            ]

            # service list active proposals
            print("=== service list active proposals ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "proposal_0" in message.observations[0].data['active_proposals']
            assert message.observations[0].data['active_proposals']["proposal_0"]['id'] == "proposal_0"
            assert message.observations[0].data['active_proposals']["proposal_0"]['content'] == "Let's vote"
            assert message.observations[0].data['active_proposals']["proposal_0"]['reasoning'] == "Here's why"

            # client get one proposal
            print("=== client get one proposal ===")
            self.team_voting_tool_1.get_proposal("proposal_0")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="get_proposal",
                    parameters={"proposal_id": "proposal_0"}
                )
            ]

            # service get one proposal
            print("=== service get one proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal']['id'] == "proposal_0"
            assert message.observations[0].data['proposal']['content'] == "Let's vote"
            assert message.observations[0].data['proposal']['reasoning'] == "Here's why"

            # service get decision
            print("=== service get decision ===")
            decision = self.team_voting_service.get_decision(self.team_state)
            assert decision == "Let's vote"

            # client vote
            print("=== client vote ===")
            self.team_voting_tool_2.vote("proposal_0")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="vote",
                    parameters={"proposal_id": "proposal_0"}
                )
            ]

            # service cast vote (not allowed in first-come-first-serve strategy)
            print("=== service cast vote (not allowed in first-come-first-serve strategy) ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert 'current_results' not in message.observations[0].data
            assert 'error' in message.observations[0].data

    def test_plurality_vote(self):
        """Test plurality vote -- proposal with most votes wins"""
        self.team_voting_service.decision_making_strategy = DecisionMakingStrategy.PLURALITY_VOTE
        self.team_voting_service.initialize_service(self.team_state)
        
        with patch.object(self.team_voting_tool_1._agent_context.message_client, "send_message") as mock_send_message, \
            patch.object(self.team_voting_tool_1._agent_context.message_client, "wait_for_response") as mock_wait_for_response:
            # client propose
            print("=== client propose ===")
            self.team_voting_tool_1.propose("Let's vote", "Here's why")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="propose",
                    parameters={"proposal_content": "Let's vote", "reasoning": "Here's why"}
                )
            ]

            # service create proposal
            print("=== service create proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal_id'] == "proposal_0"
            assert message.observations[0].data['proposal']['id'] == "proposal_0"
            assert message.observations[0].data['proposal']['content'] == "Let's vote"
            assert message.observations[0].data['proposal']['reasoning'] == "Here's why"

            # another client propose
            print("=== another client propose ===")
            self.team_voting_tool_2.propose("Let's not vote", "For no reason")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="propose",
                    parameters={"proposal_content": "Let's not vote", "reasoning": "For no reason"}
                )
            ]

            # service create proposal
            print("=== service create proposal ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['proposal_id'] == "proposal_1"
            assert message.observations[0].data['proposal']['id'] == "proposal_1"
            assert message.observations[0].data['proposal']['content'] == "Let's not vote"
            assert message.observations[0].data['proposal']['reasoning'] == "For no reason"

            # client list active proposals
            print("=== client list active proposals ===")
            self.team_voting_tool_1.list_active_proposals()
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="list_active_proposals",
                )
            ]

            # service list active proposals
            print("=== service list active proposals ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert "proposal_0" in message.observations[0].data['active_proposals']
            assert message.observations[0].data['active_proposals']["proposal_0"]['id'] == "proposal_0"
            assert message.observations[0].data['active_proposals']["proposal_0"]['content'] == "Let's vote"
            assert message.observations[0].data['active_proposals']["proposal_0"]['reasoning'] == "Here's why"
            assert "proposal_1" in message.observations[0].data['active_proposals']
            assert message.observations[0].data['active_proposals']["proposal_1"]['id'] == "proposal_1"
            assert message.observations[0].data['active_proposals']["proposal_1"]['content'] == "Let's not vote"
            assert message.observations[0].data['active_proposals']["proposal_1"]['reasoning'] == "For no reason"

            # service get decision -- inconclusive
            print("=== service get decision -- inconclusive ===")
            decision = self.team_voting_service.get_decision(self.team_state)
            assert decision == None

            # another client vote
            print("=== another client vote ===")
            self.team_voting_tool_3.vote("proposal_1")
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.destination == "VotingTeam"
            assert message.event_type == EventType.TEAM_SERVICE
            assert message.actions == [
                ActionData(
                    tool_name="team_voting",
                    action_name="vote",
                    parameters={"proposal_id": "proposal_1"}
                )
            ]

            # service cast vote
            print("=== service cast vote ===")
            self.team_voting_service.process_message(self.team_context, self.team_state, message)
            message = mock_send_message.call_args[0][0]
            print(message)
            assert message.observations[0].data['current_results'] == {'is_leading': True, 'total_votes': 3, 'votes_in_favor': 2}

            # service get decision
            print("=== service get decision ===")
            decision = self.team_voting_service.get_decision(self.team_state)
            assert decision == "Let's not vote"