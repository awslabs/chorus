"""
Utility functions for data processing and model operations.

This module provides utility functions for working with Pydantic models and data
transformations.
"""

import hashlib
import json
import re
from datetime import datetime
from datetime import timedelta
from functools import cache
from typing import Set

from pydantic import BaseModel


def unique_hash_for_model(model: BaseModel, excluded_fields: Set[str]) -> str:
    """Generates a unique hash for a Pydantic model instance.

    Creates a deterministic hash of a model's data by converting it to JSON and
    computing an MD5 hash, while excluding specified fields.

    Args:
        model: The Pydantic model instance to hash
        excluded_fields: Set of field names to exclude from the hash computation

    Returns:
        A string containing the hexadecimal MD5 hash of the model data
    """
    id_string = json.dumps(model.model_dump_json(exclude_none=True, exclude=excluded_fields))
    md5 = hashlib.md5()
    md5.update(id_string.encode("utf-8"))
    return md5.hexdigest()
