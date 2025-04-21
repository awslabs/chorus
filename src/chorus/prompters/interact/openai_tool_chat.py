"""Tool chat prompter for OpenAI Chat API.

This module provides a prompter for handling conversations with tool usage through
OpenAI's Chat API. It handles formatting messages and tool calls into
the structured format expected by the API, and parsing responses back into messages.
"""

import json
from typing import List
from typing import Optional, Dict

from chorus.data.data_types import ActionData
from chorus.data.dialog import Message
from chorus.data.resource import Resource
from chorus.data.prompt import StructuredPrompt
from chorus.data.prompt import StructuredCompletion
from chorus.data.toolschema import ToolSchema
from chorus.prompters.interact import InteractPrompter
from chorus.data.dialog import EventType

TOOL_ACTION_SEPARATOR = "__"

class OpenAIToolChatPrompter(InteractPrompter[StructuredCompletion]):
    """Prompter for tool-enabled chat using OpenAI Chat API.

    This prompter handles formatting messages and tool calls into the structured format
    expected by OpenAI's API, and parsing responses back into messages.
    It supports tool usage by formatting tool schemas and actions according to the API's
    requirements.
    """

    def __init__(self):
        """Initialize the OpenAIToolChatPrompter."""
        super().__init__()

    def _get_action_dict(self, action: ActionData) -> Dict:
        """Convert an ActionData object into an OpenAI function call dictionary.

        Args:
            action: The ActionData object to convert.

        Returns:
            A dictionary containing the function call formatted for OpenAI Chat API.
        """
        action_name = action.tool_name
        if action.action_name is not None:
            action_name += f"{TOOL_ACTION_SEPARATOR}{action.action_name}"
            
        return {
            "type": "function",
            "function": {
                "name": action_name,
                "arguments": json.dumps(action.parameters)
            }
        }

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
        """Generate a structured prompt for the OpenAI Chat API.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of tool schemas defining available tools.
            agent_instruction: Optional instruction text for the agent.
            resources: Optional list of resources available to the agent.
            reference_time: Optional reference time for the conversation.
            planner_instruction: Optional planning instruction for multi-agent scenarios.

        Returns:
            A StructuredPrompt formatted for the OpenAI Chat API.
        """
        # Create tool config
        openai_tools = []
        if tools:
            for tool_schema in tools:
                for action in tool_schema.actions:
                    tool_use_name = f"{tool_schema.name}{TOOL_ACTION_SEPARATOR}{action.name}"
                    tool_use_description = action.description
                    
                    # Convert the JSON schema to the format OpenAI expects
                    properties = {}
                    required = []
                    
                    if hasattr(action.input_schema, "properties"):
                        schema_dict = json.loads(action.input_schema.model_dump_json(exclude_none=True, by_alias=True))
                        properties = schema_dict.get("properties", {})
                        required = schema_dict.get("required", [])
                    
                    openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool_use_name,
                            "description": tool_use_description,
                            "parameters": {
                                "type": "object",
                                "properties": properties,
                                "required": required
                            }
                        }
                    })

        # Create formatted messages for OpenAI
        openai_messages = []
        
        # Add system message if provided
        system_instruction = agent_instruction if agent_instruction is not None else ""
        if planner_instruction is not None:
            system_instruction += f"\n\n{planner_instruction}"
            
        if system_instruction:
            openai_messages.append({
                "role": "system",
                "content": system_instruction
            })
        tool_id_to_name_map = {}
            
        # Process conversation messages
        for message in messages:
            # Skip messages without a clear role
            role = None
            content = None
            is_internal = message.event_type == EventType.INTERNAL_EVENT
            is_from_myself = message.source == current_agent_id
            
            if not is_internal and not is_from_myself:
                # Regular user message
                role = "user"
                content = message.content
                
            elif not is_internal and is_from_myself:
                # Regular assistant message
                role = "assistant"
                content = message.content
                
            elif is_internal and message.actions:
                # Function/tool call from assistant
                role = "assistant"
                tool_calls = []
                
                for action_data in message.actions:
                    action_name = action_data.tool_name
                    if action_data.action_name is not None:
                        action_name += f"{TOOL_ACTION_SEPARATOR}{action_data.action_name}"
                        
                    tool_calls.append({
                        "id": action_data.tool_use_id,
                        "function": {
                            "name": action_name,
                            "arguments": json.dumps(action_data.parameters)
                        },
                        "type": "function"
                    })
                    if action_data.tool_use_id:
                        tool_id_to_name_map[action_data.tool_use_id] = action_name

                    
                openai_messages.append({
                    "role": "assistant",
                    "content": message.content if message.content else "",
                    "tool_calls": tool_calls
                })
                continue
                
            elif is_internal and message.observations:
                # Function/tool result from user
                role = "tool"
                
                for observation in message.observations:
                    # Use tool_use_id as the name for the function result
                    result_content = ""
                    if isinstance(observation.data, str):
                        result_content = observation.data
                    else:
                        result_content = json.dumps(observation.data)
                        
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": observation.tool_use_id or "",
                        "name": tool_id_to_name_map.get(observation.tool_use_id, ""),
                        "content": result_content
                    })
                    
                continue
                
            # Skip if no valid role was determined
            if role is None:
                continue
                
            # Add the message
            openai_messages.append({
                "role": role,
                "content": content
            })
            
        # Create the final prompt dictionary
        prompt_dict = {
            "messages": openai_messages
        }
        
        if openai_tools:
            prompt_dict["tools"] = openai_tools
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

        Raises:
            NotImplementedError: This method is not implemented.
        """
        raise NotImplementedError()

    def parse_generation(self, completion: StructuredCompletion) -> List[Message]:
        """Parse a completion from OpenAI into messages.

        Args:
            completion: The StructuredCompletion from OpenAI.

        Returns:
            A list containing the parsed Message.

        Raises:
            ValueError: If the completion doesn't contain expected fields.
        """
        completion_dict = completion.to_dict()
        
        if "message" not in completion_dict:
            raise ValueError(f"Can't find message in completion: {completion_dict}")
            
        message_data = completion_dict["message"]
        content = message_data.get("content", "")
        
        # Handle content when it's a list (with text objects)
        if isinstance(content, list):
            # Extract text from content items
            text_parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item and item["text"] is not None:
                    text_parts.append(item["text"])
                elif isinstance(item, str):
                    text_parts.append(item)
            content = "\n".join(text_parts) if text_parts else ""
        
        # Check for tool calls (new format)
        tool_calls = message_data.get("tool_calls", [])
        if tool_calls:
            actions = []
            
            for tool_call in tool_calls:
                # Handle both object and dict formats
                if hasattr(tool_call, 'function'):
                    # Object format
                    tool_use_name = tool_call.function.name
                    arguments = tool_call.function.arguments
                    tool_id = getattr(tool_call, 'id', tool_use_name)
                else:
                    # Dict format
                    function_data = tool_call.get("function", {})
                    tool_use_name = function_data.get("name", "")
                    arguments = function_data.get("arguments", "{}")
                    tool_id = tool_call.get("id", tool_use_name)
                
                if TOOL_ACTION_SEPARATOR in tool_use_name:
                    tool_name, action_name = tool_use_name.split(TOOL_ACTION_SEPARATOR, maxsplit=1)
                else:
                    tool_name = tool_use_name
                    action_name = None
                    
                # Parse arguments
                try:
                    if isinstance(arguments, str):
                        parameters = json.loads(arguments)
                    else:
                        parameters = arguments
                except json.JSONDecodeError:
                    parameters = {"raw_arguments": arguments}
                    
                # Create an action
                action = ActionData(
                    tool_name=tool_name,
                    action_name=action_name,
                    parameters=parameters,
                    tool_use_id=tool_id
                )
                
                actions.append(action)
                
            if actions:
                message = Message(event_type=EventType.INTERNAL_EVENT, actions=actions)
                if content:
                    message.content = content
                    
                return [message]
        
        # Check for function_call (old format)
        function_call = message_data.get("function_call")
        if function_call:
            # This is a tool/function call
            if hasattr(function_call, 'name'):
                # Object format
                tool_use_name = function_call.name
                arguments = function_call.arguments
            else:
                # Dict format
                tool_use_name = function_call.get("name", "")
                arguments = function_call.get("arguments", "{}")
            
            if TOOL_ACTION_SEPARATOR in tool_use_name:
                tool_name, action_name = tool_use_name.split(TOOL_ACTION_SEPARATOR, maxsplit=1)
            else:
                tool_name = tool_use_name
                action_name = None
                
            # Parse arguments
            try:
                if isinstance(arguments, str):
                    parameters = json.loads(arguments)
                else:
                    parameters = arguments
            except json.JSONDecodeError:
                parameters = {"raw_arguments": arguments}
                
            # Create an action
            action = ActionData(
                tool_name=tool_name,
                action_name=action_name,
                parameters=parameters,
                tool_use_id=tool_name  # Use the tool name as the ID
            )
            
            message = Message(event_type=EventType.INTERNAL_EVENT, actions=[action])
            if content:
                message.content = content
                
            return [message]
        
        # This is a regular text response
        if content is None:
            content = ""
        message = Message(event_type=EventType.MESSAGE, content=content)
        return [message] 