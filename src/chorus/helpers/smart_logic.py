from chorus.config.globals import DEFAULT_AGENT_LLM_NAME
from chorus.data.dialog import Message, Role
from chorus.data.context import AgentContext
from chorus.data.prompt import StructuredCompletion
from chorus.helpers.base import AgentHelper
from chorus.lms import LanguageModelClient
from chorus.lms.bedrock_converse import BedrockConverseAPIClient
from chorus.prompters import SimpleChatPrompter

from typing import Optional


class SmartLogicHelper(AgentHelper):
    """Helper class for developing LLM-based orchestration logic.

    This class provides helper methods for using language models to implement
    intelligent orchestration logic between agents. It handles prompting,
    condition checking, and information extraction using LLMs.
    """

    def __init__(self, context: AgentContext):
        """Initialize the SmartLogicHelper.

        Args:
            context: The agent context containing configuration and services.
        """
        super().__init__(context)
        self._lm_client: Optional[LanguageModelClient] = None

    def prompt(self, prompt: str) -> Optional[str]:
        """Send a prompt to the language model and get the response.

        Args:
            prompt: The prompt text to send to the language model.

        Returns:
            str: The generated response text from the language model.
        """
        if self._lm_client is None:
            self._lm_client = BedrockConverseAPIClient(DEFAULT_AGENT_LLM_NAME)
        prompter = SimpleChatPrompter()
        processed_prompt = prompter.get_prompt(messages=[Message(role=Role.USER, content=prompt)])
        response = self._lm_client.generate(processed_prompt)
        if isinstance(response, StructuredCompletion):
            contents = response.to_dict()["message"]["content"]
            if contents:
                return contents[0].get("text", None)
            else:
                return None
        else:
            return response

    def smart_judge(self, content: str, condition: str) -> bool:
        """Use the language model to judge if content meets a condition.

        Args:
            content: The text content to evaluate.
            condition: The condition to check against the content.

        Returns:
            bool: True if the content meets the condition, False otherwise.
        """
        if self._lm_client is None:
            self._lm_client = BedrockConverseAPIClient(DEFAULT_AGENT_LLM_NAME)
        prompt = f"Judge whether the following content meets the condition.\n\nContent:\n{content}\n\nCondition:\n{condition}\n\nRespond with either TRUE or FALSE with nothing else."
        prompter = SimpleChatPrompter()
        processed_prompt = prompter.get_prompt(messages=[Message(role=Role.USER, content=prompt)])
        response = self._lm_client.generate(processed_prompt)
        if isinstance(response, StructuredCompletion):
            contents = response.to_dict()["message"]["content"]
            if contents:
                return contents[0].get("text", None) == "TRUE"
            else:
                return False
        else:
            return response == "TRUE"

    def smart_extract(self, content: str, target: str) -> Optional[str]:
        """Use the language model to extract specific information from content.

        Args:
            content: The text content to extract information from.
            target: Description of the information to extract.

        Returns:
            str: The extracted information.
        """
        if self._lm_client is None:
            self._lm_client = BedrockConverseAPIClient(DEFAULT_AGENT_LLM_NAME)
        prompt = f"Extract {target} from following content: {content}. Return only extracted information."
        prompter = SimpleChatPrompter()
        processed_prompt = prompter.get_prompt(messages=[Message(role=Role.USER, content=prompt)])
        response = self._lm_client.generate(processed_prompt)
        if isinstance(response, StructuredCompletion):
            contents = response.to_dict()["message"]["content"]
            if contents:
                return contents[0].get("text", None)
            else:
                return None
        else:
            return response
