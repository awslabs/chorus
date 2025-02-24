import unittest
from chorus.data import Message
from chorus.agents import ToolChatAgent
from chorus.data import Role
from chorus.toolbox.arxiv_tool import ArxivRetrieverTool

class TestArxivAgent(unittest.TestCase):
    def setUp(self):
        self.agent = ToolChatAgent(
            "Charlie", 
            instruction="Do not search multiple times.", 
            tools=[ArxivRetrieverTool()],
            model_name='anthropic.claude-3-haiku-20240307-v1:0'
        )
        self.context = self.agent.init_context()
        self.state = self.agent.init_state()

    def test_arxiv_search(self):
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
        self.assertGreater(len(messages), 0)
        
        # Verify agent responded
        agent_messages = [m for m in messages if m.source == "Charlie"]
        self.assertGreater(len(agent_messages), 0)

if __name__ == '__main__':
    unittest.main()
