import json
import os
import sys
import time
from typing import Dict
from typing import Optional

import boto3
import botocore.errorfactory
import botocore.exceptions
from botocore.config import Config

from tenacity import retry, stop_after_attempt, wait_exponential

from chorus.data.prompt import Prompt, StructuredCompletion
from chorus.data.prompt import StructuredPrompt
from chorus.lms.base import LanguageModelClient

AWS_DEFAULT_REGION = "us-west-2"
BEDROCK_DEFAULT_CONFIG: Dict = {}
ACCEPT = "application/json"
CONTENT_TYPE = "application/json"


class BedrockConverseAPIClient(LanguageModelClient[StructuredPrompt, StructuredCompletion]):
    """Client for interacting with Amazon Bedrock Converse API.

    Handles communication with Bedrock's Converse API, managing the 
    conversation context and model parameters.
    """

    def __init__(self, model_name: str):
        """Initialize the Bedrock conversation client.

        Args:
            model_name (str): Name of the Bedrock model to use.
        """
        super().__init__()
        self._model_name = model_name
        self.set_default_options(BEDROCK_DEFAULT_CONFIG)

    @retry(wait=wait_exponential(multiplier=2, min=5, max=60), stop=stop_after_attempt(5))
    def generate(
        self,
        prompt: Optional[StructuredPrompt] = None,
        prompt_dict: Optional[Dict] = None,
        options: Optional[Dict] = None,
        model_name: Optional[str] = None,
        region: Optional[str] = AWS_DEFAULT_REGION,
    ) -> StructuredCompletion:
        """Generate text using the Bedrock conversation model.

        Args:
            prompt (StructuredPrompt): Input prompt for generation.
            prompt_dict (Dict): Input prompt dictionary for generation.
            options (Dict): Additional generation parameters that override defaults.
            model_name (str): Name of the Bedrock model.
            region (str): AWS region for Bedrock.

        Returns:
            StructuredCompletion: Generated text response.

        Raises:
            BedrockError: If there is an error communicating with Bedrock.
            ValueError: If neither prompt nor prompt_dict is provided.
        """
        if prompt is None and prompt_dict is None:
            raise ValueError("Either prompt or prompt_dict has to be supplied.")
        if prompt_dict is None:
            if prompt is not None and isinstance(prompt, StructuredPrompt):
                prompt_dict = prompt.to_dict()
            else:
                raise ValueError("Prompt should be of type StructuredPrompt for using BedrockConverseClient.")

        # Prepare client
        try:
            session = boto3.Session()
        except botocore.exceptions.ProfileNotFound:
            session = boto3.Session()
        target_region = os.environ.get("AWS_REGION", region)
        if model_name is None:
            model_name = self._model_name
        retry_config = Config(
            region_name=target_region,
            retries={
                "max_attempts": 10,
                "mode": "standard",
            },
        )
        bedrock_client = session.client(
            service_name="bedrock-runtime",
            config=retry_config,
        )

        # Prepare options
        lm_options = self.get_default_options().copy()
        if options is not None:
            lm_options.update(options)

        # Call client
        prompt_dict["inferenceConfig"] = lm_options
        prompt_dict["modelId"] = model_name

        try:
            model_response = bedrock_client.converse(
                **prompt_dict
            )
            if "output" in model_response:
                completion = StructuredCompletion.from_dict(model_response["output"])
            else:
                raise ValueError(f"Cannot parse response from Bedrock Converse API: {json.dumps(model_response)}")
        except botocore.exceptions.ClientError as error:
            if error.response["Error"]["Code"] == "AccessDeniedException":
                print(
                    f"\x1b[41m{error.response['Error']['Message']}\
                            \nTo troubeshoot this issue please refer to the following resources.\
                             \nhttps://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html\
                             \nhttps://docs.aws.amazon.com/bedrock/latest/userguide/security-iam.html\x1b[0m\n"
                )
            elif error.response["Error"]["Code"] == "ValidationException":
                try:
                    terminal_size = os.get_terminal_size().columns
                except OSError:
                    terminal_size = 80
                print("\x1b[1;31m" + "=" * terminal_size + "\x1b[0m")
                print(f"\x1b[1;31mValidation Error when calling Bedrock Converse API.\x1b[0m")
                print(f"\x1b[1;34m[Error Message]\x1b[0m")
                print(f"{error}")
                print(f"\x1b[1;34m[Prompt]\x1b[0m")
                print(json.dumps(prompt_dict, indent=2))
                print("\x1b[1;31m" + "=" * terminal_size + "\x1b[0m")
                sys.exit(1)
            elif error.response["Error"]["Code"] == "UnrecognizedClientException":
                print("Encountered UnrecognizedClientException error when calling Bedrock Converse API.")
                print(f"\x1b[1;31mUnrecognized client exception: {error.response['Error']['Message']}\x1b[0m")
                sys.exit(1)
            else:
                raise error
        except botocore.exceptions.ParamValidationError as error:
            try:
                terminal_size = os.get_terminal_size().columns
            except OSError:
                terminal_size = 80
            print("\x1b[1;31m" + "=" * terminal_size + "\x1b[0m")
            print(f"\x1b[1;31mParameter Validation Error when calling Bedrock Converse API.\x1b[0m")
            print(f"\x1b[1;34m[Error Message]\x1b[0m")
            print(f"{error}")
            print(f"\x1b[1;34m[Prompt]\x1b[0m")
            print(json.dumps(prompt_dict, indent=2))
            print("\x1b[1;31m" + "=" * terminal_size + "\x1b[0m")
            sys.exit(1)
        return completion

