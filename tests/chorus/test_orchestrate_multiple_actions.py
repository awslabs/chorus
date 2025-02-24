import pytest
from unittest.mock import Mock, MagicMock

from chorus.data import (
    Message,
    Role,
    ActionData,
    ObservationData,
    AgentContext,
    AgentState,
)
from chorus.util.interact import orchestrate
from chorus.executors import SimpleToolExecutor
from chorus.prompters import InteractPrompter


def test_orchestrate_multiple_actions():
    # Mock dependencies
    mock_context = MagicMock(spec=AgentContext)
    mock_state = MagicMock(spec=AgentState)
    mock_prompter = MagicMock(spec=InteractPrompter)
    mock_lm = MagicMock()
    
    # Setup mock tools
    mock_tool1 = MagicMock()
    mock_tool1.get_schema.return_value.tool_name = "tool1"
    mock_tool1.get_schema.return_value.actions = [
        MagicMock(name="action1", input_schema=MagicMock(model_dump=lambda: {"properties": {}}))
    ]
    
    mock_tool2 = MagicMock()
    mock_tool2.get_schema.return_value.tool_name = "tool2"
    mock_tool2.get_schema.return_value.actions = [
        MagicMock(name="action2", input_schema=MagicMock(model_dump=lambda: {"properties": {}}))
    ]
    
    mock_context.get_tools.return_value = [mock_tool1, mock_tool2]
    mock_context.agent_id = "test_agent"
    
    # Setup initial interaction history
    interaction_history = [
        Message(role=Role.USER, content="Execute multiple actions")
    ]
    
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
    
    mock_lm.generate.side_effect = generate_turns_side_effect
    
    # Track number of prompter parse calls
    parse_call_count = 0
    def parse_generation_side_effect(response):
        nonlocal parse_call_count
        parse_call_count += 1
        if parse_call_count == 1:
            # First parse: return action message
            return [
                Message(
                    role=Role.ACTION,
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
            return [Message(role=Role.BOT, content="All actions have been executed successfully.")]
    
    mock_prompter.parse_generation.side_effect = parse_generation_side_effect
    
    # Mock tool execution results
    def mock_execute(action):
        if action.tool_name == "tool1":
            return {"result": "tool1 executed"}
        else:
            return {"result": "tool2 executed"}
    
    mock_executor = MagicMock(spec=SimpleToolExecutor)
    mock_executor.execute.side_effect = mock_execute
    
    # Execute orchestrate function
    output_turns = orchestrate(
        context=mock_context,
        state=mock_state,
        interaction_history=interaction_history,
        prompter=mock_prompter,
        lm=mock_lm,
        auto_tool_execution=True,
        tool_executor_class=lambda *args: mock_executor
    )
    
    # Verify the results
    assert len(output_turns) >= 3  # Should have action, observation, and completion messages
    
    # Verify that both actions were executed
    assert mock_executor.execute.call_count == 2
    
    # Get messages by role
    action_messages = [m for m in output_turns if m.role == Role.ACTION]
    observation_messages = [m for m in output_turns if m.role == Role.OBSERVATION]
    completion_messages = [m for m in output_turns if m.role == Role.BOT]
    
    # Verify action message
    assert len(action_messages) == 1
    assert len(action_messages[0].actions) == 2
    
    # Verify observation message
    assert len(observation_messages) == 1
    observation_message = observation_messages[0]
    assert len(observation_message.observations) == 2
    
    # Verify the observation data
    assert observation_message.observations[0].data == {"result": "tool1 executed"}
    assert observation_message.observations[1].data == {"result": "tool2 executed"}
    
    # Verify tool_use_ids are preserved
    assert observation_message.observations[0].tool_use_id == "1"
    assert observation_message.observations[1].tool_use_id == "2"
    
    # Verify completion message
    assert len(completion_messages) == 1
    assert completion_messages[0].content == "All actions have been executed successfully." 