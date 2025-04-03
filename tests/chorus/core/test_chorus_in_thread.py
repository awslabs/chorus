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

    def setUp(self):

        # Create a simple team with a coordinator and a chat agent
        self.coordinator = TaskCoordinatorAgent(
            instruction="Coordinate with other agents to answer questions.",
            reachable_agents={
                "Assistant": "A simple chat agent that can answer basic questions."
            },
            model_name="anthropic.claude-3-5-haiku-20241022-v1:0",
        ).name("Coordinator")
        
        self.assistant = ConversationalTaskAgent(
            instruction="Answer basic questions directly and concisely.",
            model_name="anthropic.claude-3-5-haiku-20241022-v1:0",
        ).name("Assistant")

        self.team = Team(
            name="TestTeam",
            agents=[self.coordinator, self.assistant],
            collaboration=CentralizedCollaboration(
                coordinator=self.coordinator.identifier()
            )
        )

        self.chorus = Chorus(teams=[self.team])
        
    def tearDown(self):
        # Ensure chorus is stopped
        if hasattr(self, 'chorus'):
            self.chorus.stop()
        

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
        time.sleep(5)
        
        # Send a test message
        test_message = "What is 2+2?"
        response = self.chorus.send_and_wait(
            destination=self.coordinator.identifier(),
            message=test_message,
            timeout=180
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
