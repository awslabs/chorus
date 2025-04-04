import pytest
import unittest
from unittest.mock import Mock, MagicMock

from chorus.data import (
    Message,
    EventType,
    ActionData,
    ObservationData,
    AgentContext,
    AgentState,
)
from chorus.util.interact import orchestrate_generate_next_actions, orchestrate_execute_actions
from chorus.executors import SimpleToolExecutor
from chorus.prompters import InteractPrompter
from chorus.data.executable_tool import ExecutableTool


class TestOrchestrate(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_context = MagicMock(spec=AgentContext)
        self.mock_state = MagicMock(spec=AgentState)
        self.mock_prompter = MagicMock(spec=InteractPrompter)
        self.mock_lm = MagicMock()
        
        # Setup mock tools that properly inherit from ExecutableTool
        self.mock_tool1 = MagicMock(spec=ExecutableTool)
        self.mock_tool1.get_schema.return_value.tool_name = "tool1"
        self.mock_tool1.get_schema.return_value.actions = [
            MagicMock(name="action1", input_schema=MagicMock(model_dump=lambda: {"properties": {}}))
        ]
        
        self.mock_tool2 = MagicMock(spec=ExecutableTool)
        self.mock_tool2.get_schema.return_value.tool_name = "tool2"
        self.mock_tool2.get_schema.return_value.actions = [
            MagicMock(name="action2", input_schema=MagicMock(model_dump=lambda: {"properties": {}}))
        ]
        
        self.mock_context.get_tools.return_value = [self.mock_tool1, self.mock_tool2]
        self.mock_context.agent_id = "test_agent"
        
        # Setup initial interaction history
        self.interaction_history = [
            Message(event_type=EventType.MESSAGE, content="Execute multiple actions")
        ]
        
        # Mock tool execution results
        def mock_execute(action):
            if action.tool_name == "tool1":
                return {"result": "tool1 executed"}
            else:
                return {"result": "tool2 executed"}
        
        self.mock_executor = MagicMock(spec=SimpleToolExecutor)
        self.mock_executor.execute.side_effect = mock_execute

    def test_orchestrate_multiple_actions(self):
        # Track number of LLM calls to return different responses
        call_count = 0
        def generate_turns_side_effect(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First response: return multiple actions
                return "I'll execute two actions.\n<action>\ntool1.action1 {}\ntool2.action2 {}\n</action>"
            else:
                # Subsequent response: return a completion message
                return "All actions have been executed successfully."
        
        self.mock_lm.generate.side_effect = generate_turns_side_effect
        
        # Track number of prompter parse calls
        parse_call_count = 0
        def parse_generation_side_effect(response):
            nonlocal parse_call_count
            parse_call_count += 1
            if parse_call_count == 1:
                # First parse: return action message
                return [
                    Message(
                        event_type=EventType.INTERNAL_EVENT,
                        actions=[
                            ActionData(
                                tool_name="tool1",
                                action_name="action1",
                                parameters={},
                                tool_use_id="1"
                            ),
                            ActionData(
                                tool_name="tool2",
                                action_name="action2",
                                parameters={},
                                tool_use_id="2"
                            )
                        ]
                    )
                ]
            else:
                # Subsequent parse: return completion message
                return [Message(event_type=EventType.MESSAGE, content="All actions have been executed successfully.")]
        
        self.mock_prompter.parse_generation.side_effect = parse_generation_side_effect
        
        # Get available tools from context
        tools = self.mock_context.get_tools()
        if tools is None:
            tools = []
        
        # Create a mapping of tool actions for easy lookup
        tool_action_map = {}
        for tool in tools:
            schema = tool.get_schema()
            for action in schema.actions:
                tool_action_map[(schema.tool_name, action.name)] = action
        
        # Use our mock_executor instead of creating a new one
        executor = self.mock_executor
        
        # Generate next actions
        output_turns = orchestrate_generate_next_actions(
            context=self.mock_context,
            state=self.mock_state,
            interaction_history=self.interaction_history,
            prompter=self.mock_prompter,
            lm=self.mock_lm,
        )
        
        # Execute the actions
        observation_message = orchestrate_execute_actions(
            context=self.mock_context,
            action_message=output_turns[-1],
            executor=executor,
        )
        
        # Now manually call orchestrate_generate_next_actions again to get completion message
        output_turns.append(observation_message)
        updated_history = self.interaction_history + output_turns
        follow_up_turns = orchestrate_generate_next_actions(
            context=self.mock_context,
            state=self.mock_state,
            interaction_history=updated_history,
            prompter=self.mock_prompter,
            lm=self.mock_lm,
        )
        output_turns.extend(follow_up_turns)
        
        # Verify the results
        self.assertGreaterEqual(len(output_turns), 3)  # Should have action, observation, and completion messages
        
        # Verify that both actions were executed
        self.assertEqual(self.mock_executor.execute.call_count, 2)
        
        # Get messages by role
        action_messages = [m for m in output_turns if m.actions]
        observation_messages = [m for m in output_turns if m.observations]
        completion_messages = [m for m in output_turns if m.event_type == EventType.MESSAGE and not m.actions and not m.observations]
        
        # Verify action message
        self.assertEqual(len(action_messages), 1)
        self.assertEqual(len(action_messages[0].actions), 2)
        
        # Verify observation message
        self.assertEqual(len(observation_messages), 1)
        observation_message = observation_messages[0]
        self.assertEqual(len(observation_message.observations), 2)
        
        # Verify the observation data
        self.assertEqual(observation_message.observations[0].data, {"result": "tool1 executed"})
        self.assertEqual(observation_message.observations[1].data, {"result": "tool2 executed"})
        
        # Verify tool_use_ids are preserved
        self.assertEqual(observation_message.observations[0].tool_use_id, "1")
        self.assertEqual(observation_message.observations[1].tool_use_id, "2")
        
        # Verify completion message
        self.assertEqual(len(completion_messages), 1)
        self.assertEqual(completion_messages[0].content, "All actions have been executed successfully.")

if __name__ == '__main__':
    unittest.main() 