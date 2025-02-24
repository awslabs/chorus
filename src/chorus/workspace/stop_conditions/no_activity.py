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
        last_activity_timestamp = runner.get_last_activity_timestamp()
        if (
            last_activity_timestamp is not None
            and all(status == AgentStatus.AVAILABLE for status in agent_status_map.values())
            and time.time() - last_activity_timestamp > self._no_activity_time_threshold
        ):
            return True
        else:
            return False
