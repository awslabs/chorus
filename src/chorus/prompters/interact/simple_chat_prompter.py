from typing import List
from typing import Optional

from chorus.data.dialog import Message
from chorus.data.prompt import Prompt
from chorus.data.resource import Resource
from chorus.data.dialog import EventType
from chorus.data.prompt import StructuredPrompt
from chorus.data.toolschema import ToolSchema
from chorus.prompters.interact.base import InteractPrompter

SUPPORTED_MODEL_TYPES = ("claude-3", "gpt")


class SimpleChatPrompter(InteractPrompter):

    def __init__(self, model_type: str = "claude-3"):
        super().__init__()
        self._model_type = model_type
        if model_type not in SUPPORTED_MODEL_TYPES:
            raise NotImplementedError(f"Model type {model_type} is not supported.")

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
        if planner_instruction is not None:
            raise NotImplementedError(
                "Planner instructions are not supported for simple chat prompter."
            )
        prompt_dict: dict = {}
        if self._model_type == "gpt":
            output_messages: List[dict] = []
            if agent_instruction is not None:
                output_messages.append(
                    {
                        "role": "system",
                        "content": agent_instruction,
                    }
                )
            for msg in messages:
                # Determine role based on source/destination
                if msg.event_type == EventType.INTERNAL_EVENT:
                    continue
                
                role = "user"
                # Determine role based on if message is to/from current agent
                if msg.source == current_agent_id:
                    role = "assistant"
                elif msg.destination == current_agent_id:
                    role = "user"
                    
                output_messages.append(
                    {
                        "role": role,
                        "content": msg.content,
                    }
                )
            prompt_dict = {"messages": output_messages}
            return StructuredPrompt.from_dict(prompt_dict)
        else:
            # Assuming using converse API
            output_messages = []
            for msg in messages:
                if msg.event_type == EventType.INTERNAL_EVENT:
                    continue
                
                role = "user"
                # Determine role based on if message is to/from current agent
                if msg.source == current_agent_id:
                    role = "assistant"
                elif msg.destination == current_agent_id:
                    role = "user"
                    
                output_messages.append(
                    {"role": role, "content": [{"text": msg.content}]}
                )
            if output_messages and output_messages[0]["role"] == "assistant":
                output_messages.pop(0)
            prompt_dict = {"messages": output_messages}
            if agent_instruction is not None:
                prompt_dict["system"] = agent_instruction
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
        raise NotImplementedError

    def parse_generation(self, generated_text: str) -> List[Message]:
        return [Message(event_type=EventType.MESSAGE, content=generated_text)]
