import os
from typing import Dict, Optional, List, Any

import anthropic

from chorus.data.prompt import StructuredPrompt, StructuredCompletion
from chorus.lms.base import LanguageModelClient


ANTHROPIC_DEFAULT_CONFIG = {
    "max_tokens": 1024,
    "temperature": 0.7,
}


class AnthropicClient(LanguageModelClient[StructuredPrompt, StructuredCompletion]):
    """Client for interacting with Anthropic's Claude API.

    Handles communication with Anthropic's API, managing the conversation context and model parameters.
    """

    def __init__(self, model_name: str, api_key: Optional[str] = None):
        """Initialize the Anthropic client.

        Args:
            model_name (str): Name of the Anthropic model to use.
            api_key (Optional[str]): API key for Anthropic. If None, uses ANTHROPIC_API_KEY environment variable.
        """
        super().__init__()
        self._model_name = model_name
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.set_default_options(ANTHROPIC_DEFAULT_CONFIG)
        
        # Initialize client
        self._client: Optional[anthropic.Anthropic] = None
    
    def generate(
        self,
        prompt: Optional[StructuredPrompt] = None,
        prompt_dict: Optional[Dict[Any, Any]] = None,
        options: Optional[Dict[Any, Any]] = None,
        model_name: Optional[str] = None,
        region: Optional[str] = None
    ) -> StructuredCompletion:
        """Generate text using the Anthropic model.

        Args:
            prompt (StructuredPrompt): Input prompt for generation.
            prompt_dict (Dict): Input prompt dictionary for generation.
            options (Dict): Additional generation parameters that override defaults.
            model_name (str): Name of the Anthropic model.
            region (str): Region for the API, not used for Anthropic.

        Returns:
            StructuredCompletion: Generated text response.

        Raises:
            ValueError: If neither prompt nor prompt_dict is provided.
        """
        # Initialize client if not already done
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
            
        if prompt is None and prompt_dict is None:
            raise ValueError("Either prompt or prompt_dict has to be supplied.")
        if prompt_dict is None:
            if prompt is not None and isinstance(prompt, StructuredPrompt):
                prompt_dict = prompt.to_dict()
            else:
                raise ValueError("Prompt should be of type StructuredPrompt for using AnthropicClient.")

        # Prepare options
        lm_options = self.get_default_options().copy()
        if options is not None:
            lm_options.update(options)
        if prompt_dict and "tools" in prompt_dict:
            lm_options["tools"] = prompt_dict["tools"]

        # Use specified model or default model
        target_model = model_name or self._model_name
        
        # Extract messages from the prompt dictionary
        messages = prompt_dict.get("messages", [])
        
        response = self._client.messages.create(
            model=target_model,
            messages=messages,
            max_tokens=lm_options.get("max_tokens", 1024),
            temperature=lm_options.get("temperature", 0.0),
            tools=lm_options.get("tools", [])
        )
        
        # Format response to be compatible with BedrockConverseToolChatPrompter
        # Create the 'message' field with the expected structure
        
        return StructuredCompletion.from_dict(response.model_dump())
    