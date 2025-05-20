"""Tool chat prompter for OpenAI Chat API.

This module provides a prompter for handling conversations with tool usage through
OpenAI's Chat API. It handles formatting messages and tool calls into
the structured format expected by the API, and parsing responses back into messages.
"""

import json
import re
from typing import Dict, List, Optional, Any, Collection, Sequence, Union, cast

from chorus.data.data_types import ActionData
from chorus.data.dialog import Message
from chorus.data.resource import Resource
from chorus.data.prompt import StructuredPrompt
from chorus.data.prompt import StructuredCompletion
from chorus.data.toolschema import ToolSchema
from chorus.prompters.interact import InteractPrompter
from chorus.data.dialog import EventType

TOOL_ACTION_SEPARATOR = "."

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

    def _get_action_dict(self, action: ActionData) -> Dict[str, Any]:
        """Convert an ActionData object to a dictionary for OpenAI tools format.

        Args:
            action: The action data to convert

        Returns:
            Dict: The action in OpenAI tool format
        """
        action_name = action.tool_name
        if action.action_name is not None:
            action_name += f"{TOOL_ACTION_SEPARATOR}{action.action_name}"
            
        return {
            "id": action.tool_use_id or action_name,
            "function": {
                "name": action_name, 
                "arguments": json.dumps(action.parameters)
            },
            "type": "function"
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
        """Create an OpenAI-formatted prompt from messages and tools.

        Args:
            current_agent_id: The ID of the current agent
            messages: List of messages in the conversation
            tools: List of available tools
            agent_instruction: Optional instruction for the agent
            resources: Optional list of resources
            reference_time: Optional reference time
            planner_instruction: Optional instruction for planning

        Returns:
            StructuredPrompt: The formatted prompt for OpenAI
        """
        # Track tool IDs to names for response parsing
        tool_id_to_name_map: Dict[str, str] = {}
        
        # Convert tools to OpenAI format if provided
        openai_tools: List[Dict[str, Any]] = []
        if tools:
            for tool in tools:
                tool_dict = tool.to_dict()
                name = tool_dict.get("name", "")
                
                # Check for action functions
                if "actions" in tool_dict and tool_dict["actions"]:
                    for action in tool_dict["actions"]:
                        action_name = action.get("name", "")
                        full_name = f"{name}{TOOL_ACTION_SEPARATOR}{action_name}"
                        
                        function_dict = {
                            "name": full_name,
                            "description": action.get("description", ""),
                        }
                        
                        if "parameters" in action:
                            function_dict["parameters"] = action["parameters"]
                        
                        openai_tools.append({
                            "type": "function",
                            "function": function_dict
                        })
                else:
                    # Tool with no actions - make it a direct function
                    function_dict = {
                        "name": name,
                        "description": tool_dict.get("description", ""),
                    }
                    
                    if "parameters" in tool_dict:
                        function_dict["parameters"] = tool_dict["parameters"]
                    
                    openai_tools.append({
                        "type": "function",
                        "function": function_dict
                    })
        
        # Convert messages to OpenAI format
        openai_messages = []
        
        # Add agent instruction as system message if provided
        if agent_instruction:
            openai_messages.append({
                "role": "system",
                "content": agent_instruction
            })
        
        # Add each message
        for message in messages:
            role = None
            content = message.content or ""
            is_internal = message.event_type == EventType.INTERNAL_EVENT
            
            # Skip internal messages without actions or observations
            if is_internal and not message.actions and not message.observations:
                continue
            
            # Determine role based on source
            if message.source == "user":
                role = "user"
            elif message.source == current_agent_id:
                role = "assistant"
            elif message.source == "system":
                role = "system"
            
            # Handle actions (function/tool calls from assistant)
            if is_internal and message.actions:
                # Create tool calls
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

                # Using type annotations to help mypy
                message_content: Optional[str] = message.content if message.content else None
                message_dict: Dict[str, Any] = {
                    "role": "assistant",
                    "content": message_content,
                    "tool_calls": tool_calls
                }
                
                openai_messages.append(message_dict)
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
                        "name": tool_id_to_name_map.get(observation.tool_use_id or "", ""),
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
        prompt_dict: Dict[str, Any] = {
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