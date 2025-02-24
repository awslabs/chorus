from abc import ABCMeta
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from chorus.data.prompt import Prompt
from chorus.data.prompt import Completion


class LanguageModelClient(metaclass=ABCMeta):
    """Base class for language model clients.

    Provides the interface for interacting with different language models in a 
    consistent way across the Chorus system.
    """

    def __init__(self):
        self._default_options = {}

    def set_default_options(self, options: Dict):
        """Set default options for the language model.

        Args:
            options (Dict): Dictionary of default options to set.
        """
        self._default_options.update(options)

    def get_default_options(self):
        """Get the current default options.

        Returns:
            Dict: Current default options for the model.
        """
        return self._default_options

    @abstractmethod
    def generate(self, prompt: Prompt, options: Optional[Dict] = None) -> Completion:
        """Generate text from the language model.

        Args:
            prompt (Prompt): Input prompt for generation.
            options (Optional[Dict]): Generation options that override defaults.

        Returns:
            Completion: Generated text completion.

        Raises:
            NotImplementedError: This is an abstract method.
        """
        raise NotImplementedError
