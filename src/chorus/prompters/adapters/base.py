from abc import ABCMeta
from abc import abstractmethod
from typing import List

from chorus.data.dialog import Message
from chorus.data.prompt import Prompt
from chorus.data.resource import Resource
from chorus.data.toolschema import ToolSchema
from chorus.prompters.base_prompter import BasePrompter


class PromptAdapter(BasePrompter, metaclass=ABCMeta):

    def get_prompt(self, prompt: str) -> Prompt:
        return Prompt(prompt)

    def get_target(self, target: str) -> str:
        return target

    def parse_generation(self, generated_text: str) -> str:
        return generated_text
