import json
import unittest
from unittest.mock import patch, MagicMock
from chorus.data import Message
from chorus.agents import ConversationalTaskAgent
from chorus.toolbox.arxiv_tool import ArxivRetrieverTool
from chorus.data.dialog import EventType
from chorus.data.state import PassiveAgentState

def mock_generate(prompt):
    prompt_data = json.loads(prompt)
    if len(prompt_data["messages"]) == 1:
        # First call - return the tool use
        return MagicMock(to_dict=lambda: {
            "message": {
                "role": "assistant", 
                "content": [
                    {"toolUse": {"toolUseId": "tooluse_zb7HDcODTf2elJIq6EWdSw", "name": "ArxivRetriever__search", "input": {"query": "constrained decoding", "num_results": 3}}}
                ]
            }
        })
    else:
        # Second call - return a text response that will be sent to the user
        return MagicMock(to_dict=lambda: {
            "message": {
                "role": "assistant",
                "content": [
                    {"text": "Here are some papers on constrained decoding: Test Title by Test Author. The summary is: Test Summary"}
                ]
            }
        })

class TestArxivAgent(unittest.TestCase):
    def setUp(self):
        lm = MagicMock()
        lm.generate = mock_generate
        self.agent = ConversationalTaskAgent(
            "Charlie", 
            instruction="Do not search multiple times.", 
            tools=[ArxivRetrieverTool()],
            model_name='anthropic.claude-3-haiku-20240307-v1:0',
            lm=lm
        )
        self.context = self.agent.init_context()
        self.state = self.agent.init_state()

    @patch("chorus.toolbox.arxiv_tool.arxiv")
    def test_arxiv_search(self, mock_arxiv):
        # Mock the arxiv client
        mock_arxiv.Client.return_value = MagicMock()
        mock_arxiv.Client.return_value.results.return_value = [
            MagicMock(
                entry_id='foobar',
                title='Test Title',
                summary='Test Summary',
                authors=[MagicMock(name='Test Author')],
            )
        ]

        # Send test query
        self.context.message_service.send_message(
            Message(
                source="human", 
                destination="Charlie", 
                content="any good paper on constrained decoding?"
            )
        )
        
        # Run agent iteration
        new_state = self.agent.iterate(self.context, self.state)
        
        # Verify messages were exchanged
        messages = self.context.message_service.fetch_all_messages()
        print(messages)
        self.assertGreater(len(messages), 0)
        
        # Verify agent responded
        agent_messages = [m for m in messages if m.source == "Charlie"]
        self.assertGreater(len(agent_messages), 0)
        
        # Verify response content
        user_directed_messages = [m for m in agent_messages if m.destination == "human"]
        self.assertGreater(len(user_directed_messages), 0)
        self.assertIn("Test Title", user_directed_messages[0].content)

if __name__ == '__main__':
    unittest.main()
