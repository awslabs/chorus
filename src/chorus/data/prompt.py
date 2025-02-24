import json
from typing import Dict


class Prompt(str):
    """Base class for prompts.

    A string-based class that represents a prompt for language models.

    Attributes:
        prompt_type: Type identifier for the prompt, defaults to "text"
    """
    prompt_type: str = "text"


class StructuredPrompt(Prompt):
    """Class for structured prompts.

    A prompt class that handles structured data in JSON format.

    Attributes:
        prompt_type: Type identifier for the prompt, set to "structured"
    """
    prompt_type: str = "structured"

    @staticmethod
    def from_dict(src_dict: Dict):
        """Creates a StructuredPrompt from a dictionary.

        Args:
            src_dict: Source dictionary to convert to JSON string

        Returns:
            StructuredPrompt: A new structured prompt containing the JSON string
        """
        return StructuredPrompt(json.dumps(src_dict))

    def to_dict(self):
        """Converts the prompt back to a dictionary.

        Returns:
            dict: Dictionary parsed from the JSON string
        """
        return json.loads(self)


class Completion(str):
    """Base class for completions.

    A string-based class that represents a completion from language models.

    Attributes:
        completion_type: Type identifier for the completion, defaults to "text"
    """
    completion_type: str = "text"


class StructuredCompletion(Completion):
    """Class for structured completions.

    A completion class that handles structured data in JSON format.

    Attributes:
        completion_type: Type identifier for the completion, set to "structured"
    """
    completion_type: str = "structured"

    @staticmethod
    def from_dict(src_dict: Dict):
        """Creates a StructuredCompletion from a dictionary.

        Args:
            src_dict: Source dictionary to convert to JSON string

        Returns:
            StructuredCompletion: A new structured completion containing the JSON string
        """
        return StructuredCompletion(json.dumps(src_dict))

    def to_dict(self):
        """Converts the completion back to a dictionary.

        Returns:
            dict: Dictionary parsed from the JSON string
        """
        return json.loads(self)