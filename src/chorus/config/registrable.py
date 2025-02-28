"""
`allennlp.common.registrable.Registrable` is a "mixin" for endowing
any base class with a named registry for its subclasses and a decorator
for registering them.

Original Copyright 2022 AllenAI. Licensed under the Apache 2.0 License.
https://github.com/allenai/allennlp/blob/main/allennlp/common/registrable.py

Modifications Copyright 2022 Amazon.com, Inc. or its affiliates. All Rights Reserved.
"""

import importlib
import inspect
import logging
from collections import defaultdict
from typing import Any
from typing import Callable
from typing import ClassVar
from typing import DefaultDict
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import cast

from chorus.config.checks import ConfigurationError
from chorus.config.from_params import FromParams

logger = logging.getLogger(__name__)

_T = TypeVar("_T")
_RegistrableT = TypeVar("_RegistrableT", bound="Registrable")

_SubclassRegistry = Dict[str, Tuple[type, Optional[str]]]


class Registrable(FromParams):
    """Base class for registrable components.

    Provides registration functionality for Chorus components, allowing them to be
    dynamically loaded and instantiated by name.
    """

    _registry: ClassVar[DefaultDict[type, _SubclassRegistry]] = defaultdict(dict)
    default_implementation: Optional[str] = None

    @classmethod
    def register(
        cls, name: str, constructor: Optional[str] = None, exist_ok: bool = True
    ) -> Callable[[Type[_T]], Type[_T]]:
        """Register a subclass with a given name.

        Args:
            name (str): Name to register the subclass under.
            constructor (Optional[str]): Optional constructor method name.
            exist_ok (bool): Whether to allow overwriting existing registrations.

        Returns:
            Callable: Decorator function that registers the class.

        Raises:
            ConfigurationError: If name is already registered and exist_ok is False.
        """
        registry = Registrable._registry[cls]

        def add_subclass_to_registry(subclass: Type[_T]) -> Type[_T]:
            # Add to registry, raise an error if key has already been used.
            if name in registry:
                if exist_ok:
                    message = (
                        f"{name} has already been registered as {registry[name][0].__name__}, but "
                        f"exist_ok=True, so overwriting with {cls.__name__}"
                    )
                    logger.info(message)
                else:
                    message = (
                        f"Cannot register {name} as {cls.__name__}; "
                        f"name already in use for {registry[name][0].__name__}"
                    )
                    raise ConfigurationError(message)
            registry[name] = (subclass, constructor)
            return subclass

        return add_subclass_to_registry

    @classmethod
    def by_name(cls: Type[_RegistrableT], name: str) -> Callable[..., _RegistrableT]:
        """Get a constructor for a registered class by name.

        Args:
            name (str): Name of the registered class.

        Returns:
            Callable: Constructor function for the registered class.

        Raises:
            ConfigurationError: If the class name cannot be resolved.
        """
        logger.debug(f"instantiating registered subclass {name} of {cls}")
        subclass, constructor = cls.resolve_class_name(name)
        if not constructor:
            return cast(Type[_RegistrableT], subclass)
        else:
            return cast(Callable[..., _RegistrableT], getattr(subclass, constructor))

    @classmethod
    def resolve_class_name(
        cls: Type[_RegistrableT], name: str
    ) -> Tuple[Type[_RegistrableT], Optional[str]]:
        """Resolve a class name to its class and constructor.

        Args:
            name (str): Name to resolve.

        Returns:
            Tuple[Type[_RegistrableT], Optional[str]]: The class and optional constructor name.

        Raises:
            ConfigurationError: If the class name cannot be resolved.
        """
        if name in Registrable._registry[cls]:
            subclass, constructor = Registrable._registry[cls][name]
            return subclass, constructor
        elif "." in name:
            # This might be a fully qualified class name, so we'll try importing its "module"
            # and finding it there.
            parts = name.split(".")
            submodule = ".".join(parts[:-1])
            class_name = parts[-1]

            try:
                module = importlib.import_module(submodule)
            except ModuleNotFoundError:
                raise ConfigurationError(
                    f"tried to interpret {name} as a path to a class "
                    f"but unable to import module {submodule}"
                )

            try:
                subclass = getattr(module, class_name)
                constructor = None
                return subclass, constructor
            except AttributeError:
                raise ConfigurationError(
                    f"tried to interpret {name} as a path to a class "
                    f"but unable to find class {class_name} in {submodule}"
                )

        else:
            # is not a qualified class name
            available = cls.list_available()
            suggestion = _get_suggestion(name, available)
            raise ConfigurationError(
                (
                    f"'{name}' is not a registered name for '{cls.__name__}'"
                    + (". " if not suggestion else f", did you mean '{suggestion}'? ")
                )
                + "If your registered class comes from custom code, you'll need to import "
                "the corresponding modules. If you're using AllenNLP from the command-line, "
                "this is done by using the '--include-package' flag, or by specifying your imports "
                "in a '.allennlp_plugins' file. "
                "Alternatively, you can specify your choices "
                """using fully-qualified paths, e.g. {"model": "my_module.models.MyModel"} """
                "in which case they will be automatically imported correctly."
            )

    @classmethod
    def list_available(cls) -> List[str]:
        """List default first if it exists"""
        keys = list(Registrable._registry[cls].keys())
        default = cls.default_implementation

        if default is None:
            return keys
        elif default not in keys:
            raise ConfigurationError(f"Default implementation {default} is not registered")
        else:
            return [default] + [k for k in keys if k != default]

    def _to_params(self) -> Dict[str, Any]:
        """
        Default behavior to get a params dictionary from a registrable class
        that does NOT have a _to_params implementation. It is NOT recommended to
         use this method. Rather this method is a minial implementation that
         exists so that calling `_to_params` does not break.
        # Returns
        parameter_dict: `Dict[str, Any]`
            A minimal parameter dictionary for a given registrable class. Will
            get the registered name and return that as well as any positional
            arguments it can find the value of.
        """
        logger.warning(
            f"'{self.__class__.__name__}' does not implement '_to_params`. Will"
            f" use Registrable's `_to_params`."
        )

        # Get the list of parent classes in the MRO in order to check where to
        # look for the registered name. Skip the first because that is the
        # current class.
        mro = inspect.getmro(self.__class__)[1:]

        registered_name = None
        for parent in mro:
            # Check if Parent has any registered classes
            try:
                registered_classes = self._registry[parent]
            except KeyError:
                continue

            # Found a dict of (name,(class,constructor)) pairs. Check if the
            # current class is in it.
            for name, registered_value in registered_classes.items():
                registered_class, _ = registered_value
                if registered_class == self.__class__:
                    registered_name = name
                    break

            # Extra break to end the top loop.
            if registered_name is not None:
                break

        if registered_name is None:
            raise KeyError(f"'{self.__class__.__name__}' is not registered")

        parameter_dict = {"type": registered_name}

        # Get the parameters from the init function.
        for parameter in inspect.signature(self.__class__).parameters.values():
            # Skip non-positional arguments. For simplicity, these are arguments
            # without a default value as those will be required for the
            # `from_params` method.
            if parameter.default != inspect.Parameter.empty:
                logger.debug(f"Skipping parameter {parameter.name}")
                continue

            # Try to get the value of the parameter from the class. Will only
            # try 'name' and '_name'. If it is not there, the parameter is not
            # added to the returned dict.
            if hasattr(self, parameter.name):
                parameter_dict[parameter.name] = getattr(self, parameter.name)
            elif hasattr(self, f"_{parameter.name}"):
                parameter_dict[parameter.name] = getattr(self, f"_{parameter.name}")
            else:
                logger.warning(f"Could not find a value for positional argument {parameter.name}")
                continue

        return parameter_dict

    @classmethod
    def get_subclass(cls, name: str) -> Type:
        """Get a registered subclass by name.

        Args:
            name (str): Name of the registered subclass.

        Returns:
            Type: The registered subclass.

        Raises:
            KeyError: If no subclass is registered with the given name.
        """
        if name in Registrable._registry[cls]:
            subclass, _ = Registrable._registry[cls][name]
            return subclass
        else:
            raise KeyError(f"No subclass registered with name {name}")


def _get_suggestion(name: str, available: List[str]) -> Optional[str]:
    # First check for simple mistakes like using '-' instead of '_', or vice-versa.
    for ch, repl_ch in (("_", "-"), ("-", "_")):
        suggestion = name.replace(ch, repl_ch)
        if suggestion in available:
            return suggestion
    return None
