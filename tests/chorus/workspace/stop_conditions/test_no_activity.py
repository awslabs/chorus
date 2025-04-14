import time
import pytest
from unittest.mock import MagicMock, patch

from chorus.data.agent_status import AgentStatus, AgentStatusRecord
from chorus.workspace.stop_conditions import NoActivityStopper


class TestNoActivityStopper:
    """Test cases for the NoActivityStopper class."""
    
    def test_stop_all_idle_with_old_timestamp(self):
        """Test that the stopper returns True when all agents are idle and last activity is old."""
        # Create a mock runner
        mock_runner = MagicMock()
        current_time = int(time.time())
        
        # All agents are idle with status records - timestamps are old
        mock_runner.get_agents_status.return_value = {
            "agent1": AgentStatusRecord(status=AgentStatus.IDLE, last_active_timestamp=current_time - 15),
            "agent2": AgentStatusRecord(status=AgentStatus.IDLE, last_active_timestamp=current_time - 20)
        }
        
        # Create the stopper with a 10 second threshold
        stopper = NoActivityStopper(no_activity_time_threshold=10)
        stopper.set_runner(mock_runner)
        
        # Test that it returns True (should stop)
        assert stopper.stop() is True
    
    def test_stop_all_idle_with_recent_timestamp(self):
        """Test that the stopper returns False when all agents are idle but activity is recent."""
        # Create a mock runner
        mock_runner = MagicMock()
        current_time = int(time.time())
        
        # All agents are idle with status records - timestamps are recent
        mock_runner.get_agents_status.return_value = {
            "agent1": AgentStatusRecord(status=AgentStatus.IDLE, last_active_timestamp=current_time - 5),
            "agent2": AgentStatusRecord(status=AgentStatus.IDLE, last_active_timestamp=current_time - 8)
        }
        
        # Create the stopper with a 10 second threshold
        stopper = NoActivityStopper(no_activity_time_threshold=10)
        stopper.set_runner(mock_runner)
        
        # Test that it returns False (should not stop yet)
        assert stopper.stop() is False
    
    def test_stop_some_busy_with_old_timestamp(self):
        """Test that the stopper returns False when some agents are busy, even with old timestamp."""
        # Create a mock runner
        mock_runner = MagicMock()
        current_time = int(time.time())
        
        # Not all agents are idle, although timestamps are old
        mock_runner.get_agents_status.return_value = {
            "agent1": AgentStatusRecord(status=AgentStatus.IDLE, last_active_timestamp=current_time - 15),
            "agent2": AgentStatusRecord(status=AgentStatus.BUSY, last_active_timestamp=current_time - 15)
        }
        
        # Create the stopper with a 10 second threshold
        stopper = NoActivityStopper(no_activity_time_threshold=10)
        stopper.set_runner(mock_runner)
        
        # Test that it returns False (should not stop while agents are busy)
        assert stopper.stop() is False
    
    def test_stop_no_agents(self):
        """Test that the stopper returns False when no agents are registered."""
        # Create a mock runner
        mock_runner = MagicMock()
        
        # No agents registered
        mock_runner.get_agents_status.return_value = {}
        
        # Create the stopper with a 10 second threshold
        stopper = NoActivityStopper(no_activity_time_threshold=10)
        stopper.set_runner(mock_runner)
        
        # Test that it returns False (can't determine activity without agents)
        assert stopper.stop() is False 