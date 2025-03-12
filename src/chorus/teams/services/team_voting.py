from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from chorus.data.collaboration_strategies import DecisionMakingStrategy
from chorus.data.state import TeamState
from chorus.data.data_types import ObservationData
from chorus.data.dialog import Message
from chorus.data.context import TeamContext
from chorus.helpers.communication import CommunicationHelper
from chorus.teams.services.base import TeamService

@TeamService.register("TeamVoting")
class TeamVoting(TeamService):
    def __init__(self, decision_making_strategy: DecisionMakingStrategy = DecisionMakingStrategy.MAJORITY_VOTE, proposal_duration_seconds: int = 300):
        """Initialize the voting service with configurable strategy and duration.
        
        Args:
            decision_making_strategy: The strategy to use for making decisions:
                - MAJORITY_VOTE: Proposal needs more than 50% of votes
                - FIRST_COME_FIRST_SERVE: First proposal is automatically selected
                - PLURALITY_VOTE: Proposal with most votes wins
            proposal_duration_seconds: How long proposals remain active for voting (in seconds).
        """
        super().__init__("team_voting")
        self.decision_making_strategy = decision_making_strategy
        self.proposal_duration_seconds = proposal_duration_seconds

    def initialize_service(self, team_state: TeamState):
        data_store = team_state.get_service_data_store(self.get_name())
        data_store["proposals"] = {}  # Dict[str, Dict] to store proposals
        data_store["votes"] = {}  # Dict[str, Dict[str, bool]] to store votes per proposal

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        if inbound_message.event_type != "team_service":
            return
        
        data_store = team_state.get_service_data_store(self.get_name())
        observations = []
        if inbound_message.actions is None:
            return
        for action in inbound_message.actions:
            if action.tool_name == self.get_name():
                if action.action_name == "propose":
                    result = self.create_proposal(
                        team_context,
                        data_store,
                        action.parameters.get("proposal_content"),
                        action.parameters.get("reasoning", ""),
                        inbound_message.source
                    )
                    observations.append(ObservationData(data=result))
                
                elif action.action_name == "vote":
                    result = self.cast_vote(
                        data_store,
                        action.parameters.get("proposal_id"),
                        inbound_message.source
                    )
                    observations.append(ObservationData(data=result))
                
                elif action.action_name == "get_proposal":
                    result = self.get_proposal(
                        data_store,
                        action.parameters.get("proposal_id")
                    )
                    observations.append(ObservationData(data=result))
                
                elif action.action_name == "list_active_proposals":
                    result = self.list_active_proposals(data_store)
                    observations.append(ObservationData(data=result))

        if observations:
            outbound_event = Message(
                destination=inbound_message.source,
                observations=observations
            )
            team_context.message_service.send_message(outbound_event)

    def create_proposal(self, team_context: TeamContext, data_store: Dict, content: str, reasoning: str, proposer: str) -> Dict:
        comm = CommunicationHelper(team_context)
        """Create a new proposal for voting."""
        if not content:
            return {"error": "Proposal content is required"}
        
        proposal_id = f"proposal_{len(data_store['proposals'])}"
        now = datetime.now()
        
        proposal = {
            "id": proposal_id,
            "content": content,
            "reasoning": reasoning,
            "proposer": proposer,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self.proposal_duration_seconds)).isoformat(),
            "status": "active"
        }
        
        data_store["proposals"][proposal_id] = proposal
        data_store["votes"][proposal_id] = {}

        # For first come first serve, automatically mark this as accepted if it's the first proposal
        if self.decision_making_strategy == DecisionMakingStrategy.FIRST_COME_FIRST_SERVE:
            active_proposals = self.list_active_proposals(data_store).get("active_proposals", {})
            if len(active_proposals) == 1:  # This is the first proposal
                data_store["votes"][proposal_id][proposer] = True
        else:
            # For other strategies, proposer automatically votes for their proposal
            data_store["votes"][proposal_id][proposer] = True

        # Notify all team members about the new proposal
        reasoning_text = f"\nReasoning: {reasoning}" if reasoning else ""
        team_info = self.get_team_info()
        if team_info is not None:
            if team_info.agent_ids:
                for agent_id in team_info.agent_ids:
                    comm.send(
                        destination=agent_id,
                        content=f"New proposal created by {proposer}:\nContent: {content}{reasoning_text}\nProposal ID: {proposal_id}"
                    )

        return {"proposal_id": proposal_id, "proposal": proposal}

    def cast_vote(self, data_store: Dict, proposal_id: str, voter: str) -> Dict:
        """Cast a vote for a proposal."""
        if proposal_id not in data_store["proposals"]:
            return {"error": "Proposal not found"}
        
        proposal = data_store["proposals"][proposal_id]
        if proposal["status"] != "active":
            return {"error": "Proposal is not active"}
        
        if datetime.now() > datetime.fromisoformat(proposal["expires_at"]):
            proposal["status"] = "expired"
            return {"error": "Proposal has expired"}
        
        # For first come first serve, don't allow voting
        if self.decision_making_strategy == DecisionMakingStrategy.FIRST_COME_FIRST_SERVE:
            return {"error": "Voting not allowed in first-come-first-serve mode"}
        
        # For plurality and majority voting, remove any existing votes by this voter
        if self.decision_making_strategy in [DecisionMakingStrategy.PLURALITY_VOTE, DecisionMakingStrategy.MAJORITY_VOTE]:
            for pid, votes in data_store["votes"].items():
                if voter in votes:
                    del votes[voter]
        
        # Record vote as True (in favor)
        data_store["votes"][proposal_id][voter] = True
        
        # Calculate current results
        votes = data_store["votes"][proposal_id]
        total_votes = len(self.get_team_info().agent_ids) if self.get_team_info() else len(votes)
        votes_in_favor = sum(1 for v in votes.values() if v)
        
        results = {
            "total_votes": total_votes,
            "votes_in_favor": votes_in_favor,
        }
        
        # Add strategy-specific results
        if self.decision_making_strategy == DecisionMakingStrategy.MAJORITY_VOTE:
            results["has_majority"] = votes_in_favor > total_votes / 2
        elif self.decision_making_strategy == DecisionMakingStrategy.PLURALITY_VOTE:
            # Get vote counts for all proposals
            all_vote_counts = self._get_vote_counts(data_store)
            results["is_leading"] = all_vote_counts[0][0] == proposal_id if all_vote_counts else False
        
        return {
            "success": True,
            "proposal_id": proposal_id,
            "voter": voter,
            "current_results": results
        }

    def _get_vote_counts(self, data_store: Dict) -> List[Tuple[str, int]]:
        """Get sorted list of proposal IDs and their vote counts.
        
        Returns:
            List of tuples (proposal_id, vote_count) sorted by vote count descending.
        """
        vote_counts = []
        for proposal_id, votes in data_store["votes"].items():
            if data_store["proposals"][proposal_id]["status"] == "active":
                vote_counts.append((proposal_id, len(votes)))
        return sorted(vote_counts, key=lambda x: (-x[1], data_store["proposals"][x[0]]["created_at"]))

    def get_proposal(self, data_store: Dict, proposal_id: str) -> Dict:
        """Get details of a specific proposal including votes."""
        if proposal_id not in data_store["proposals"]:
            return {"error": "Proposal not found"}
        
        proposal = data_store["proposals"][proposal_id]
        votes = data_store["votes"][proposal_id]
        
        # Update status if expired
        if proposal["status"] == "active" and datetime.now() > datetime.fromisoformat(proposal["expires_at"]):
            proposal["status"] = "expired"
        
        total_votes = len(votes)
        votes_in_favor = sum(1 for v in votes.values() if v)
        
        results = {
            "total_votes": total_votes,
            "votes_in_favor": votes_in_favor,
        }
        
        # Add strategy-specific results
        if self.decision_making_strategy == DecisionMakingStrategy.MAJORITY_VOTE:
            results["has_majority"] = votes_in_favor > total_votes / 2
        elif self.decision_making_strategy == DecisionMakingStrategy.PLURALITY_VOTE:
            all_vote_counts = self._get_vote_counts(data_store)
            results["is_leading"] = all_vote_counts[0][0] == proposal_id if all_vote_counts else False
        
        return {
            "proposal": proposal,
            "votes": votes,
            "results": results
        }

    def list_active_proposals(self, data_store: Dict) -> Dict:
        """List all active proposals."""
        active_proposals = {}
        for proposal_id, proposal in data_store["proposals"].items():
            if proposal["status"] == "active":
                if datetime.now() > datetime.fromisoformat(proposal["expires_at"]):
                    proposal["status"] = "expired"
                else:
                    active_proposals[proposal_id] = proposal
        
        return {"active_proposals": active_proposals}
    
    def get_decision(self, team_state: TeamState) -> Optional[str]:
        """Get the decision from the voting service based on the strategy.
        
        For majority vote: Returns first proposal that has majority votes
        For first come first serve: Returns the first active proposal
        For plurality vote: Returns proposal with most votes after expiry
        """
        data_store = team_state.get_service_data_store(self.get_name())
        if not data_store:
            return None

        # Get active proposals sorted by creation time
        proposals = data_store["proposals"]
        active_proposals = {
            pid: p for pid, p in proposals.items() 
            if p["status"] == "active" and datetime.now() <= datetime.fromisoformat(p["expires_at"])
        }
        
        if not active_proposals:
            return None

        if self.decision_making_strategy == DecisionMakingStrategy.FIRST_COME_FIRST_SERVE:
            # Return the first active proposal
            first_proposal = min(active_proposals.values(), key=lambda p: p["created_at"])
            return first_proposal["content"]
        
        elif self.decision_making_strategy == DecisionMakingStrategy.PLURALITY_VOTE:
            # Get proposal with most votes
            vote_counts = self._get_vote_counts(data_store)
            if not vote_counts:
                return None
                
            winning_id, winning_votes = vote_counts[0]
            total_required_votes = len(self.get_team_info().agent_ids) if self.get_team_info() else sum(len(votes) for votes in data_store["votes"].values())
            votes_cast = len(data_store["votes"].get(winning_id, {}))
            remaining_votes = total_required_votes - votes_cast
            
            # If second place exists, check if remaining votes could change outcome
            if len(vote_counts) > 1:
                second_place_votes = vote_counts[1][1]
                if winning_votes - second_place_votes <= remaining_votes:
                    return None
            
            # Return winner if all votes are in or remaining votes can't change outcome
            if votes_cast == total_required_votes or remaining_votes == 0:
                return proposals[winning_id]["content"]
            return None
        
        else:  # Majority vote
            for proposal_id, proposal in active_proposals.items():
                proposal_votes = data_store["votes"].get(proposal_id, {})
                total_required_votes = len(self.get_team_info().agent_ids) if self.get_team_info() else len(proposal_votes)
                votes_in_favor = sum(1 for v in proposal_votes.values() if v)

                if votes_in_favor > total_required_votes / 2:
                    return proposal["content"]

        return None
