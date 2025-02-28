import unittest
from chorus.data import Message
from chorus.agents import ToolChatAgent, SynchronizedCoordinatorAgent
from chorus.core.runner import Chorus
from chorus.teams import Team
from chorus.collaboration import CentralizedCollaboration
from chorus.workspace.stop_conditions import NoActivityStopper
from chorus.helpers.communication import CommunicationHelper

class TestCentralizedCollaboration(unittest.TestCase):
    def setUp(self):
        # Set up agents and team before each test
        self.sub_agents = {
            "MathExpert": "This is a MathExpert can answer your math questions."
        }
        self.router = SynchronizedCoordinatorAgent(
            name="Router",
            reachable_agents=self.sub_agents
        )
        self.math_expert = ToolChatAgent(
            "MathExpert",
            instruction="You are MathExpert, an expert that can answer any question about math."
        )
        self.team = Team(
            name="myteam",
            agents=[self.router, self.math_expert],
            collaboration=CentralizedCollaboration(coordinator=self.router.get_name())
        )
        self.chorus = Chorus(teams=[self.team])
        self.chorus.start()
        self.comm_helper = CommunicationHelper(self.chorus.get_global_context())
    
    def tearDown(self):
        self.chorus.stop()

    def test_single_request_processing(self):
        """Test that a single request is properly processed through the coordinator"""
        # Send a math question and wait for response
        question = "How to solve 3x^2 + 5 = 13? Please just give me the answer, no explanation needed."
        response = self.comm_helper.send_and_wait(
            destination="team:myteam",
            content=question,
            source="human",
            timeout=180
        )
        
        # Verify response
        self.assertIsNotNone(response, "Should receive a response")
        self.assertEqual(response.source, "team:myteam", "Response should come from the team")
        self.assertIsNotNone(response.content, "Response should have content")
        self.assertTrue(len(response.content) > 0, "Response content should not be empty")
        
    def test_multiple_requests_queuing(self):
        """Test that multiple requests are properly queued and processed in order"""
        # Send multiple questions in sequence
        questions = [
            "What is 2 + 2? Please just give me the answer, no explanation needed.",
            "Solve x^2 = 16. Please just give me the answer, no explanation needed.",
        ]
        
        responses = []
        for question in questions:
            response = self.comm_helper.send_and_wait(
                destination="team:myteam",
                content=question,
                source="human",
                timeout=180
            )
            responses.append(response)
        
        # Verify all messages were processed
        self.assertEqual(len(responses), len(questions), "Should receive response for each question")
        
        # Verify each response
        for i, response in enumerate(responses):
            self.assertIsNotNone(response, f"Should receive response for question {i+1}")
            self.assertEqual(response.source, "team:myteam", f"Response {i+1} should come from the team")
            self.assertTrue(len(response.content) > 0, f"Response {i+1} content should not be empty")
            
            # For the first response, verify queue notification
            if i > 0:
                self.assertNotIn("queue position", response.content.lower(), 
                               f"Response {i+1} should not be a queue notification")

if __name__ == '__main__':
    unittest.main()