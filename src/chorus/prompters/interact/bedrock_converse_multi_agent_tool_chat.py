"""Multi-agent tool chat prompter for Bedrock Converse API.

This module provides a prompter for handling multi-agent conversations with tool usage
through Amazon Bedrock's Converse API. It extends the base tool chat prompter to support
interactions between multiple agents, including action calls and observations.
"""

import json
import re
from datetime import datetime
from typing import List
from typing import Optional

from jinja2 import Template

from chorus.data.data_types import ActionData
from chorus.data.dialog import Message
from chorus.data.prompt import Prompt
from chorus.data.resource import Resource
from chorus.data.dialog import EventType
from chorus.data.prompt import StructuredPrompt
from chorus.data.toolschema import ToolSchema
from chorus.prompters.interact.bedrock_converse_tool_chat import BedrockConverseToolChatPrompter

TOOL_ACTION_SEPARATOR = "__"

USER_PROMPT = """
Your are in a multi-agent environment. Here is previous interaction history visible to you:
<interaction_history>
{% for interaction in interactions %}{{interaction}}
{% endfor -%}
</interaction_history>
{{history}}

Generate the next step. Include only one function call in the response.
""".strip()

TARGET = "{{thought}}"

MESSAGE_TEMPLATE = """
<message from="{{source}}" to="{{destination}}">
{{content}}
</message>
""".strip()

CHANNEL_MESSAGE_TEMPLATE = """
<message from="{{source}}" to="{{destination}}" channel="{{channel}}">
{{content}}
</message>
""".strip()

EVENT_TEMPLATE = """
<event type="{{event_type}}">
{{content}}
</event>
""".strip()


class BedrockConverseMultiAgentToolChatPrompter(BedrockConverseToolChatPrompter):
    """Prompter for multi-agent tool-based conversations using Bedrock Converse API.

    This prompter handles conversations between multiple agents that can use tools,
    formatting messages and actions in a structured way for the Bedrock Converse API.
    It supports action calls, observations, and both direct and channeled messages
    between agents.
    """

    def _get_action_prompt(self, action: ActionData):
        """Formats an action into a structured prompt format.

        Args:
            action: The action data containing tool name, action name and parameters.

        Returns:
            str: Formatted XML-style string representing the action call.
        """
        content = "<function_call>\n"
        content += f'<invoke action="{action.tool_name}__{action.action_name}">\n'
        for parameter_key, val in action.parameters.items():
            content += f'<parameter name="{parameter_key}">\n{str(val)}\n</parameter>\n'
        content += "</parameter>\n"
        content += "</invoke>\n"
        content += "</function_call>"
        return content

    def get_prompt(
        self,
        current_agent_id: str,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        agent_instruction: Optional[str] = None,
        resources: Optional[List[Resource]] = None,
        reference_time: Optional[str] = None,
        planner_instruction: Optional[str] = None,
    ) -> Prompt:
        """Generates a structured prompt for multi-agent conversation.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of previous conversation messages.
            tools: Optional list of available tools and their schemas.
            agent_instruction: Optional instruction text for the agent.
            resources: Optional list of resources available to the agent.
            reference_time: Optional reference time for the conversation.
            planner_instruction: Optional planning instructions.

        Returns:
            A structured prompt formatted for the Bedrock Converse API.
        """
        # Create tool config
        tool_config = None
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

        system_instruction = agent_instruction if agent_instruction is not None else ""

        if planner_instruction is not None:
            system_instruction += f"\n\n{planner_instruction}"

        interactions = []
        for turn in messages:
            if turn.event_type == EventType.INTERNAL_EVENT and turn.actions:
                action = turn.actions[0]
                content = self._get_action_prompt(action)
                interactions.append(
                    Template(EVENT_TEMPLATE, autoescape=True).render(event_type="action", content=content)
                )
            elif turn.event_type == EventType.INTERNAL_EVENT and turn.observations:
                interactions.append(
                    Template(EVENT_TEMPLATE, autoescape=True).render(
                        event_type="observation",
                        content=f"<fnr>\n<r>\n{json.dumps(turn.observations[0].data)}\n</r>\n</fnr>",
                    )
                )
            else:
                if turn.channel:
                    interactions.append(
                        Template(CHANNEL_MESSAGE_TEMPLATE, autoescape=True).render(
                            source=turn.source, destination=turn.destination, content=turn.content, channel=turn.channel
                        )
                    )
                else:
                    interactions.append(
                        Template(MESSAGE_TEMPLATE, autoescape=True).render(
                            source=turn.source, destination=turn.destination, content=turn.content
                        )
                    )

        user_prompt = Template(USER_PROMPT, autoescape=True).render(
            interactions=interactions,
        )
        prompt_dict = {
            "messages": [{"role": "user", "content": [{"text": user_prompt}]}],
        }
        if agent_instruction is not None:
            prompt_dict["system"] = [{"text": system_instruction}]
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
