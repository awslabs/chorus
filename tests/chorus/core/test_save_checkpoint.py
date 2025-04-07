import unittest
import time
from unittest.mock import MagicMock, patch

from chorus.agents import Agent
from chorus.core.runner import Chorus
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.checkpoint import ChorusCheckpoint, AgentSnapshot
from chorus.data.team_info import TeamInfo

class SimpleTestAgentState(AgentState):
    """Simple agent state implementation for testing."""
    
    counter: int = 0
    status: str = "idle"

class SimpleTestAgent(Agent):
    """Simple agent implementation for testing."""
    
    def __init__(self, test_param="default_value"):
        super().__init__()
        self.test_param = test_param
    
    def init_state(self) -> SimpleTestAgentState:
        return SimpleTestAgentState()
    
    def iterate(self, context: AgentContext, state: SimpleTestAgentState) -> SimpleTestAgentState:
        """Simple iteration that updates a counter in the state."""
        state.counter += 1
        return state

class MockMessageRouter:
    """Mock message router for testing state checkpoints."""
    
    def __init__(self):
        self._agent_state_map = {}
        
    def get_agent_state_map(self):
        """Return a copy of the agent state map."""
        return self._agent_state_map.copy()
    
    def get_agent_state(self, agent_id):
        """Get the state for a specific agent."""
        return self._agent_state_map.get(agent_id)
    
    def set_agent_state(self, agent_id, state_dict):
        """Set the state for an agent."""
        self._agent_state_map[agent_id] = state_dict

class MockGlobalContext:
    """Mock global context for testing."""
    
    def __init__(self):
        self._message_router = MockMessageRouter()
        
    def status_manager(self):
        """Return a mock status manager."""
        return MagicMock()

