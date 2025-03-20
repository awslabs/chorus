import multiprocessing
import unittest
import time
from unittest.mock import MagicMock
from chorus.core import Chorus
from chorus.agents import ConversationalTaskAgent, TaskCoordinatorAgent
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.helpers.communication import CommunicationHelper

class TestChorusInThread(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Store the original start method
        try:
            cls.original_start_method = multiprocessing.get_start_method()
        except RuntimeError:
            cls.original_start_method = 'spawn'  # Default to spawn if not set

    def setUp(self):
        # Set start method to fork
        multiprocessing.set_start_method('fork', force=True)

        lm = MagicMock()
        lm.generate.return_value = MagicMock(to_dict=lambda: {"message": {"content": [{"text": "Hello, World!"}]}})

        # Create a simple team with a coordinator and a chat agent
        self.coordinator = TaskCoordinatorAgent(
            "Coordinator",
            instruction="Coordinate with other agents to answer questions.",
            reachable_agents={
                "Assistant": "A simple chat agent that can answer basic questions."
            },
            model_name="anthropic.claude-3-5-haiku-20241022-v1:0",
            lm=lm
        )
        
        self.assistant = ConversationalTaskAgent(
            "Assistant",
            instruction="Answer basic questions directly and concisely.",
            model_name="anthropic.claude-3-5-haiku-20241022-v1:0",
            lm=lm
        )

        self.team = Team(
            name="TestTeam",
            agents=[self.coordinator, self.assistant],
            collaboration=CentralizedCollaboration(
                coordinator=self.coordinator.get_name()
            )
        )

        self.chorus = Chorus(teams=[self.team])
        
    def tearDown(self):
        # Ensure chorus is stopped
        if hasattr(self, 'chorus'):
            self.chorus.stop()
        
        # Reset the start method to original
        multiprocessing.set_start_method(self.original_start_method, force=True)

    def test_start_stop_thread(self):
        # Test that chorus starts properly in a thread
        self.chorus.start()
        self.assertTrue(self.chorus._chorus_thread.is_alive())
        
        # Test that starting again doesn't create a new thread
        original_thread = self.chorus._chorus_thread
        self.chorus.start()
        self.assertEqual(original_thread, self.chorus._chorus_thread)
        
        # Test stopping
        self.chorus.stop()
        self.assertFalse(self.chorus._chorus_thread.is_alive())

    def test_agent_communication_in_thread(self):
        # Start chorus in a thread
        self.chorus.start()
        
        # Create communication helper
        comm = CommunicationHelper(self.chorus.get_global_context())
        
        # Send a test message
        test_message = "What is 2+2?"
        comm.send(
            destination="Coordinator",
            content=test_message
        )
        
        # Wait for response with timeout
        response = comm.wait(
            source="Coordinator",
            timeout=180  # 180 seconds timeout
        )
        
        # Verify we got a response
        self.assertIsNotNone(response)
        self.assertTrue(len(response.content) > 0)
        
        # Stop chorus
        self.chorus.stop()

    def test_multiple_start_stop_cycles(self):
        # Test that chorus can be started and stopped multiple times
        for _ in range(3):
            print("Starting chorus")
            self.chorus.start()
            self.assertTrue(self.chorus._chorus_thread.is_alive())
            
            # Give it a moment to initialize
            time.sleep(0.1)
            
            self.chorus.stop()
            self.assertFalse(self.chorus._chorus_thread.is_alive())
            print("Chorus stopped")
            time.sleep(3)
        
if __name__ == '__main__':
    unittest.main()
