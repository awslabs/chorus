from abc import ABCMeta
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Optional

from chorus.config import Registrable
from chorus.data.schema import JsonData
from chorus.data.toolschema import ToolSchema

if TYPE_CHECKING:
    from chorus.data.context import AgentContext


class ExecutableTool(Registrable, metaclass=ABCMeta):
    """Base class for executable tools.

    An executable tool represents a tool that can perform actions based on its schema.

    Args:
        tool_schema: Schema defining the tool's capabilities and parameters.
    """

    def __init__(self, tool_schema: ToolSchema):
        self._tool_schema = tool_schema
        self._agent_context = None

    def get_schema(self):
        """Gets the tool's schema.

        Returns:
            ToolSchema: The schema defining this tool's capabilities.
        """
        return self._tool_schema

    def set_context(self, context: "AgentContext"):
        """Sets the agent context for this tool.

        Args:
            context: The agent context to set.
        """
        self._agent_context = context

    def get_context(self) -> "AgentContext":
        """Gets the agent context for this tool.

        Returns:
            AgentContext: The current agent context.
        """
        return self._agent_context

    def requires_method_checking(self):
        """Checks if this tool requires method checking.

        Returns:
            bool: False by default, indicating no method checking required.
        """
        return False

    @abstractmethod
    def execute(self, action_name: Optional[str] = None, parameters: JsonData = None) -> JsonData:
        """Executes the tool with given action and parameters.

        Args:
            action_name: Name of the action to execute.
            parameters: Parameters for the action.

        Returns:
            JsonData: The observation/result from executing the action.
        """


class SimpleExecutableTool(ExecutableTool):
    """A simple executable tool implementation.

    In SimpleExecutableTool, all actions have to be implemented as member functions.
    The action name must match the name of an existing method in the class.
    """

    def requires_method_checking(self):
        """Checks if this tool requires method checking.

        Returns:
            bool: True, indicating method checking is required.
        """
        return True

    def execute(self, action_name: Optional[str] = None, parameters: JsonData = None) -> JsonData:
        """Executes the named action with given parameters.

        Args:
            action_name: Name of the action/method to execute.
            parameters: Parameters to pass to the action method.

        Returns:
            JsonData: The result from executing the action method.

        Raises:
            ValueError: If action_name is None or if the named action is not implemented.
        """
        if action_name is None:
            raise ValueError("Action name needs to be specified.")
        function = getattr(self, action_name)
        if function is None:
            raise ValueError(
                f"Action {action_name} is not implemented in this this tool {type(self)}."
            )
        return function(**parameters)
