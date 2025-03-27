"""Tool chat prompter for Bedrock Converse API.

This module provides a prompter for handling conversations with tool usage through
Amazon Bedrock's Converse API. It handles formatting messages and tool calls into
the structured format expected by the API, and parsing responses back into messages.
"""

import json
from typing import List
from typing import Optional


from chorus.data.data_types import ActionData
from chorus.data.dialog import Message
from chorus.data.resource import Resource
from chorus.data.prompt import StructuredPrompt
from chorus.data.prompt import StructuredCompletion
from chorus.data.toolschema import ToolSchema
from chorus.prompters.interact import InteractPrompter
from chorus.data.dialog import EventType

TOOL_ACTION_SEPARATOR = "__"

class BedrockConverseToolChatPrompter(InteractPrompter[StructuredCompletion]):
    """Prompter for tool-enabled chat using Bedrock Converse API.

    This prompter handles formatting messages and tool calls into the structured format
    expected by Amazon Bedrock's Converse API, and parsing responses back into messages.
    It supports tool usage by formatting tool schemas and actions according to the API's
    requirements.
    """

    def __init__(self, add_output_schema: bool = False):
        """Initialize the BedrockConverseToolChatPrompter.

        Args:
            add_output_schema: Whether to add output schema to tool definitions.
        """
        super().__init__()
        self._add_output_schema = add_output_schema

    def _get_action_dict(self, action: ActionData):
        """Convert an ActionData object into a Bedrock Converse tool use dictionary.

        Args:
            action: The ActionData object to convert.

        Returns:
            A dictionary containing the tool use formatted for Bedrock Converse.
        """
        action_name = action.tool_name
        if action.action_name is not None:
            action_name += f"{TOOL_ACTION_SEPARATOR}{action.action_name}"
        tool_use_dict = {
            "toolUse": {
                "toolUseId": action.tool_use_id,
                "name": action_name,
                "input": action.parameters
            }
        }
        return tool_use_dict

    def get_prompt(
        self,
        current_agent_id: str,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        agent_instruction: Optional[str] = None,
        resources: Optional[List[Resource]] = None,
        reference_time: Optional[str] = None,
        planner_instruction: Optional[str] = None,
    ) -> StructuredPrompt:
        """Generate a structured prompt for the Bedrock Converse API.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of tool schemas defining available tools.
            agent_instruction: Optional instruction text for the agent.
            resources: Optional list of resources available to the agent.
            reference_time: Optional reference time for the conversation.
            planner_instruction: Optional planning instruction for multi-agent scenarios.

        Returns:
            A StructuredPrompt formatted for the Bedrock Converse API.
        """

        # Create tool config
        tool_config: Optional[dict] = None
        if tools:
            tool_config = {"tools": []}
            for tool_schema in tools:
                for action in tool_schema.actions:
                    tool_use_name = f"{tool_schema.name}{TOOL_ACTION_SEPARATOR}{action.name}"
                    tool_use_description = action.description
                    tool_use_schema = action.input_schema
                    tool_config["tools"].append(
                        {
                            "toolSpec":{
                                "name": tool_use_name,
                                "description": tool_use_description,
                                "inputSchema": {
                                    "json": json.loads(tool_use_schema.model_dump_json(exclude_none=True, by_alias=True))
                                }
                            }
                        }
                    )
        # Create system prompt
        system_instruction = agent_instruction if agent_instruction is not None else ""

        if planner_instruction is not None:
            system_instruction += f"\n\n{planner_instruction}"

        converse_messages = []            
        for message in messages:
            role = None
            content: Optional[list] = None
            is_internal = message.event_type == EventType.INTERNAL_EVENT
            is_from_myself = message.source == current_agent_id
            
            if not is_internal and not is_from_myself:
                role = "user"
                content = [
                    {
                        "text": message.content
                    }
                ]
            elif not is_internal and is_from_myself:
                role = "assistant"
                content = [
                    {
                        "text": message.content
                    }
                ]
            elif is_internal and message.actions:
                role = "assistant"
                content = []
                if message.actions:
                    for action_data in message.actions:
                        content.append(self._get_action_dict(action_data))
                if message.content is not None:
                    content.append({"text": message.content})
            elif is_internal and message.observations:
                role = "user"
                content = []
                observation_content: List = []
                for observation in message.observations:
                    if type(observation.data) == str:
                        observation_content = [
                            {"text": observation.data}
                        ]
                    else:
                        observation_content = [
                            {"json": observation.data}
                        ]
                    content.append({
                        "toolResult": {
                            "toolUseId": observation.tool_use_id,
                            "content": observation_content
                        }
                    })
            if role is None:
                continue
            converse_messages.append({"role": role, "content": content})
        if converse_messages and converse_messages[0]["role"] == "assistant":
            converse_messages.pop(0)
        if system_instruction:
            system = [
                {"text": system_instruction}
            ]
        else:
            system = None
        prompt_dict: dict = {
            "messages": converse_messages,
        }
        if system is not None:
            prompt_dict["system"] = system
        if tool_config is not None:
            prompt_dict["toolConfig"] = tool_config

        return StructuredPrompt.from_dict(prompt_dict)

    def get_target(
        self,
        current_agent_id: str,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        agent_instruction: Optional[str] = None,
        resources: Optional[List[Resource]] = None,
        reference_time: Optional[str] = None,
    ):
        """Not implemented for this prompter.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of tool schemas.
            agent_instruction: Optional instruction text.
            resources: Optional list of resources.
            reference_time: Optional reference time.

        Raises:
            NotImplementedError: This method is not implemented.
        """
        raise NotImplementedError()

    def parse_generation(self, completion: StructuredCompletion) -> List[Message]:
        """Parse a completion from Bedrock Converse into messages.

        Args:
            completion: The StructuredCompletion from Bedrock Converse.

        Returns:
            A list containing the parsed Message.

        Raises:
            ValueError: If the completion doesn't contain a message.
        """
        completion_dict = completion.to_dict()
        if "message" not in completion_dict:
            raise ValueError(f"Can't find message in completion: {completion_dict}")
        text_responses = []
        actions = []
        for response_item in completion_dict["message"]["content"]:
            if "toolUse" in response_item:
                tool_use_id = response_item["toolUse"]["toolUseId"]
                tool_use_name = response_item["toolUse"]["name"]
                tool_use_input = response_item["toolUse"]["input"]
                if TOOL_ACTION_SEPARATOR in tool_use_name:
                    tool_name, action_name = tool_use_name.split(TOOL_ACTION_SEPARATOR, maxsplit=1)
                else:
                    tool_name = tool_use_name
                    action_name = None
                action = ActionData(
                    tool_name=tool_name,
                    action_name=action_name,
                    parameters=tool_use_input,
                    tool_use_id=tool_use_id,
                )
                actions.append(action)
            elif "text" in response_item:
                text_responses.append(response_item["text"])
        if actions:
            message = Message(event_type=EventType.INTERNAL_EVENT, actions=actions)
            if text_responses:
                message.content = "\n".join(text_responses)
        else:
            message = Message(event_type=EventType.MESSAGE, content="\n".join(text_responses))
        return [message]