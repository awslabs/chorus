from abc import ABCMeta
from abc import abstractmethod
from typing import List
from typing import Optional

from chorus.data.dialog import Message
from chorus.data.prompt import Completion
from chorus.data.planner_output import PlannerOutput
from chorus.data.prompt import Prompt
from chorus.data.resource import Resource
from chorus.data.dialog import EventType
from chorus.data.toolschema import ToolSchema
from chorus.prompters.base_prompter import BasePrompter
from chorus.util.prompt_util import PrompterUtil


class InteractPrompter(BasePrompter, metaclass=ABCMeta):
    """Base class for prompters that handle user-assistant interactions with LLMs.

    This class provides the base functionality for prompters that process multi-turn
    conversations between users and agents. It handles prompt adaptation, message parsing,
    and conversation state tracking.
    """

    def __init__(self, prompt_adapter: Optional[str] = None):
        """Initialize the InteractPrompter.

        Args:
            prompt_adapter: Optional name of prompt adapter to use for processing prompts.
        """
        if prompt_adapter is not None:
            self._prompt_adapter = PrompterUtil.get_prompter(
                prompt_adapter, prompter_type="adapter"
            )
        else:
            self._prompt_adapter = None

    def adapt_prompt(self, prompt: Prompt) -> Prompt:
        """Adapt a prompt using the configured prompt adapter.

        Args:
            prompt: The prompt to adapt.

        Returns:
            The adapted prompt.
        """
        if self._prompt_adapter is not None:
            return self._prompt_adapter.get_prompt(prompt)
        else:
            return Prompt(prompt)

    def adapt_target(self, target: Completion) -> Completion:
        """Adapt a target completion using the configured prompt adapter.

        Args:
            target: The target completion to adapt.

        Returns:
            The adapted target completion.
        """
        if self._prompt_adapter is not None:
            return self._prompt_adapter.get_target(target)
        else:
            return target

    def adapt_generation(self, generation: Completion) -> Completion:
        """Adapt a generated completion using the configured prompt adapter.

        Args:
            generation: The generated completion to adapt.

        Returns:
            The adapted generated completion.
        """
        if self._prompt_adapter is not None:
            return self._prompt_adapter.parse_generation(generation)
        else:
            return generation

    @abstractmethod
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
        """Generate a prompt from conversation messages and context.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of available tools.
            agent_instruction: Optional instruction for the agent.
            resources: Optional list of resources.
            reference_time: Optional reference time.
            planner_instruction: Optional instruction for planning.

        Returns:
            The generated prompt.
        """
        pass

    @abstractmethod
    def get_target(
        self,
        current_agent_id: str,
        messages: List[Message],
        tools: Optional[List[ToolSchema]] = None,
        agent_instruction: Optional[str] = None,
        resources: Optional[List[Resource]] = None,
        reference_time: Optional[str] = None,
    ) -> Completion:
        """Generate a target completion from conversation messages and context.

        Args:
            current_agent_id: ID of the current agent, used to identify if messages are inbound/outbound.
            messages: List of conversation messages.
            tools: Optional list of available tools.
            agent_instruction: Optional instruction for the agent.
            resources: Optional list of resources.
            reference_time: Optional reference time.

        Returns:
            The generated target completion.
        """
        pass

    @abstractmethod
    def parse_generation(self, completion: Completion) -> List[Message]:
        """Parse a generated completion into a list of messages.

        Args:
            completion: The completion to parse.

        Returns:
            List of parsed messages.
        """
        pass
