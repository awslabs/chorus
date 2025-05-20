import os
from typing import Optional

from chorus.lms.openai_client import OpenAIClient


DEEPSEEK_BASE_URL = "https://api.deepseek.com"


class DeepseekClient(OpenAIClient):
    """Client for interacting with Deepseek's API.
    
    Extends OpenAIClient since Deepseek uses the OpenAI compatible API format.
    """
    
    def __init__(self, model_name: str = "deepseek-chat", api_key: Optional[str] = None):
        """Initialize the Deepseek client.
        
        Args:
            model_name (str): Name of the Deepseek model to use.
            api_key (Optional[str]): API key for Deepseek. If None, uses DEEPSEEK_API_KEY environment variable.
        """
        api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL
        ) 