class TestSaveCheckpoint(unittest.TestCase):
    
    def setUp(self):
        # Create test agents with specific parameters
        self.agent1 = SimpleTestAgent(test_param="value1").name("Agent1")
        self.agent2 = SimpleTestAgent(test_param="value2").name("Agent2")
        
        # Create a Chorus instance with mock global context
        self.chorus = Chorus(agents=[self.agent1, self.agent2])
        
        # Replace the global context with our mock
        self.mock_global_context = MockGlobalContext()
        self.chorus._global_context = self.mock_global_context
        
        # Set up agent states
        self.agent1_state = {"counter": 5, "status": "ready"}
        self.agent2_state = {"counter": 10, "status": "busy"}
        
        # Add the states to the message router
        self.mock_global_context._message_router.set_agent_state("Agent1", self.agent1_state)
        self.mock_global_context._message_router.set_agent_state("Agent2", self.agent2_state)
    
    def test_save_checkpoint_basic(self):
        """Test basic checkpoint creation with agent snapshots."""
        # Call save_checkpoint
        checkpoint = self.chorus.save_checkpoint()
        
        # Verify the checkpoint is of the right type
        self.assertIsInstance(checkpoint, ChorusCheckpoint)
        
        # Verify the checkpoint contains agent snapshots
        self.assertEqual(len(checkpoint.agent_snapshot_map), 2)
        
        # Get the agent UUIDs from Chorus
        agent_uuids = {}
        for uuid, agent in self.chorus._agent_map.items():
            agent_uuids[agent.identifier()] = uuid
        
        # Check that both agents have snapshots
        for uuid in agent_uuids.values():
            self.assertIn(uuid, checkpoint.agent_snapshot_map)
    
    def test_save_checkpoint_agent_snapshots(self):
        """Test that agent snapshots are created correctly."""
        # Call save_checkpoint
        checkpoint = self.chorus.save_checkpoint()
        
        # Get the agent UUIDs from Chorus
        agent_uuids = {}
        for uuid, agent in self.chorus._agent_map.items():
            agent_uuids[agent.identifier()] = uuid
        
        # Check each agent snapshot
        for agent_id, uuid in agent_uuids.items():
            # Verify snapshot exists
            self.assertIn(uuid, checkpoint.agent_snapshot_map)
            
            # Get the snapshot
            snapshot = checkpoint.agent_snapshot_map[uuid]
            self.assertIsInstance(snapshot, AgentSnapshot)
            
            # Verify snapshot contains correct data
            self.assertTrue(snapshot.class_name.endswith("SimpleTestAgent"))
            self.assertEqual(snapshot.agent_name, agent_id)
            self.assertEqual(snapshot.agent_id, agent_id)
            
            # Check init arguments
            self.assertIsInstance(snapshot.init_args, tuple)
            self.assertIsInstance(snapshot.init_kwargs, dict)
            
            # Check that test_param is correctly stored
            if agent_id == "Agent1":
                self.assertEqual(snapshot.init_kwargs.get("test_param"), "value1")
            elif agent_id == "Agent2":
                self.assertEqual(snapshot.init_kwargs.get("test_param"), "value2")
                
            # Check that state_dump is included and has the right type
            self.assertIsInstance(snapshot.state_dump, dict)
    
    def test_save_checkpoint_with_agent_states(self):
        """Test that agent states are correctly included in the snapshots."""
        # Call save_checkpoint
        checkpoint = self.chorus.save_checkpoint()
        
        # Get the agent UUIDs from Chorus
        agent_uuids = {}
        for uuid, agent in self.chorus._agent_map.items():
            agent_uuids[agent.identifier()] = uuid
            
        # Check the state dumps in each snapshot
        for agent_id, uuid in agent_uuids.items():
            snapshot = checkpoint.agent_snapshot_map[uuid]
            
            # Verify state values are correctly stored in state_dump
            self.assertIsInstance(snapshot.state_dump, dict)
            self.assertIn("counter", snapshot.state_dump)
            self.assertIn("status", snapshot.state_dump)
            
            # Verify the specific state values
            if agent_id == "Agent1":
                self.assertEqual(snapshot.state_dump["counter"], 5)
                self.assertEqual(snapshot.state_dump["status"], "ready")
            elif agent_id == "Agent2":
                self.assertEqual(snapshot.state_dump["counter"], 10)
                self.assertEqual(snapshot.state_dump["status"], "busy")
    
    def test_save_checkpoint_no_router(self):
        """Test checkpoint creation when no message router is available."""
        # Remove the global context
        self.chorus._global_context = None
        
        # Call save_checkpoint
        checkpoint = self.chorus.save_checkpoint()
        
        # Verify the checkpoint still contains agent snapshots
        self.assertEqual(len(checkpoint.agent_snapshot_map), 2)
        
        # Since there's no global context, state_dumps should be empty
        for uuid, snapshot in checkpoint.agent_snapshot_map.items():
            agent = self.chorus._agent_map[uuid]
            agent_id = agent.identifier()
            
            self.assertEqual(snapshot.agent_id, agent_id)
            
            # Check that test_param is correctly stored
            if agent_id == "Agent1":
                self.assertEqual(snapshot.init_kwargs.get("test_param"), "value1")
            elif agent_id == "Agent2":
                self.assertEqual(snapshot.init_kwargs.get("test_param"), "value2")
                
            # State dump should be empty when no global context is available
            self.assertEqual(len(snapshot.state_dump), 0)
                
    def test_save_checkpoint_empty_state(self):
        """Test checkpoint creation with empty agent states."""
        # Clear the router states
        self.mock_global_context._message_router._agent_state_map = {}
        
        # Call save_checkpoint
        checkpoint = self.chorus.save_checkpoint()
        
        # Verify the snapshots have empty state dumps
        for uuid, snapshot in checkpoint.agent_snapshot_map.items():
            self.assertIsInstance(snapshot.state_dump, dict)
            self.assertEqual(len(snapshot.state_dump), 0, "State dump should be empty when agent has no state")

if __name__ == '__main__':
    unittest.main() 