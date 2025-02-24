"""
Functions and exceptions for checking that
AllenNLP and its models are configured correctly.

Original Copyright 2022 AllenAI. Licensed under the Apache 2.0 License.
https://github.com/allenai/allennlp/blob/main/allennlp/common/checks.py

Modifications Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""

import logging
from typing import Any
from typing import Tuple
from typing import Union
from typing import Type
from typing import Dict
from typing import List

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """
    The exception raised by any AllenNLP object when it's misconfigured
    (e.g. missing properties, invalid properties, unknown properties).
    """

    def __reduce__(self) -> Union[str, Tuple[Any, ...]]:
        return type(self), (self.message,)

    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return self.message


def check_type(value: Any, expected_type: Type) -> bool:
    """Check if a value matches an expected type.

    Args:
        value (Any): The value to check.
        expected_type (Type): The expected type.

    Returns:
        bool: True if value matches expected type, False otherwise.
    """
    return isinstance(value, expected_type)


def check_required_params(params: Dict, required_keys: List[str]) -> None:
    """Verify that required parameters are present.

    Args:
        params (Dict): Dictionary of parameters to check.
        required_keys (List[str]): List of required parameter keys.

    Raises:
        ConfigurationError: If any required parameters are missing.
    """
    for key in required_keys:
        if key not in params:
            raise ConfigurationError(f"Required parameter '{key}' is missing")
