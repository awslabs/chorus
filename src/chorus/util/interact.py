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
from chorus.data.planner_output import PlannerOutput
from chorus.data.dialog import Role
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


def extract_relevant_interaction_history(
    context: AgentContext, inbound_message: Message
) -> List[Message]:
    history = []
    all_messages = context.message_service.fetch_all_messages()
    sender = inbound_message.source
    agent_id = context.agent_id
    for msg in all_messages:
        if msg.source == agent_id and msg.destination == sender:
            msg = msg.model_copy()
            if msg.role != Role.ACTION and msg.role != Role.OBSERVATION:
                msg.role = Role.BOT
            history.append(msg)
        if msg.source == sender and msg.destination == agent_id:
            msg = msg.model_copy()
            msg.role = Role.USER
            history.append(msg)
        if msg.message_id == inbound_message.message_id:
            break
    return history


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
        output_turns = [Message(role=Role.BOT, content=llm_response)]
    if planner is not None:
        output_turns = planner.process_output(context, state, interaction_history, output_turns)
    return output_turns


def orchestrate(
    context: AgentContext,
    state: AgentState,
    interaction_history: List[Message],
    prompter: InteractPrompter,
    lm: LanguageModelClient,
    auto_tool_execution: bool = True,
    planner: Optional[MultiAgentPlanner] = None,
    dynamic_message_loading: bool = False,
    multi_agent_tool_name: Optional[str] = None,
    multi_agent_finish_action: Optional[str] = None,
    tool_executor_class: Type[SimpleToolExecutor] = SimpleToolExecutor,
) -> List[Message]:
    """
    Choruste the interaction of an agent based on the interaction history.
    """
    if planner is not None:
        planner.prepare_agent_state(state)
    tools = context.get_tools()
    if tools is None:
        tools = []
    tool_action_map = {}
    for tool in tools:
        schema = tool.get_schema()
        for action in schema.actions:
            tool_action_map[(schema.tool_name, action.name)] = action

    if dynamic_message_loading:
        interaction_history = context.message_service.fetch_all_messages()

    output_turns = orchestrate_generate_turns(
        context, state, interaction_history, prompter, lm, planner
    )
    if dynamic_message_loading:
        for message in output_turns:
            if message.source is None:
                message.source = context.agent_id
        context.message_service.send_messages(output_turns)

    executor = tool_executor_class(tools, context)
    while output_turns and auto_tool_execution and output_turns[-1].role == Role.ACTION:
        actions = output_turns[-1].extract_actions()
        
        observations = []
        for action in actions:
            if (
                multi_agent_finish_action is not None
                and action.tool_name == multi_agent_tool_name
                and action.action_name == multi_agent_finish_action
            ):
                return output_turns

            # Print planning result
            if output_turns[-1].content is not None and "<plan>" in output_turns[-1].content:
                goal_content_match = re.search(
                    r"<goal>.*?</goal>", output_turns[-1].content, re.DOTALL
                )
                thinking_content_match = re.search(
                    r"<thinking>.*?</thinking>", output_turns[-1].content, re.DOTALL
                )
                plan_content_match = re.search(
                    r"<plan>.*?</plan>", output_turns[-1].content, re.DOTALL
                )
                steps_content_match = re.search(
                    r"<steps>.*?</steps>", output_turns[-1].content, re.DOTALL
                )
                print("===========================================")
                print(f"\033[1m[PLANNING RESULT] {context.agent_id}\033[0m")
                if thinking_content_match is not None:
                    print(thinking_content_match.group(0))
                if goal_content_match is not None:
                    print(goal_content_match.group(0))
                if plan_content_match is not None:
                    print(plan_content_match.group(0))
                if steps_content_match is not None:
                    print(steps_content_match.group(0))

            action = fix_action_param_type(tool_action_map, action)
            if chorus_logging_option("action"):
                logger.info(f"\033[1m[ACTION] {context.agent_id}\033[0m")
                logger.info(f"Tool: {action.tool_name}, Action: {action.action_name}, Parameters: {action.parameters}")
            if not action.tool_name.startswith("agent_") and action.action_name != "send_message":
                print(f"   ╰─>\033[1m[ACTION] {context.agent_id} triggered {action.tool_name}.{action.action_name} with following parameters:\033[0m")
                print(f"      {action.parameters}")
            
            observation = executor.execute(action)
            if chorus_logging_option("action"):
                logger.info(f"\033[1m[OBSERVATION] {context.agent_id}\033[0m")
                logger.info(observation)
            
            # Handle async execution immediately for any action
            if is_async_observation_data(observation):
                async_execution_id = observation.get("async_execution_id", None)
                assert async_execution_id is not None
                async_cache = context.get_async_execution_cache()
                last_message = interaction_history[-1]
                async_cache[async_execution_id] = AsyncExecutionRecord(
                    action_source=last_message.source,
                    action_channel=last_message.channel,
                    tool_use_id=action.tool_use_id
                )
                # Create observation turn for async action and return
                observation_turn = Message(
                    role=Role.OBSERVATION, 
                    observations=[ObservationData(data=observation, tool_use_id=action.tool_use_id)],
                    source=context.agent_id,
                    destination=context.agent_id
                )
                output_turns.append(observation_turn)
                if dynamic_message_loading:
                    context.message_service.send_message(observation_turn)
                return output_turns

            observations.append(ObservationData(data=observation, tool_use_id=action.tool_use_id))

        # Create single observation turn with all observations
        observation_turn = Message(
            role=Role.OBSERVATION,
            observations=observations,
            source=context.agent_id,
            destination=context.agent_id
        )
        output_turns.append(observation_turn)
        if dynamic_message_loading:
            context.message_service.send_message(observation_turn)

        # Handle multi-agent tool messages
        if multi_agent_tool_name is not None:
            non_multi_agent_actions = [a for a in actions if a.tool_name != multi_agent_tool_name]
            if non_multi_agent_actions:
                action_turn = output_turns[-2]
                action_turn.source = context.agent_id
                action_turn.destination = context.agent_id
                action_turn.role = Role.ACTION
                context.message_service.send_message(action_turn)
                observation_turn = output_turns[-1]
                observation_turn.source = context.agent_id
                observation_turn.destination = context.agent_id
                observation_turn.role = Role.OBSERVATION
                context.message_service.send_message(observation_turn)

        # Generate next turns
        if dynamic_message_loading:
            input_messages = context.message_service.fetch_all_messages()
        else:
            input_messages = interaction_history + output_turns
        parsed_turns = orchestrate_generate_turns(
            context, state, input_messages, prompter, lm, planner
        )
        output_turns.extend(parsed_turns)
        if dynamic_message_loading:
            for message in parsed_turns:
                if message.source is None:
                    message.source = context.agent_id
            context.message_service.send_messages(parsed_turns)

    return output_turns
