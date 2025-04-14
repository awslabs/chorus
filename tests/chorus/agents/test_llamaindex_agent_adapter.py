import unittest
from unittest.mock import patch, MagicMock, PropertyMock

from chorus.agents.llamaindex_agent_adapter import LlamaIndexAgentAdapter, LLAMAINDEX_AVAILABLE
from chorus.data.context import AgentContext
from chorus.data.dialog import Message, EventType
from chorus.util.testing_util import MockMessageClient


class TestLlamaIndexAgentAdapter(unittest.TestCase):
    """Test cases for the LlamaIndexAgentAdapter."""
    
    def setUp(self):
        """Set up the test environment."""
        # Mock the LLAMAINDEX_AVAILABLE flag to True for testing
        self.llamaindex_available_patcher = patch(
            'chorus.agents.llamaindex_agent_adapter.LLAMAINDEX_AVAILABLE', 
            True
        )
        self.llamaindex_available_patcher.start()
        
        # Mock the required llama_index modules
        self.llamaindex_modules_patcher = patch.dict('sys.modules', {
            'llama_index': MagicMock(),
            'llama_index.agent': MagicMock(),
            'llama_index.core.agent': MagicMock(),
            'llama_index.core.agent.workflow': MagicMock(),
            'llama_index.core.callbacks': MagicMock(),
            'llama_index.core.callbacks.base': MagicMock(),
        })
        self.llamaindex_modules_patcher.start()
        
        # Create a mock agent with a run method
        self.mock_agent = MagicMock()
        self.mock_agent.run.return_value = "This is a response from the LlamaIndex agent."
        # Make the agent have a .run method but not a .chat method
        type(self.mock_agent).chat = PropertyMock(side_effect=AttributeError)
        
        # Create a factory function that returns our mock agent
        def mock_agent_factory():
            return self.mock_agent
        
        # Create the LlamaIndexAgentAdapter with our mock factory
        self.agent = LlamaIndexAgentAdapter(
            agent_factory=mock_agent_factory,
            preserve_history=True
        ).name("llamaindex_agent")
        
        # Properly mock the _is_function_agent method to always return False in tests
        self.agent._is_function_agent = MagicMock(return_value=False)
        
        # Initialize the agent context
        self.context = AgentContext(agent_id=self.agent.identifier())
        self.context.message_client = MockMessageClient(self.agent.identifier())
        
        # Initialize the agent state
        self.state = self.agent.init_state()
    
    def tearDown(self):
        """Tear down the test environment."""
        self.llamaindex_available_patcher.stop()
        self.llamaindex_modules_patcher.stop()
    
    def test_initialization_check(self):
        """Test that the adapter checks for LlamaIndex availability during initialization."""
        # Mock LLAMAINDEX_AVAILABLE to False
        with patch('chorus.agents.llamaindex_agent_adapter.LLAMAINDEX_AVAILABLE', False):
            # Attempting to create an adapter should raise an ImportError
            with self.assertRaises(ImportError):
                LlamaIndexAgentAdapter(
                    agent_factory=lambda: None,
                    preserve_history=True
                )
    
    def test_respond_to_message_with_run(self):
        """Test that the agent responds to a message using the run method."""
        # Create a test message
        message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="Hello, can you help me?",
            event_type=EventType.MESSAGE
        )
        self.context.message_client.send_message(message)
        
        # Force the agent to be initialized
        self.agent._ensure_initialized()
        
        # Run the agent's respond method
        new_state = self.agent.respond(self.context, self.state, message)
        
        # Check that the agent's run method was called with the expected input
        self.mock_agent.run.assert_called_once()
        call_args = self.mock_agent.run.call_args[0][0]
        self.assertEqual(call_args, "Hello, can you help me?")
        
        # Check that the agent sent a response message
        outgoing_messages = self.context.message_client.filter_messages(
            source=self.agent.identifier(),
            destination="user"
        )
        self.assertEqual(len(outgoing_messages), 1)
        self.assertEqual(outgoing_messages[0].content, "This is a response from the LlamaIndex agent.")
    
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
        self.assertIn(conversation_id, new_state.llamaindex_memory)
        
        # Create and process a second message
        second_message = Message(
            source="user",
            destination=self.agent.identifier(),
            content="Second message",
            event_type=EventType.MESSAGE
        )
        final_state = self.agent.respond(self.context, new_state, second_message)
        
        # Verify that the history contains both conversations
        self.assertIn(conversation_id, final_state.llamaindex_memory)
        chat_history = final_state.llamaindex_memory[conversation_id].get("chat_history", [])
        self.assertEqual(len(chat_history), 2)
        self.assertEqual(chat_history[0][0], "First message")
        self.assertEqual(chat_history[1][0], "Second message")
    
    def test_error_handling(self):
        """Test that errors are handled properly."""
        # Set up the agent to raise an exception
        self.mock_agent.run.side_effect = Exception("Simulated error")
        
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
    
    def test_async_support_detection(self):
        """Test that the adapter correctly detects if a method is async."""
        # Mock the asyncio.iscoroutinefunction to control its behavior
        with patch('chorus.agents.llamaindex_agent_adapter.asyncio.iscoroutinefunction') as mock_is_async:
            # Test when the run method is async
            mock_is_async.return_value = True
            
            # Create a test message
            message = Message(
                source="user",
                destination=self.agent.identifier(),
                content="Hello, can you help me?",
                event_type=EventType.MESSAGE
            )
            
            # Also mock asyncio.get_event_loop to avoid actual event loop creation
            with patch('chorus.agents.llamaindex_agent_adapter.asyncio.get_event_loop') as mock_get_loop:
                # And mock run_until_complete
                mock_loop = MagicMock()
                mock_get_loop.return_value = mock_loop
                mock_loop.run_until_complete.return_value = "Async response"
                
                # Run the agent's respond method
                self.agent.respond(self.context, self.state, message)
                
                # Check that get_event_loop and run_until_complete were called
                mock_get_loop.assert_called()
                mock_loop.run_until_complete.assert_called()


if __name__ == "__main__":
    unittest.main() 