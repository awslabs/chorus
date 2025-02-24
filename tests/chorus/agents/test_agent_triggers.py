import unittest
from unittest.mock import MagicMock, patch, PropertyMock

from chorus.agents import ToolChatAgent
from chorus.data.trigger import MessageTrigger
from chorus.data.dialog import Message, Role
from chorus.data.context import ChorustionContext, AgentContext
from chorus.data.executable_tool import ExecutableTool
from chorus.data.channel import Channel
from chorus.data.prompt import StructuredCompletion
from chorus.prompters.interact.bedrock_converse_tool_chat import BedrockConverseToolChatPrompter


class MockContext(MagicMock):
    """Custom mock class to handle context attribute updates."""
    def __init__(self, *args, **kwargs):
        instruction = kwargs.pop('instruction', "Test instruction")
        super().__init__(*args, **kwargs)
        # Store the instruction value after super init
        object.__setattr__(self, '_instruction', instruction)
        # Set up the property mock after super init
        self._setup_instruction_property()

    def _setup_instruction_property(self):
        """Set up the instruction property mock."""
        def instruction_getter(instance):
            return instance._instruction
        def instruction_setter(instance, value):
            object.__setattr__(instance, '_instruction', value)
        # Create a property for agent_instruction
        type(self).agent_instruction = property(instruction_getter, instruction_setter)

    def __getattr__(self, name):
        if name == '_instruction':
            return object.__getattribute__(self, '_instruction')
        return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name == '_instruction':
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)


