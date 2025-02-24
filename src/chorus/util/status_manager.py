import time
from multiprocessing import Manager
from typing import List
from typing import Optional
from typing import Tuple

from pydantic import BaseModel

from chorus.data.agent_status import AgentStatus


class MultiAgentStatusManager(BaseModel):
    """Manages status tracking for agents and processes.

    Provides functionality for tracking and updating the status of various
    components in the system, including agents and their tasks.
    """

    status_records: Optional[List[str]] = None

    def __init__(self, proc_manager: Manager):
        super().__init__()
        self.status_records = proc_manager.list()

    def record(self, agent_id: str, status: AgentStatus):
        timestamp = int(time.time())
        self.status_records.append(f"{timestamp} ||| {agent_id} ||| {status.value}")

    def record_plan(
        self,
        agent_id: str,
        plan: Optional[str],
        current_step: Optional[str],
        current_progress: Optional[float],
    ):
        pass

    def get_records(self) -> List[Tuple[int, str, AgentStatus]]:
        records = []
        for record in self.status_records:
            timestamp, agent_id, status = record.split(" ||| ")
            timestamp = int(timestamp)
            records.append((timestamp, agent_id, AgentStatus(status)))
        return records

    def update_status(self, entity_id: str, status: AgentStatus):
        """Update the status of an entity.

        Args:
            entity_id (str): ID of the entity to update.
            status (Status): New status to set.
        """
        timestamp = int(time.time())
        self.status_records.append(f"{timestamp} ||| {entity_id} ||| {status.value}")

    def get_status(self, entity_id: str) -> Optional[AgentStatus]:
        """Get the current status of an entity.

        Args:
            entity_id (str): ID of the entity to check.

        Returns:
            Optional[Status]: Current status of the entity, or None if not found.
        """
        for record in self.status_records:
            timestamp, agent_id, status = record.split(" ||| ")
            if agent_id == entity_id:
                return AgentStatus(status)
        return None
