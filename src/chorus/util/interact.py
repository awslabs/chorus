import json
import logging
import re
from typing import Callable
from typing import List
from typing import Optional
from typing import Type

from chorus.data.data_types import ActionData, ObservationData
from chorus.data.context import AgentContext
from chorus.data.state import AgentState
from chorus.data.dialog import Message
from chorus.data.dialog import EventType
from chorus.data.planner_output import PlannerOutput
from chorus.data.prompt import StructuredPrompt
from chorus.data.context import AsyncExecutionRecord
from chorus.data.state import PassiveAgentState
from chorus.executors import SimpleToolExecutor
from chorus.lms import LanguageModelClient
from chorus.planners.base import MultiAgentPlanner
from chorus.prompters import InteractPrompter
from chorus.util.async_actions import is_async_observation_data
from chorus.util.logging import chorus_logging_option

logger = logging.getLogger(__name__)


def fix_action_param_type(tool_action_map: dict, action: ActionData):
    action_schema = tool_action_map.get((action.tool_name, action.action_name), None)
    if action_schema is None:
        return action
    input_schema = action_schema.input_schema.model_dump()
    for parameter_key, parameter_schema in input_schema.get("properties", {}).items():
        if parameter_key in action.parameters and parameter_schema["data_type"] in (
            "number",
            "integer",
        ):
            action.parameters[parameter_key] = int(action.parameters[parameter_key])
    return action


def orchestrate_generate_turns(
    context: AgentContext,
    state: AgentState,
    interaction_history: List[Message],
    prompter: InteractPrompter,
    lm: LanguageModelClient,
    planner: Optional[MultiAgentPlanner] = None,
) -> List[Message]:
    agent_instruction = context.get_agent_instruction()
    reference_datetime = context.get_current_datetime()
    resources = context.get_resources()
    tool_schemas = [tool.get_schema() for tool in context.get_tools()]

    # Call planner
    if planner is not None:
        planner_output = planner.plan(context, state, interaction_history)
        if planner_output.agent_instruction is not None:
            agent_instruction = planner_output.agent_instruction
        if planner_output.messages is not None:
            interaction_history = planner_output.messages
        if planner_output.tool_schemas is not None:
            tool_schemas = planner_output.tool_schemas
        planner_instruction = planner_output.planner_instruction
    else:
        planner_instruction = None

    prompt = prompter.get_prompt(
        current_agent_id=context.agent_id,
        messages=interaction_history,
        tools=tool_schemas,
        agent_instruction=agent_instruction,
        resources=resources,
        reference_time=reference_datetime,
        planner_instruction=planner_instruction,
    )
    try:
        llm_response = lm.generate(prompt)
    except Exception as e:
        logger.info(f"==== PROMPT inside {context.agent_id} ====")
        if isinstance(prompt, StructuredPrompt):
            logger.info(json.dumps(prompt.to_dict(), indent=2))
        else:
            logger.info(str(prompt))
        logger.info("--->")
        logger.info("ERROR")
        logger.info("==== *** ====")
        raise e
    logger.info(f"==== PROMPT inside {context.agent_id} ====")
    if isinstance(prompt, StructuredPrompt):
        logger.info(json.dumps(prompt.to_dict(), indent=2))
    else:
        logger.info(str(prompt))
    logger.info("--->")
    logger.info(llm_response)
    logger.info("==== *** ====")

    output_turns = prompter.parse_generation(llm_response)
    if not output_turns:
        # todo: check
        output_turns = [Message(event_type=EventType.MESSAGE, content=llm_response)]
    if planner is not None:
        output_turns = planner.process_output(context, state, interaction_history, output_turns)
    return output_turns


def orchestrate_generate_next_actions(
    context: AgentContext,
    state: AgentState,
    interaction_history: List[Message],
    prompter: InteractPrompter,
    lm: LanguageModelClient,
    planner: Optional[MultiAgentPlanner] = None,
) -> List[Message]:
    """
    Generate the next actions for an agent based on the interaction history.
    
    Args:
        context: The agent's context containing tools and other configuration
        state: The current agent state
        interaction_history: The history of interactions with the agent
        prompter: The prompter to use for generating the prompt
        lm: The language model client to use for generating text
        planner: Optional planner for planning solutions
        
    Returns:
        A list of messages representing the agent's next actions
    """
    # Initialize planner if provided
    if planner is not None:
        planner.prepare_agent_state(state)

    # Generate response turns from the LLM
    output_turns = orchestrate_generate_turns(
        context, state, interaction_history, prompter, lm, planner
    )
                
    return output_turns


def orchestrate_execute_actions(
    context: AgentContext,
    action_message: Message,
    executor: SimpleToolExecutor,
) -> Optional[Message]:
    """
    Execute the actions generated by the agent and return the resulting observations.
    
    Args:
        context: The agent's context containing tools and other configuration
        action_message: The message containing the actions to execute
        executor: The tool executor to use for executing actions
    Returns:
        A message containing the observations from executing the actions
    """
    if not action_message.actions:
        return None
    
    # Create a mapping of tool actions for easy lookup
    tool_action_map = {}
    for tool in context.get_tools():
        schema = tool.get_schema()
        for action in schema.actions:
            tool_action_map[(schema.tool_name, action.name)] = action
    
    # Extract actions from the last message
    actions = action_message.extract_actions()
    
    observations = []
    for action in actions:
        # Fix parameter types for the action
        action = fix_action_param_type(tool_action_map, action)
        
        # Log action details if action logging is enabled
        if chorus_logging_option("action"):
            logger.info(f"\033[1m[ACTION] {context.agent_id}\033[0m")
            logger.info(f"Tool: {action.tool_name}, Action: {action.action_name}, Parameters: {action.parameters}")
        
        # Print non-agent actions to console for visibility
        if not action.tool_name.startswith("agent_") and action.action_name != "send_message":
            print(f"   ╰─>\033[1m[ACTION] {context.agent_id} triggered {action.tool_name}.{action.action_name} with following parameters:\033[0m")
            print(f"      {action.parameters}")
        
        # Execute the action using the tool executor
        observation = executor.execute(action)
        
        # Log observation if action logging is enabled
        if chorus_logging_option("action"):
            logger.info(f"\033[1m[OBSERVATION] {context.agent_id}\033[0m")
            logger.info(observation)
        
        # Special handling for asynchronous actions
        if is_async_observation_data(observation):
            # Extract and validate async execution ID
            async_execution_id = observation.get("async_execution_id", None)
            assert async_execution_id is not None
            
            # Store execution record in the async cache
            async_cache = context.get_async_execution_cache()
            async_cache[async_execution_id] = AsyncExecutionRecord(
                action_source=action_message.source,
                action_channel=action_message.channel,
                tool_use_id=action.tool_use_id
            )
            
            # Create observation message for the async action
            observation_turn = Message(
                event_type=EventType.INTERNAL_EVENT, 
                observations=[ObservationData(data=observation, tool_use_id=action.tool_use_id)],
                source=context.agent_id,
                destination=context.agent_id
            )
            
            # Return early for async actions
            return observation_turn

        # Add observation to the list for synchronous actions
        observations.append(ObservationData(data=observation, tool_use_id=action.tool_use_id))

    # Create a single message containing all observations
    observation_turn = Message(
        event_type=EventType.INTERNAL_EVENT,
        observations=observations,
        source=context.agent_id,
        destination=context.agent_id
    )
    return observation_turn
