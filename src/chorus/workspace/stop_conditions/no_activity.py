import time

from chorus.data.agent_status import AgentStatus
from chorus.workspace.stop_conditions.base import MultiAgentStopCondition


class NoActivityStopper(MultiAgentStopCondition):

    def __init__(self, no_activity_time_threshold: int = 10):
        super().__init__()
        self._no_activity_time_threshold = no_activity_time_threshold

    def stop(self) -> bool:
        """Check if there has been no activity for too long.

        Returns:
            bool: True if there has been no activity for longer than max_idle_time.
        """
        runner = self.runner()
        agent_status_map = runner.get_agents_status()
        
        # If no agents are registered, we can't determine inactivity
        if not agent_status_map:
            return False
            
        most_recent_timestamp = None
        for status_record in agent_status_map.values():
            if most_recent_timestamp is None or status_record.last_active_timestamp > most_recent_timestamp:
                most_recent_timestamp = status_record.last_active_timestamp
                
        if (
            most_recent_timestamp is not None
            and all(status_record.status == AgentStatus.IDLE for status_record in agent_status_map.values())
            and time.time() - most_recent_timestamp > self._no_activity_time_threshold
        ):
            return True
        return False
