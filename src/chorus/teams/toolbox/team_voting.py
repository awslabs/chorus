from typing import Dict, Optional

from chorus.data import ExecutableTool
from chorus.data import SimpleExecutableTool
from chorus.data import ToolSchema
from chorus.data import Message
from chorus.data.data_types import ActionData

NOT_IN_A_TEAM_ERROR_MESSAGE = "Error: This agent is not part of a team."
TIMEOUT = 10

@ExecutableTool.register("TeamVotingClient")
class TeamVotingClient(SimpleExecutableTool):
    """A tool for participating in team voting, allowing agents to create proposals and vote on them."""

    def __init__(self):
        schema = {
            "tool_name": "TeamVotingClient",
            "name": "TeamVotingClient",
            "description": "A tool for participating in team voting, allowing creation of proposals and majority voting.",
            "actions": [
                {
                    "name": "propose",
                    "description": "Create a new proposal for the team to vote on. Requires a proposal content.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "proposal_content": {"type": "string", "description": "The content of the proposal"},
                            "reasoning": {"type": "string", "description": "The reasoning behind the proposal"}
                        },
                        "required": ["proposal_content"],
                    }
                },
                {
                    "name": "vote",
                    "description": "Cast a vote in favor of a proposal (majority voting). Requires a proposal ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "proposal_id": {"type": "string", "description": "ID of the proposal to vote on"}
                        },
                        "required": ["proposal_id"],
                    }
                },
                {
                    "name": "get_proposal",
                    "description": "Get details of a specific proposal including current votes. Requires a proposal ID.",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "proposal_id": {"type": "string", "description": "ID of the proposal to get details for"}
                        },
                        "required": ["proposal_id"],
                    }
                },
                {
                    "name": "list_active_proposals",
                    "description": "List all currently active proposals. No input required.",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                }
            ],
        }
        super().__init__(ToolSchema.model_validate(schema))

    def propose(self, proposal_content: str, reasoning: Optional[str] = "") -> Dict:
        """Create a new proposal for the team to vote on."""
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[
                    ActionData(
                        tool_name="team_voting",
                        action_name="propose",
                        parameters={"proposal_content": proposal_content, "reasoning": reasoning}
                    )
                ]
            )
        )
        
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None

    def vote(self, proposal_id: str) -> Dict:
        """Cast a vote in favor of a proposal."""
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[
                    ActionData(
                        tool_name="team_voting",
                        action_name="vote",
                        parameters={"proposal_id": proposal_id}
                    )
                ]
            )
        )
        
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None

    def get_proposal(self, proposal_id: str) -> Dict:
        """Get details of a specific proposal including current votes."""
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[
                    ActionData(
                        tool_name="team_voting",
                        action_name="get_proposal",
                        parameters={"proposal_id": proposal_id}
                    )
                ]
            )
        )
        
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None

    def list_active_proposals(self) -> Dict:
        """List all currently active proposals."""
        context = self.get_context()
        if context.team_info is None:
            return NOT_IN_A_TEAM_ERROR_MESSAGE
        
        team_name = context.team_info.get_identifier()
        context.message_service.send_message(
            Message(
                event_type="team_service",
                destination=team_name,
                actions=[
                    ActionData(
                        tool_name="team_voting",
                        action_name="list_active_proposals",
                        parameters={}
                    )
                ]
            )
        )
        
        observation_message = context.message_service.wait_for_response(
            source=team_name,
            timeout=TIMEOUT
        )
        if observation_message is not None and observation_message.observations:
            return observation_message.observations[0].data
        return None 