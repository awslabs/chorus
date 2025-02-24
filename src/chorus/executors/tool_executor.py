import json
import logging
import os
import traceback
from typing import Any
from typing import List
from typing import Optional

from chorus.data.data_types import ActionData
from chorus.data.context import AgentContext
from chorus.data.executable_tool import ExecutableTool
from chorus.executors.base import ToolExecutor

logger = logging.getLogger(__name__)


class SimpleToolExecutor(ToolExecutor):
    """A simple tool executor that calls corresponding functions in Python objects.

    This executor takes a list of ExecutableTool objects and executes actions by calling
    their corresponding methods. It supports error handling and context management for tools.

    Args:
        tools: List of ExecutableTool objects that can be executed.
        agent_context: Optional context information for the agent executing the tools.
        tolerate_error: Whether to continue execution when tools raise errors.
    
    Raises:
        SystemError: If any tool in the provided list does not extend ExecutableTool.
    """

    def __init__(self, tools: List[ExecutableTool], agent_context: Optional[AgentContext] = None, tolerate_error: bool = True):
        for tool in tools:
            if not isinstance(tool, ExecutableTool):
                raise SystemError(
                    "When execute_tools is enabled, all tools must extends ExecutableTool class."
                )
        self._tool_map = {tool.get_schema().tool_name: tool for tool in tools}
        self._agent_context = agent_context
        self._tolerate_error = tolerate_error

    def execute(self, action: ActionData) -> Any:
        """Executes an action call and returns the observation.

        Args:
            action: The action to execute, containing tool name, action name and parameters.

        Returns:
            The observation result from executing the action. If an error occurs and
            tolerate_error is True, returns a dict with the error message.

        Raises:
            ValueError: If the tool is not registered or the action method is not found.
            Exception: If tolerate_error is False and any error occurs during execution.
        """
        logger.info(
            f"Executing action {action.tool_name}.{action.action_name}({action.parameters})"
        )
        try:
            if action.tool_name not in self._tool_map:
                raise ValueError(f"Tool {action.tool_name} is not registered")
            tool_object = self._tool_map[action.tool_name]
            if tool_object.requires_method_checking() and not hasattr(tool_object, action.action_name):
                raise ValueError(
                    f"The implementation of action {action.action_name} is not found for tool {action.tool_name}"
                )
            tool_object.set_context(self._agent_context)
            observation = tool_object.execute(
                action_name=action.action_name, parameters=action.parameters
            )
        except Exception as e:
            print("\033[1;31m" + "=" * os.get_terminal_size().columns + "\033[0m")
            print(f"\033[1;31m[Tool Execution Error Recorded] Error tolerance is set to {self._tolerate_error}. \033[0m")
            if self._tolerate_error:
                print("Agent will react to this error message rather than raise an exception.")
            else:
                print("Agent will raise an exception and stop execution.")
            print(f"\033[1;34mAction:\033[0m")
            print(action.model_dump_json(indent=2))
            print(f"\033[1;31mError details:\033[0m {str(e)}")
            print(f"\033[1;31mError type:\033[0m {type(e).__name__}")
            print(f"\033[1;31mTraceback:\033[0m {traceback.format_exc()}")
            print("\033[1;31m" + "=" * os.get_terminal_size().columns + "\033[0m")
            if self._tolerate_error:
                observation = {"error": str(e)}
            else:
                raise e
        logger.info(f"Observation: {json.dumps(observation)}")

        return observation
