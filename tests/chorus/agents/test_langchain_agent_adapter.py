import unittest
from unittest.mock import patch, MagicMock

from chorus.agents.langchain_agent_adapter import LangChainAgentAdapter
from chorus.data.context import AgentContext
from chorus.data.dialog import Message, EventType
from chorus.data.state import PassiveAgentState
from chorus.util.testing_util import MockMessageClient


class MockFunction:
    """A mock function to use in LangChain tools."""
    
    def __init__(self, return_value):
        self.return_value = return_value
        self.called_with = None
        
    def __call__(self, *args, **kwargs):
        self.called_with = (args, kwargs)
        return self.return_value


# Create a mock base callback handler
class MockBaseCallbackHandler:
    def __init__(self, *args, **kwargs):
        pass


class TestLangChainAgentAdapter(unittest.TestCase):
    """Test cases for the LangChainAgentAdapter."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock the required langchain modules with proper callback handler
        langchain_mocks = {
            'langchain': MagicMock(),
            'langchain.agents': MagicMock(),
            'langchain.schema': MagicMock(),
            'langchain.callbacks.manager': MagicMock(),
        }
        
        # Create a mock BaseCallbackHandler
        mock_callback_module = MagicMock()
        mock_callback_module.BaseCallbackHandler = MockBaseCallbackHandler
        langchain_mocks['langchain.callbacks.base'] = mock_callback_module
        
        self.langchain_modules_patcher = patch.dict('sys.modules', langchain_mocks)
        self.langchain_modules_patcher.start()
        
        # Create the mock agent executor
        self.mock_agent_executor = MagicMock()
        # Set up the run method to return a text response
        self.mock_agent_executor.run.return_value = "This is a response from the LangChain agent."
        self.mock_agent_executor.callbacks = MagicMock()
        self.mock_agent_executor.callbacks.add_handler = MagicMock()
        self.mock_agent_executor.callbacks.remove_handler = MagicMock()
        
        # Create a factory function that returns our mock agent
        def mock_agent_factory():
            return self.mock_agent_executor
        
        # Create the LangChainAgentAdapter with our mock factory
        self.agent = LangChainAgentAdapter(
            agent_factory=mock_agent_factory,
            preserve_history=True
        ).name("langchain_agent")
        
        # Initialize the agent context
        self.context = AgentContext(agent_id=self.agent.identifier())
        self.context.message_client = MockMessageClient(self.agent.identifier())
        
        # Initialize the agent state
        self.state = self.agent.init_state()
    
    def tearDown(self):
        """Tear down the test environment."""
        self.langchain_modules_patcher.stop()
    
    def test_respond_to_message(self):
        """Test that the agent responds to a message."""
        # Create a test message
        message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="Hello, can you help me?",
            event_type=EventType.MESSAGE
        )
        self.context.message_client.send_message(message)
        
        # Run the agent's respond method
        new_state = self.agent.respond(self.context, self.state, message)
        
        # Check that the agent executor was called with the expected input
        self.mock_agent_executor.run.assert_called_once()
        call_args = self.mock_agent_executor.run.call_args[0][0]
        self.assertEqual(call_args["input"], "Hello, can you help me?")
        
        # Check that the agent sent a response message
        outgoing_messages = self.context.message_client.filter_messages(
            source=self.agent.identifier(),
            destination="user"
        )
        self.assertEqual(len(outgoing_messages), 1)
        self.assertEqual(outgoing_messages[0].content, "This is a response from the LangChain agent.")
    
    def test_conversation_history(self):
        """Test that conversation history is preserved."""
        # Create and process the first message
        first_message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="First message",
            event_type=EventType.MESSAGE
        )
        new_state = self.agent.respond(self.context, self.state, first_message)
        
        # Verify that the conversation is stored in the state
        conversation_id = f"user-{self.agent.identifier()}"
        self.assertIn(conversation_id, new_state.langchain_memory)
        
        # Create and process a second message
        second_message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="Second message",
            event_type=EventType.MESSAGE
        )
        final_state = self.agent.respond(self.context, new_state, second_message)
        
        # Verify that the history contains both conversations
        self.assertIn(conversation_id, final_state.langchain_memory)
        chat_history = final_state.langchain_memory[conversation_id].get("chat_history", [])
        self.assertEqual(len(chat_history), 2)
        self.assertEqual(chat_history[0][0], "First message")
        self.assertEqual(chat_history[1][0], "Second message")
    
    def test_error_handling(self):
        """Test that errors are handled properly."""
        # Set up the agent executor to raise an exception
        self.mock_agent_executor.run.side_effect = Exception("Simulated error")
        
        # Create a test message
        message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="Hello, can you help me?",
            event_type=EventType.MESSAGE
        )
        
        # Run the agent's respond method
        new_state = self.agent.respond(self.context, self.state, message)
        
        # Check that an error message was sent
        outgoing_messages = self.context.message_client.filter_messages(
            source=self.agent.identifier(),
            destination="user"
        )
        self.assertEqual(len(outgoing_messages), 1)
        self.assertIn("Sorry, I encountered an error", outgoing_messages[0].content)


if __name__ == "__main__":
    unittest.main() 