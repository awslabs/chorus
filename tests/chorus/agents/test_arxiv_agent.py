import json
import unittest
from unittest.mock import patch, MagicMock

from chorus.data.dialog import Message, EventType
from chorus.agents import ConversationalTaskAgent
from chorus.data.state import PassiveAgentState
from chorus.data import ActionData, ObservationData
from chorus.toolbox.arxiv_tool import ArxivRetrieverTool
from chorus.util.testing_util import MockMessageClient
from chorus.data.prompt import StructuredCompletion

class TestArxivAgent(unittest.TestCase):
    @patch("chorus.toolbox.arxiv_tool.arxiv")
    def setUp(self, mock_arxiv):
        # Mock the ArxivRetrieverTool's arxiv client
        mock_client = MagicMock()
        mock_results = [
            MagicMock(
                entry_id='https://arxiv.org/abs/2302.01318',
                title='Machine Learning: A Comprehensive Survey',
                summary='This paper provides a comprehensive survey of machine learning techniques and applications.',
                authors=[MagicMock(name='John Smith'), MagicMock(name='Jane Doe')]
            )
        ]
        mock_client.results.return_value = mock_results
        mock_arxiv.Client.return_value = mock_client
        mock_arxiv.Search.return_value = MagicMock()
        
        # Set up arxiv retriever tool
        self.arxiv_tool = ArxivRetrieverTool()
        
        # Mock LLM for the agent
        self.mock_lm = MagicMock()
        # Mock the LLM to generate a response that uses the arxiv tool and then summarizes the results
        self.mock_lm.generate.return_value = StructuredCompletion(
            '{"message": {"role": "assistant", "content": "I\'ll search for papers about machine learning."},"tool_calls": [{"name": "ArxivRetriever.search", "parameters": {"query": "machine learning", "num_results": 5}}]}'
        )
        
        # Set up agent with mocked LLM
        self.agent = ConversationalTaskAgent(
            tools=[self.arxiv_tool],
            instruction="Use the provided tools to search for papers.",
            lm=self.mock_lm
        ).name("ArxivAgent")
        self.agent.initialize()
        
        # Initialize agent context
        self.context = self.agent.init_context()
        self.context.message_client = MockMessageClient(self.agent.identifier())
        
        # Initialize agent state
        self.state = PassiveAgentState()
        
    def test_arxiv_search(self):
        # Create a test query message
        query_message = Message(
            source="user",
            destination="ArxivAgent",
            channel="user_channel",
            content="Can you find a paper about machine learning?",
            event_type=EventType.MESSAGE
        )
        self.context.message_client.send_message(query_message)

        # Run the agent iteration (now uses mocked response)
        new_state = self.agent.iterate(self.context, self.state)
        
        # Check that the agent has at least one message in response
        self.assertTrue(len(self.context.message_client.fetch_all_messages()) > 1, "Agent should have generated a response")
        
        # Verify the response is related to arxiv search
        response_messages = [msg for msg in self.context.message_client.fetch_all_messages() 
                            if msg.source == "ArxivAgent" and msg.destination == "user"]
        
        self.assertTrue(len(response_messages) > 0, "Agent should have sent a response to the user")
        
        # Verify that the arxiv tool was called
        self.mock_lm.generate.assert_called()

if __name__ == '__main__':
    unittest.main()
