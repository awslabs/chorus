"""
Original Copyright 2022 AllenAI. Licensed under the Apache 2.0 License.
https://github.com/allenai/allennlp/blob/main/allennlp/common/params.py

Modifications Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""

import copy
import json
import logging
import os
import zlib
from collections.abc import MutableMapping
from itertools import chain
from os import PathLike
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Optional
from typing import Set
from typing import TypeVar
from typing import Union

# _jsonnet doesn't work on Windows, so we have to use fakes.
try:
    from _jsonnet import evaluate_file
    from _jsonnet import evaluate_snippet
except ImportError:
    raise ImportError("jsonnet is missing.")

from chorus.config.checks import ConfigurationError

logger = logging.getLogger(__name__)


def infer_and_cast(value: Any):
    """Infer and cast types for JSON-like values.

    Recursively infers and casts values that look like bool, int, or float
    to their appropriate types.

    Args:
        value (Any): Value to infer and cast.

    Returns:
        Any: The value with inferred types.

    Raises:
        ValueError: If the type cannot be inferred.
    """

    if isinstance(value, (int, float, bool)):
        # Already one of our desired types, so leave as is.
        return value
    elif isinstance(value, list):
        # Recursively call on each list element.
        return [infer_and_cast(item) for item in value]
    elif isinstance(value, dict):
        # Recursively call on each dict value.
        return {key: infer_and_cast(item) for key, item in value.items()}
    elif isinstance(value, str):
        # If it looks like a bool, make it a bool.
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        else:
            # See if it could be an int.
            try:
                return int(value)
            except ValueError:
                pass
            # See if it could be a float.
            try:
                return float(value)
            except ValueError:
                # Just return it as a string.
                return value
    else:
        raise ValueError(f"cannot infer type of {value}")


def _is_encodable(value: str) -> bool:
    """Check if a string can be unicode-encoded.

    Args:
        value (str): String to check.

    Returns:
        bool: True if the string can be unicode-encoded.
    """
    # Idiomatically you'd like to not check the != b""
    # but mypy doesn't like that.
    return (value == "") or (value.encode("utf-8", "ignore") != b"")


def _environment_variables() -> Dict[str, str]:
    """Get encodable environment variables.

    Returns:
        Dict[str, str]: Dictionary of environment variables that can be encoded.
    """
    return {key: value for key, value in os.environ.items() if _is_encodable(value)}


T = TypeVar("T", dict, list)


def with_overrides(original: T, overrides_dict: Dict[str, Any], prefix: str = "") -> T:
    merged: T
    keys: Union[Iterable[str], Iterable[int]]
    if isinstance(original, list):
        merged = [None] * len(original)
        keys = range(len(original))
    elif isinstance(original, dict):
        merged = {}
        keys = chain(
            original.keys(), (k for k in overrides_dict if "." not in k and k not in original)
        )
    else:
        if prefix:
            raise ValueError(
                f"overrides for '{prefix[:-1]}.*' expected list or dict in original, "
                f"found {type(original)} instead"
            )
        else:
            raise ValueError(f"expected list or dict, found {type(original)} instead")

    used_override_keys: Set[str] = set()
    for key in keys:
        if str(key) in overrides_dict:
            merged[key] = copy.deepcopy(overrides_dict[str(key)])
            used_override_keys.add(str(key))
        else:
            overrides_subdict = {}
            for o_key in overrides_dict:
                if o_key.startswith(f"{key}."):
                    overrides_subdict[o_key[len(f"{key}.") :]] = overrides_dict[o_key]
                    used_override_keys.add(o_key)
            if overrides_subdict:
                merged[key] = with_overrides(
                    original[key], overrides_subdict, prefix=prefix + f"{key}."
                )
            else:
                merged[key] = copy.deepcopy(original[key])

    unused_override_keys = [prefix + key for key in set(overrides_dict.keys()) - used_override_keys]
    if unused_override_keys:
        raise ValueError(f"overrides dict contains unused keys: {unused_override_keys}")

    return merged


def parse_overrides(
    serialized_overrides: str, ext_vars: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if serialized_overrides:
        ext_vars = {**_environment_variables(), **(ext_vars or {})}

        return json.loads(evaluate_snippet("", serialized_overrides, ext_vars=ext_vars))
    else:
        return {}


def _is_dict_free(obj: Any) -> bool:
    """
    Returns False if obj is a dict, or if it's a list with an element that _has_dict.
    """
    if isinstance(obj, dict):
        return False
    elif isinstance(obj, list):
        return all(_is_dict_free(item) for item in obj)
    else:
        return True


class Params(MutableMapping):
    """Configuration parameter management class.

    Represents a parameter dictionary with a history, and contains functionality around
    parameter passing and validation. Provides parameter validation, including checking
    for acceptable values and ensuring no extra parameters are passed.
    """

    DEFAULT = object()

    def __init__(self, params: Dict[str, Any], history: str = "") -> None:
        """Initialize configuration parameters.

        Args:
            params (Dict[str, Any]): Dictionary of configuration parameters.
            history (str): History of parameter access.
        """
        self.params = _replace_none(params)
        self.history = history

    def pop(self, key: str, default: Any = DEFAULT, keep_as_dict: bool = False) -> Any:
        """Pop a value from the parameters dictionary.

        Args:
            key (str): Key to pop from the parameters.
            default (Any): Default value if key not found.
            keep_as_dict (bool): Whether to keep dictionary values as dicts.

        Returns:
            Any: The popped value.

        Raises:
            ConfigurationError: If key is required but not found.
        """
        if default is self.DEFAULT:
            try:
                value = self.params.pop(key)
            except KeyError:
                msg = f'key "{key}" is required'
                if self.history:
                    msg += f' at location "{self.history}"'
                raise ConfigurationError(msg)
        else:
            value = self.params.pop(key, default)

        if keep_as_dict or _is_dict_free(value):
            logger.info(f"{self.history}{key} = {value}")
            return value
        else:
            return self._check_is_dict(key, value)

    def pop_int(self, key: str, default: Any = DEFAULT) -> Optional[int]:
        """Pop and convert a value to integer.

        Args:
            key (str): Key to pop from the parameters.
            default (Any): Default value if key not found.

        Returns:
            Optional[int]: The popped value converted to int, or None.
        """
        value = self.pop(key, default)
        if value is None:
            return None
        else:
            return int(value)

    def pop_float(self, key: str, default: Any = DEFAULT) -> Optional[float]:
        """Pop and convert a value to float.

        Args:
            key (str): Key to pop from the parameters.
            default (Any): Default value if key not found.

        Returns:
            Optional[float]: The popped value converted to float, or None.
        """
        value = self.pop(key, default)
        if value is None:
            return None
        else:
            return float(value)

    def pop_bool(self, key: str, default: Any = DEFAULT) -> Optional[bool]:
        """Pop and convert a value to boolean.

        Args:
            key (str): Key to pop from the parameters.
            default (Any): Default value if key not found.

        Returns:
            Optional[bool]: The popped value converted to bool, or None.

        Raises:
            ValueError: If the value cannot be converted to bool.
        """
        value = self.pop(key, default)
        if value is None:
            return None
        elif isinstance(value, bool):
            return value
        elif value == "true":
            return True
        elif value == "false":
            return False
        else:
            raise ValueError("Cannot convert variable to bool: " + value)

    def get(self, key: str, default: Any = DEFAULT):
        """Get a value from the parameters dictionary.

        Similar to dict.get() but also checks for returned dicts and returns
        a Params object in their place with an updated history.

        Args:
            key (str): Key to get from the parameters.
            default (Any): Default value if key not found.

        Returns:
            Any: The value, or default if not found.
        """
        default = None if default is self.DEFAULT else default
        value = self.params.get(key, default)
        return self._check_is_dict(key, value)

    def pop_choice(
        self,
        key: str,
        choices: List[Any],
        default_to_first_choice: bool = False,
        allow_class_names: bool = True,
    ) -> Any:
        """
        Gets the value of `key` in the `params` dictionary, ensuring that the value is one of
        the given choices. Note that this `pops` the key from params, modifying the dictionary,
        consistent with how parameters are processed in this codebase.
        # Parameters
        key: `str`
            Key to get the value from in the param dictionary
        choices: `List[Any]`
            A list of valid options for values corresponding to `key`.  For example, if you're
            specifying the type of encoder to use for some part of your model, the choices might be
            the list of encoder classes we know about and can instantiate.  If the value we find in
            the param dictionary is not in `choices`, we raise a `ConfigurationError`, because
            the user specified an invalid value in their parameter file.
        default_to_first_choice: `bool`, optional (default = `False`)
            If this is `True`, we allow the `key` to not be present in the parameter
            dictionary.  If the key is not present, we will use the return as the value the first
            choice in the `choices` list.  If this is `False`, we raise a
            `ConfigurationError`, because specifying the `key` is required (e.g., you `have` to
            specify your model class when running an experiment, but you can feel free to use
            default settings for encoders if you want).
        allow_class_names: `bool`, optional (default = `True`)
            If this is `True`, then we allow unknown choices that look like fully-qualified class names.
            This is to allow e.g. specifying a model type as my_library.my_model.MyModel
            and importing it on the fly. Our check for "looks like" is extremely lenient
            and consists of checking that the value contains a '.'.
        """
        default = choices[0] if default_to_first_choice else self.DEFAULT
        value = self.pop(key, default)
        ok_because_class_name = allow_class_names and "." in value
        if value not in choices and not ok_because_class_name:
            key_str = self.history + key
            message = (
                f"{value} not in acceptable choices for {key_str}: {choices}. "
                "You should either use the --include-package flag to make sure the correct module "
                "is loaded, or use a fully qualified class name in your config file like "
                """{"model": "my_module.models.MyModel"} to have it imported automatically."""
            )
            raise ConfigurationError(message)
        return value

    def as_dict(self, quiet: bool = False, infer_type_and_cast: bool = False):
        """Convert parameters to a dictionary.

        Converts the parameters to a plain dictionary, optionally with type inference
        and casting.

        Args:
            quiet (bool): Whether to suppress logging of parameters.
            infer_type_and_cast (bool): Whether to infer and cast types.

        Returns:
            Dict[str, Any]: Dictionary representation of parameters.
        """
        if infer_type_and_cast:
            params_as_dict = infer_and_cast(self.params)
        else:
            params_as_dict = self.params

        if quiet:
            return params_as_dict

        def log_recursively(parameters, history):
            for key, value in parameters.items():
                if isinstance(value, dict):
                    new_local_history = history + key + "."
                    log_recursively(value, new_local_history)
                else:
                    logger.info(f"{history}{key} = {value}")

        log_recursively(self.params, self.history)
        return params_as_dict

    def as_flat_dict(self) -> Dict[str, Any]:
        """Convert to a flat dictionary.

        Returns a flat dictionary where nested structure is collapsed with periods
        in the keys.

        Returns:
            Dict[str, Any]: Flattened dictionary of parameters.
        """
        flat_params = {}

        def recurse(parameters, path):
            for key, value in parameters.items():
                newpath = path + [key]
                if isinstance(value, dict):
                    recurse(value, newpath)
                else:
                    flat_params[".".join(newpath)] = value

        recurse(self.params, [])
        return flat_params

    def duplicate(self) -> "Params":
        """Create a deep copy of these parameters.

        Returns:
            Params: A new Params instance with identical contents.
        """
        return copy.deepcopy(self)

    def assert_empty(self, class_name: str):
        """Assert that no parameters remain unconsumed.

        Args:
            class_name (str): Name of the calling class for error messages.

        Raises:
            ConfigurationError: If there are unconsumed parameters.
        """
        if self.params:
            raise ConfigurationError(
                "Extra parameters passed to {}: {}".format(class_name, self.params)
            )

    def __getitem__(self, key):
        if key in self.params:
            return self._check_is_dict(key, self.params[key])
        else:
            raise KeyError(str(key))

    def __setitem__(self, key, value):
        self.params[key] = value

    def __delitem__(self, key):
        del self.params[key]

    def __iter__(self):
        return iter(self.params)

    def __len__(self):
        return len(self.params)

    def _check_is_dict(self, new_history, value):
        """Check if a value is a dictionary and convert if needed.

        Args:
            new_history (str): History string for the new value.
            value (Any): Value to check.

        Returns:
            Any: Original value or new Params instance if value was dict.
        """
        if isinstance(value, dict):
            new_history = self.history + new_history + "."
            return Params(value, history=new_history)
        if isinstance(value, list):
            value = [self._check_is_dict(f"{new_history}.{i}", v) for i, v in enumerate(value)]
        return value

    @classmethod
    def from_file(
        cls,
        params_file: Union[str, PathLike],
        params_overrides: Union[str, Dict[str, Any]] = "",
        ext_vars: dict = None,
    ) -> "Params":
        """Create a Params instance from a configuration file.

        Args:
            params_file (Union[str, PathLike]): Path to the configuration file.
            params_overrides (Union[str, Dict[str, Any]]): Overrides to apply.
            ext_vars (dict): External variables for substitution.

        Returns:
            Params: New instance initialized with parameters from file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            ValueError: If the file format is invalid.
        """
        if ext_vars is None:
            ext_vars = {}

        ext_vars = {**_environment_variables(), **ext_vars}

        file_dict = json.loads(evaluate_file(params_file, ext_vars=ext_vars))

        if isinstance(params_overrides, dict):
            params_overrides = json.dumps(params_overrides)
        overrides_dict = parse_overrides(params_overrides, ext_vars=ext_vars)

        if overrides_dict:
            param_dict = with_overrides(file_dict, overrides_dict)
        else:
            param_dict = file_dict

        return cls(param_dict)

    def get_hash(self) -> str:
        """Get a hash representing the current state.

        Returns a deterministic hash code representing the current state of the parameters.
        Uses zlib.adler32 instead of Python's builtin hash for determinism across runs.

        Returns:
            str: Hash code of the current parameter state.
        """
        dumped = json.dumps(self.params, sort_keys=True)
        hashed = zlib.adler32(dumped.encode())
        return str(hashed)

    def __str__(self) -> str:
        return f"{self.history}Params({self.params})"


def _replace_none(params: Any) -> Any:
    """Replace 'None' string values with None.

    Recursively replaces string values of 'None' with Python None.

    Args:
        params (Any): Parameters to process.

    Returns:
        Any: Parameters with 'None' strings replaced.
    """
    if params == "None":
        return None
    elif isinstance(params, dict):
        for key, value in params.items():
            params[key] = _replace_none(value)
        return params
    elif isinstance(params, list):
        return [_replace_none(value) for value in params]
    return params
