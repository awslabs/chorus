import time
import logging
from typing import Dict, List, Optional, Tuple, Union

from pydantic import BaseModel

from chorus.data.agent_status import AgentStatus
from chorus.communication.message_service import ChorusMessageRouter
from chorus.communication.zmq_protocol import MessageType, ZMQMessage

logger = logging.getLogger(__name__)

class MultiAgentStatusManager(BaseModel):
    """Manages status tracking for agents using ZMQ for communication.
    
    Provides functionality for tracking and updating the status of various
    components in the system using ZMQ-based communication.
    """
    
    def __init__(self, message_router: Optional[ChorusMessageRouter] = None):
        """Initialize the status manager.
        
        Args:
            message_router: The ZMQ message router to use for communication
            proc_manager: Legacy parameter for compatibility, not used in ZMQ implementation
        """
        super().__init__()
        self._message_router = message_router
        self._status_records = []  # [(timestamp, agent_id, status)]
        
    def record(self, agent_id: str, status: AgentStatus):
        """Record an agent status event.
        
        Args:
            agent_id: ID of the agent
            status: Status to record
        """
        timestamp = int(time.time())
        self._status_records.append((timestamp, agent_id, status))
        
    def record_plan(
        self,
        agent_id: str,
        plan: Optional[str],
        current_step: Optional[str],
        current_progress: Optional[float],
    ):
        """Record a plan execution event.
        
        Args:
            agent_id: ID of the agent
            plan: The current plan
            current_step: The current step being executed
            current_progress: The progress through the plan (0.0-1.0)
        """
        # This could be enhanced to send plan information over ZMQ
        pass
    
    def get_records(self) -> List[Tuple[int, str, AgentStatus]]:
        """Get all status records.
        
        Returns:
            List of (timestamp, agent_id, status) tuples
        """
        return self._status_records
    
    def update_status(self, entity_id: str, status: AgentStatus):
        """Update the status of an entity.
        
        Args:
            entity_id: ID of the entity to update
            status: New status to set
        """
        timestamp = int(time.time())
        self._status_records.append((timestamp, entity_id, status))
        
    def get_status(self, entity_id: str) -> Optional[AgentStatus]:
        """Get the current status of an entity.
        
        Args:
            entity_id: ID of the entity to check
        
        Returns:
            Current status of the entity, or None if not found
        """
        for timestamp, agent_id, status in reversed(self._status_records):
            if agent_id == entity_id:
                return status
        return None
