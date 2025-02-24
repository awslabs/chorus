from typing import Optional
import uuid

DEFAULT_DESCRIPTION = "Launched an async action."

def make_async_observation_data(action_name: str, tool_name: Optional[str] = None, expected_source: Optional[str] = None, description: Optional[str] = None):
    """
    Make an observation data for an async tool use.
    """
    if description is None:
        description = DEFAULT_DESCRIPTION
    return {
        "type": "async_action_calling",
        "action_name": action_name,
        "tool_name": tool_name,
        "expected_source": expected_source,
        "async_execution_id": str(uuid.uuid4()),
        "description": description,
    }

def is_async_observation_data(data: dict):
    """
    Check if the data is an async observation data.
    """
    if data is None or type(data) != dict:
        return False
    return data.get("type", None) == "async_action_calling"