class TestAgentTriggers(unittest.TestCase):
    def setUp(self):
        # Create mock tools
        self.mock_tool = MagicMock(spec=ExecutableTool)
        self.mock_tool.get_schema.return_value.tool_name = "test_tool"

        # Create test contexts
        self.default_context = ChorustionContext(
            agent_instruction="Default mode instruction",
            tools=[self.mock_tool]
        )

        self.special_context = ChorustionContext(
            agent_instruction="Special mode instruction",
            tools=[self.mock_tool]
        )

        # Mock the language model client
        self.mock_lm = MagicMock()
        self.mock_lm.generate.return_value = StructuredCompletion('{"message": {"role": "assistant", "content": "Test response"}}')

        # Create test agent with mocked LM and prompter
        self.agent = ToolChatAgent(
            name="TestAgent",
            instruction="Test instruction",
            tools=[self.mock_tool],
            lm=self.mock_lm,
            prompter=BedrockConverseToolChatPrompter()
        )

        # Create test channel
        self.test_channel = Channel(
            name="test_channel",
            members=["TestAgent", "OtherAgent"]
        )

    def setup_mock_context(self, instruction="Test instruction"):
        """Helper method to create a properly mocked agent context."""
        mock_context = MockContext(spec=AgentContext, instruction=instruction)
        mock_context.agent_id = "TestAgent"
        mock_context.message_service = MagicMock()
        
        # Mock methods to return JSON-serializable values
        mock_context.get_agent_instruction = lambda: mock_context.agent_instruction
        mock_context.get_tools.return_value = []
        mock_context.get_resources.return_value = []
        mock_context.get_views.return_value = []
        mock_context.get_current_datetime.return_value = None
        mock_context.get_async_execution_cache.return_value = {}
        
        # Mock properties to be JSON-serializable
        type(mock_context).tools = PropertyMock(return_value=[])
        type(mock_context).resources = PropertyMock(return_value=[])
        type(mock_context).views = PropertyMock(return_value=[])
        type(mock_context).artifacts = PropertyMock(return_value={})
        
        return mock_context

    def test_trigger_registration(self):
        """Test that triggers can be registered and removed correctly."""
        # Create a trigger
        trigger = MessageTrigger(source="OtherAgent")
        
        # Register trigger
        self.agent.on(trigger, self.special_context)
        
        # Verify trigger was added
        self.assertEqual(len(self.agent._context_switchers), 1)
        self.assertEqual(self.agent._context_switchers[0][0], trigger)
        self.assertEqual(self.agent._context_switchers[0][1], self.special_context)
        
        # Remove trigger
        self.agent.remove_trigger(trigger, self.special_context)
        
        # Verify trigger was removed
        self.assertEqual(len(self.agent._context_switchers), 0)

    def test_context_switching_on_message(self):
        """Test that context switches correctly when a matching message is received."""
        # Create triggers
        direct_trigger = MessageTrigger(source="OtherAgent", destination="TestAgent")
        channel_trigger = MessageTrigger(channel="test_channel")

        # Register triggers
        self.agent.on(direct_trigger, self.special_context)
        self.agent.on(channel_trigger, self.default_context)

        # Create a mock agent context
        mock_agent_context = self.setup_mock_context()

        # Test direct message trigger
        direct_message = Message(
            source="OtherAgent",
            destination="TestAgent",
            content="Test message",
            role=Role.USER
        )
        
        # Mock extract_relevant_interaction_history to return a list with our message
        with patch('chorus.util.interact.extract_relevant_interaction_history') as mock_extract:
            mock_extract.return_value = [direct_message]
            self.agent.respond(mock_agent_context, None, direct_message)

            # Verify context was updated with special context
            mock_agent_context.message_service.send_messages.assert_called()
            # Verify the agent instruction was updated
            self.assertEqual(
                mock_agent_context.agent_instruction,
                self.special_context.agent_instruction
            )

        # Reset mock
        mock_agent_context = self.setup_mock_context()

        # Test channel message trigger
        channel_message = Message(
            source="OtherAgent",
            channel="test_channel",
            content="Test channel message",
            role=Role.USER
        )
        
        with patch('chorus.util.interact.extract_relevant_interaction_history') as mock_extract:
            mock_extract.return_value = [channel_message]
            self.agent.respond(mock_agent_context, None, channel_message)

            # Verify context was updated with default context
            mock_agent_context.message_service.send_messages.assert_called()
            # Verify the agent instruction was updated
            self.assertEqual(
                mock_agent_context.agent_instruction,
                self.default_context.agent_instruction
            )

    def test_trigger_priority(self):
        """Test that triggers are evaluated in the correct order (last registered first)."""
        # Create triggers with overlapping conditions
        general_trigger = MessageTrigger(source="OtherAgent")
        specific_trigger = MessageTrigger(source="OtherAgent", destination="TestAgent")

        # Create contexts with distinct instructions
        general_context = ChorustionContext(agent_instruction="General instruction")
        specific_context = ChorustionContext(agent_instruction="Specific instruction")

        # Register triggers in order (specific last)
        self.agent.on(general_trigger, general_context)
        self.agent.on(specific_trigger, specific_context)

        # Create a mock agent context
        mock_agent_context = self.setup_mock_context()

        # Create a message that matches both triggers
        test_message = Message(
            source="OtherAgent",
            destination="TestAgent",
            content="Test message",
            role=Role.USER
        )

        # Test response with mocked interaction history
        with patch('chorus.util.interact.extract_relevant_interaction_history') as mock_extract:
            mock_extract.return_value = [test_message]
            self.agent.respond(mock_agent_context, None, test_message)

            # Verify the specific trigger's context was used (last registered)
            self.assertEqual(
                mock_agent_context.agent_instruction,
                specific_context.agent_instruction
            )

    def test_no_matching_trigger(self):
        """Test that the agent maintains its current context when no triggers match."""
        # Create a trigger that won't match our test message
        trigger = MessageTrigger(source="NonexistentAgent")
        self.agent.on(trigger, self.special_context)

        # Create a mock agent context with original instruction
        original_instruction = "Original instruction"
        mock_agent_context = self.setup_mock_context(instruction=original_instruction)

        # Create a message that doesn't match the trigger
        test_message = Message(
            source="OtherAgent",
            destination="TestAgent",
            content="Test message",
            role=Role.USER
        )

        # Test response with mocked interaction history
        with patch('chorus.util.interact.extract_relevant_interaction_history') as mock_extract:
            mock_extract.return_value = [test_message]
            self.agent.respond(mock_agent_context, None, test_message)

            # Verify the instruction wasn't changed
            self.assertEqual(
                mock_agent_context.agent_instruction,
                original_instruction
            )
