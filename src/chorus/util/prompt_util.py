import os
from typing import Any, Dict, Optional

import yaml


class PrompterUtil:
    """Utility class for creating prompters.

    Manages the creation and configuration of prompters, with support for different
    prompter types and styles.
    """

    @staticmethod
    def get_prompter(
        prompter_name: str, config_path: Optional[str] = None, prompter_type: str = "interact"
    ):
        """Get a prompter instance.

        Args:
            prompter_name (str): The name of the prompter.
            config_path (str): The path to the prompter configuration file.
            prompter_type (str): The type of prompter.

        Returns:
            Prompter: The created prompter instance.

        Raises:
            ValueError: If neither prompter name nor config path is provided.
            NotImplementedError: If the prompter type is not supported.
        """
        # Load using prompter name or config path?
        if prompter_name is None and config_path is None:
            raise ValueError(
                "Either prompter name or path to config file has to be provided for creating a prompter."
            )
        # Load config file
        kwargs = {}
        if config_path is not None:
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"Prompter config does not exist:\n{config_path}")
            with open(config_path) as f:
                config = yaml.safe_load(f)
            if "prompter" not in config:
                raise ValueError(
                    f"Prompter config file must have 'prompter' field to specify prompter name."
                )
            prompter_name = config["prompter"]
            del config["prompter"]
            kwargs = config
        # Create base prompter class
        if prompter_type == "interact":
            from chorus.prompters import InteractPrompter
            prompter_class = InteractPrompter.get_subclass(prompter_name)
        elif prompter_type == "adapter":
            from chorus.prompters import PromptAdapter
            prompter_class = PromptAdapter.get_subclass(prompter_name)
        else:
            raise NotImplementedError
        return prompter_class(**kwargs)
