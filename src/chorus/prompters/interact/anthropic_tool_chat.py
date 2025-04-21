"""Tool chat prompter for Anthropic Claude API.

This module provides a prompter for handling conversations with tool usage through
Anthropic's Claude API. It handles formatting messages and tool calls into
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

class AnthropicToolChatPrompter(InteractPrompter[StructuredCompletion]):
    """Prompter for tool-enabled chat using Anthropic Claude API.

    This prompter handles formatting messages and tool calls into the structured format
    expected by Anthropic's API, and parsing responses back into messages.
    It supports tool usage by formatting tool schemas and actions according to the API's
    requirements.
    """

    def __init__(self):
        """Initialize the AnthropicToolChatPrompter."""
        super().__init__()

    def _get_action_dict(self, action: ActionData) -> Dict:
        """Convert an ActionData object into an Anthropic tool use dictionary.

        Args:
            action: The ActionData object to convert.

        Returns:
            A dictionary containing the tool use formatted for Anthropic Claude API.
        """
        action_name = action.tool_name
        if action.action_name is not None:
            action_name += f"{TOOL_ACTION_SEPARATOR}{action.action_name}"
            
        return {
            "type": "tool_use",
            "id": action.tool_use_id or action_name,
            "name": action_name,
            "input": action.parameters
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
        """Generate a structured prompt for the Anthropic Claude API.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of tool schemas defining available tools.
            agent_instruction: Optional instruction text for the agent.
            resources: Optional list of resources available to the agent.
            reference_time: Optional reference time for the conversation.
            planner_instruction: Optional planning instruction for multi-agent scenarios.

        Returns:
            A StructuredPrompt formatted for the Anthropic Claude API.
        """
        # Create tool config for Anthropic
        anthropic_tools = []
        if tools:
            for tool_schema in tools:
                for action in tool_schema.actions:
                    tool_use_name = f"{tool_schema.name}{TOOL_ACTION_SEPARATOR}{action.name}"
                    tool_use_description = action.description
                    
                    # Convert the JSON schema to the format Anthropic expects
                    schema_dict = json.loads(action.input_schema.model_dump_json(exclude_none=True, by_alias=True))
                    
                    anthropic_tools.append({
                        "name": tool_use_name,
                        "description": tool_use_description,
                        "input_schema": schema_dict
                    })

        # Create formatted messages for Anthropic
        anthropic_messages = []
        
        # System instruction is handled separately by Anthropic
        system_instruction = agent_instruction if agent_instruction is not None else ""
        if planner_instruction is not None:
            system_instruction += f"\n\n{planner_instruction}"
            
        # Process conversation messages
        for message in messages:
            # Skip messages without a clear role
            role = None
            content_parts = []
            is_internal = message.event_type == EventType.INTERNAL_EVENT
            is_from_myself = message.source == current_agent_id
            
            if not is_internal and not is_from_myself:
                # Regular user message
                role = "user"
                if message.content:
                    content_parts.append({"type": "text", "text": message.content})
                
            elif not is_internal and is_from_myself:
                # Regular assistant message
                role = "assistant"
                if message.content:
                    content_parts.append({"type": "text", "text": message.content})
                
            elif is_internal and message.actions:
                # Tool use from assistant
                role = "assistant"
                
                for action_data in message.actions:
                    action_name = action_data.tool_name
                    if action_data.action_name is not None:
                        action_name += f"{TOOL_ACTION_SEPARATOR}{action_data.action_name}"
                    
                    content_parts.append({
                        "type": "tool_use",
                        "id": action_data.tool_use_id or action_name,
                        "name": action_name,
                        "input": action_data.parameters
                    })
                
                if message.content:
                    content_parts.insert(0, {"type": "text", "text": message.content})
                
            elif is_internal and message.observations:
                # Tool result from user
                role = "user"
                
                for observation in message.observations:
                    
                    tool_result_content = None
                    if isinstance(observation.data, str):
                        tool_result_content = observation.data
                    else:
                        tool_result_content = observation.data
                    
                    content_parts.append({
                        "type": "tool_result",
                        "tool_use_id": observation.tool_use_id,
                        "content": json.dumps(observation.data)
                    })
            
            # Skip if no valid role was determined or no content
            if role is None or not content_parts:
                continue
                
            # Add the message
            anthropic_messages.append({
                "role": role,
                "content": content_parts
            })
            
        # Create the final prompt dictionary
        prompt_dict = {
            "messages": anthropic_messages
        }
        
        if system_instruction:
            prompt_dict["system"] = system_instruction
            
        if anthropic_tools:
            prompt_dict["tools"] = anthropic_tools
            
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
        """Parse a completion from Anthropic Claude into messages.

        Args:
            completion: The StructuredCompletion from Anthropic Claude.

        Returns:
            A list containing the parsed Message.

        Raises:
            ValueError: If the completion doesn't contain expected fields.
        """
        completion_dict = completion.to_dict()
        
        # Handle direct content in the completion dict
        if "content" in completion_dict:
            content_parts = completion_dict["content"]
        # Handle content in the message field
        elif "message" in completion_dict:
            message_data = completion_dict["message"]
            content_parts = message_data.get("content", [])
        else:
            raise ValueError(f"Can't find content or message in completion: {completion_dict}")
        
        # Handle content when it's not a list
        if not isinstance(content_parts, list):
            if isinstance(content_parts, str):
                return [Message(event_type=EventType.MESSAGE, content=content_parts)]
            elif isinstance(content_parts, dict) and "text" in content_parts:
                return [Message(event_type=EventType.MESSAGE, content=content_parts["text"])]
            content_parts = []
        
        text_parts = []
        actions = []
        
        for part in content_parts:
            if isinstance(part, str):
                text_parts.append(part)
                continue
            
            if not isinstance(part, dict):
                continue
            
            part_type = part.get("type")
            
            if part_type == "text":
                # Regular text content
                text_content = part.get("text", "")
                if text_content is not None:
                    text_parts.append(text_content)
                
            elif part_type == "tool_use":
                # Tool use / function call
                tool_use_id = part.get("id")
                tool_use_name = part.get("name")
                
                if TOOL_ACTION_SEPARATOR in tool_use_name:
                    tool_name, action_name = tool_use_name.split(TOOL_ACTION_SEPARATOR, maxsplit=1)
                else:
                    tool_name = tool_use_name
                    action_name = None
                    
                parameters = part.get("input", {})
                
                action = ActionData(
                    tool_name=tool_name,
                    action_name=action_name,
                    parameters=parameters,
                    tool_use_id=tool_use_id
                )
                
                actions.append(action)
        
        if actions:
            # This is a tool/function call
            message = Message(event_type=EventType.INTERNAL_EVENT, actions=actions)
            if text_parts:
                message.content = "\n".join(text_parts)
        else:
            # This is a regular text response
            content = "\n".join(text_parts) if text_parts else ""
            message = Message(event_type=EventType.MESSAGE, content=content)
            
        return [message] 