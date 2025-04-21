import os
from typing import Dict, Optional, List

from openai import OpenAI

from chorus.data.prompt import StructuredPrompt, StructuredCompletion
from chorus.lms.base import LanguageModelClient


OPENAI_DEFAULT_CONFIG = {
    "max_tokens": 1024,
    "temperature": 0.7,
}


class OpenAIClient(LanguageModelClient[StructuredPrompt, StructuredCompletion]):
    """Client for interacting with OpenAI Chat Completions API.

    Handles communication with OpenAI's API, managing the conversation context and model parameters.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the OpenAI client.

        Args:
            model_name (str): Name of the OpenAI model to use.
            api_key (Optional[str]): API key for OpenAI. If None, uses OPENAI_API_KEY environment variable.
            base_url (Optional[str]): Base URL for API calls. If None, uses OpenAI's default endpoint.
        """
        super().__init__()
        self._model_name = model_name
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self._base_url = base_url or os.environ.get("OPENAI_BASE_URL")
        self.set_default_options(OPENAI_DEFAULT_CONFIG)
        
        # Initialize client
        self._client_kwargs = {"api_key": self._api_key}
        if self._base_url:
            self._client_kwargs["base_url"] = self._base_url
            
        self._client = None
    
    def generate(
        self,
        prompt: Optional[StructuredPrompt] = None,
        prompt_dict: Optional[Dict] = None,
        options: Optional[Dict] = None,
        model_name: Optional[str] = None,
        **kwargs
    ) -> StructuredCompletion:
        """Generate text using the OpenAI chat completion model.

        Args:
            prompt (StructuredPrompt): Input prompt for generation.
            prompt_dict (Dict): Input prompt dictionary for generation.
            options (Dict): Additional generation parameters that override defaults.
            model_name (str): Name of the OpenAI model.

        Returns:
            StructuredCompletion: Generated text response.

        Raises:
            ValueError: If neither prompt nor prompt_dict is provided.
        """
        if self._client is None:
            self._client = OpenAI(**self._client_kwargs)

        if prompt is None and prompt_dict is None:
            raise ValueError("Either prompt or prompt_dict has to be supplied.")
        if prompt_dict is None:
            if prompt is not None and isinstance(prompt, StructuredPrompt):
                prompt_dict = prompt.to_dict()
            else:
                raise ValueError("Prompt should be of type StructuredPrompt for using OpenAIClient.")

        # Prepare options
        lm_options = self.get_default_options().copy()
        if options is not None:
            lm_options.update(options)
        if "tools" in prompt_dict:
            lm_options["tools"] = prompt_dict["tools"]

        # Use specified model or default model
        target_model = model_name or self._model_name
        
        # Extract messages from the prompt dictionary and format them correctly
        messages = prompt_dict.get("messages", [])
        
        # Call OpenAI API
        response = self._client.chat.completions.create(
            model=target_model,
            messages=messages,
            **lm_options
        )
        
        completion_dict = response.choices[0].to_dict()
        
        return StructuredCompletion.from_dict(completion_dict)