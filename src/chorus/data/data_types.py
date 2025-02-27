from typing import Optional, Dict

from pydantic import BaseModel, Field

from chorus.data.schema import JsonData

class ObservationData(BaseModel):
    """Data model representing an observation from a tool execution.

    This class defines the structure for observations returned when executing tools,
    including support for both synchronous and asynchronous execution patterns.

    Attributes:
        data: The actual observation data returned from the tool execution.
        tool_use_id: Optional identifier for tracking specific tool usage.
        is_async_observation: Flag indicating if this is an asynchronous observation.
        async_execution_id: Optional identifier for tracking async executions.
    """

    data: JsonData
    tool_use_id: Optional[str] = None
    is_async_observation: bool = False
    async_execution_id: Optional[str] = None


class ActionData(BaseModel):
    """Data model representing an action call to execute a tool.

    This class defines the structure for actions that can be executed by tools,
    including parameters and tracking information for both sync and async execution.

    Attributes:
        tool_name: Name of the tool to execute.
        action_name: Optional specific action name within the tool.
        parameters: Optional parameters to pass to the tool action.
        tool_use_id: Optional identifier for tracking specific tool usage.
        async_execution_id: Optional identifier for tracking async executions.
    """

    tool_name: str
    action_name: Optional[str] = None
    parameters: Optional[Dict] = Field(default_factory=dict)
    tool_use_id: Optional[str] = None
    async_execution_id: Optional[str] = None
