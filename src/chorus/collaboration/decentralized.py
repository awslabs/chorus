from typing import List, Optional, Dict
from datetime import datetime

from chorus.collaboration.base import Collaboration
from chorus.data.dialog import Message
from chorus.helpers.communication import CommunicationHelper
from chorus.teams.services.team_voting import TeamVoting
from chorus.data.team_info import TeamInfo
from chorus.data.context import TeamContext
from chorus.data.state import TeamState
from chorus.teams.services.base import TeamService

class TaskInfo:
    """Information about a queued task."""
    def __init__(self, task_id: str, content: str, requester: str):
        self.task_id = task_id
        self.content = content
        self.requester = requester

    def to_dict(self) -> Dict:
        """Convert TaskInfo to dictionary for storage."""
        return {
            "task_id": self.task_id,
            "content": self.content,
            "requester": self.requester
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TaskInfo":
        """Create TaskInfo from dictionary."""
        return cls(
            task_id=data["task_id"],
            content=data["content"],
            requester=data["requester"]
        )

@Collaboration.register('DecentralizedCollaboration')
class DecentralizedCollaboration(Collaboration):
    """Implements a decentralized collaboration strategy between agents.

    This strategy allows initiative taker agents to directly obtain a task from team and work on the task.
    All agents can propose and vote on solutions. Once a majority vote is reached, that solution is used as the team's response.
    If no majority is reached within the time limit, the collaboration stops with no decision.
    
    Tasks are queued if there is currently a task being processed. When the current task is completed,
    the next task in the queue will automatically start.
    """

    def __init__(self, initiative_takers: Optional[List[str]] = None, time_limit: Optional[int] = 60):
        """Initialize the decentralized collaboration strategy.

        Args:
            initiative_takers (List[str]): The agents that can take initiative to obtain a task from the team.
            time_limit (int): The time limit in seconds for reaching a decision. None means no limit.
        """
        super().__init__()
        self.initiative_takers = initiative_takers
        self.time_limit = time_limit
        self.CHECK_INTERVAL = 3  # Check every 3 seconds
        self._voting_service = None
        self._team_info = None

    def _get_data_store(self, team_state: TeamState) -> Dict:
        """Get or initialize the collaboration data store."""
        data_store = team_state.get_collaboration_data_store()
        if "task_start_time" not in data_store:
            data_store.update({
                "task_start_time": None,
                "current_task_id": None,
                "current_requester": None,
                "last_check_time": None,
                "task_queue": []  # List of TaskInfo dictionaries
            })
        return data_store

    def register_team(self, team_info: TeamInfo, services: List["TeamService"]):
        """Register team info and services with the collaboration."""
        self._team_info = team_info
        for service in services:
            if isinstance(service, TeamVoting):
                self._voting_service = service
                break

    def process_message(self, team_context: TeamContext, team_state: TeamState, inbound_message: Message):
        """Process incoming messages and manage the decentralized collaboration."""
        if inbound_message.event_type == "team_service":
            return

        # Find voting service if not already set
        if not self._voting_service:
            for service in self.list_services():
                if isinstance(service, TeamVoting):
                    self._voting_service = service
                    break

        # Check if voting service is available
        if not self._voting_service:
            helper = CommunicationHelper(team_context)
            helper.send(inbound_message.source, "Error: Team voting service is not configured")
            return

        # Create task info
        task = TaskInfo(
            task_id=inbound_message.message_id,
            content=inbound_message.content,
            requester=inbound_message.source
        )

        data_store = self._get_data_store(team_state)
        
        # If no current task, start this one
        if data_store["current_task_id"] is None:
            self._start_task(task, team_context, team_state)
        else:
            # Queue the task and notify requester
            data_store["task_queue"].append(task.to_dict())
            helper = CommunicationHelper(team_context)
            helper.send(
                task.requester,
                f"Your task has been queued. Current queue position: {len(data_store['task_queue'])}",
                source=self._team_info.get_identifier()
            )

    def iterate(self, team_context: TeamContext, team_state: TeamState) -> TeamState:
        """Periodically check for voting results and time limits."""
        data_store = self._get_data_store(team_state)
        if data_store["current_task_id"] is None or not self._voting_service:
            return team_state

        # Only check every CHECK_INTERVAL seconds
        now = datetime.now()
        last_check_time = datetime.fromisoformat(data_store["last_check_time"]) if data_store["last_check_time"] else None
        if last_check_time and (now - last_check_time).total_seconds() < self.CHECK_INTERVAL:
            return team_state
        
        data_store["last_check_time"] = now.isoformat()
        helper = CommunicationHelper(team_context)

        # Check if we've exceeded time limit
        if self.time_limit is not None:
            task_start_time = datetime.fromisoformat(data_store["task_start_time"])
            elapsed_time = (now - task_start_time).total_seconds()
            if elapsed_time > self.time_limit:
                # Send timeout message to requester
                helper.send(
                    data_store["current_requester"],
                    "No decision was reached within the time limit.",
                    source=self._team_info.get_identifier()
                )
                # Notify all agents about collaboration end
                self._notify_collaboration_end(team_context, "Collaboration ended: Time limit exceeded")
                self._end_current_task(team_context, team_state)
                return team_state

        # Check for majority decision using voting service
        decision = self._voting_service.get_decision(team_state)
        if decision:
            # Send result to requester
            helper.send(
                data_store["current_requester"],
                decision,
                source=self._team_info.get_identifier()
            )
            # Notify all agents about collaboration end with winning proposal
            self._notify_collaboration_end(
                team_context,
                f"Collaboration ended: Majority decision reached\nWinning proposal: {decision}"
            )
            self._end_current_task(team_context, team_state)
            return team_state

        return team_state

    def _notify_collaboration_end(self, team_context: TeamContext, message: str):
        """Send notification to all team agents about collaboration end."""
        helper = CommunicationHelper(team_context)
        for agent_id in self._team_info.agent_ids:
            helper.send(
                agent_id,
                message,
                source=self._team_info.get_identifier()
            )

    def _start_task(self, task: TaskInfo, team_context: TeamContext, team_state: TeamState):
        """Start processing a new task."""
        data_store = self._get_data_store(team_state)
        data_store.update({
            "current_task_id": task.task_id,
            "current_requester": task.requester,
            "task_start_time": datetime.now().isoformat(),
            "last_check_time": datetime.now().isoformat()
        })
        
        # Forward task to initiative takers or all agents
        helper = CommunicationHelper(team_context)
        if self.initiative_takers:
            # Forward to specified initiative takers
            for agent_id in self.initiative_takers:
                helper.send(agent_id, task.content, source=task.requester)
        else:
            # Forward to all agents in team
            for agent_id in self._team_info.agent_ids:
                helper.send(agent_id, task.content, source=task.requester)

    def _end_current_task(self, team_context: TeamContext, team_state: TeamState):
        """End current task and start next task if available."""
        data_store = self._get_data_store(team_state)
        self._reset_task(data_store)
        
        # Start next task if available
        if data_store["task_queue"]:
            next_task_dict = data_store["task_queue"].pop(0)
            next_task = TaskInfo.from_dict(next_task_dict)
            self._start_task(next_task, team_context, team_state)
            
            # Notify remaining queue positions
            if data_store["task_queue"]:
                helper = CommunicationHelper(team_context)
                for i, task_dict in enumerate(data_store["task_queue"], 1):
                    helper.send(
                        task_dict["requester"],
                        f"Queue position updated: {i}",
                        source=self._team_info.get_identifier()
                    )

    def _reset_task(self, data_store: Dict):
        """Reset the current task tracking."""
        data_store.update({
            "current_task_id": None,
            "task_start_time": None,
            "current_requester": None,
            "last_check_time": None
        })

    def get_name(self):
        return "decentralized"
    
    