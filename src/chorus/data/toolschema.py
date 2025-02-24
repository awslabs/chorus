import logging
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from jsonref import replace_refs
from openapi_spec_validator import OpenAPIV30SpecValidator
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename
from pydantic import BaseModel
from pydantic import Field

from chorus.data.schema import JsonData
from chorus.data.schema import JsonSchema

logger = logging.getLogger(__file__)


class ToolType(str, Enum):
    """Enumeration of tool types.

    Attributes:
        MODULE: Represents a module tool type
        DATA_SOURCE: Represents a data source tool type
    """
    MODULE: str = "Module"
    DATA_SOURCE: str = "DataSource"


class Action(BaseModel):
    """Action definition.

    Actions correspond to functions, with well-defined input/output schemas (JSON Schema).
    Each action should have a human-readable name and description.

    Attributes:
        name: Action name (unique within a tool)
        description: Human-readable description of the action
        input_schema: Input parameters JSON Schema
        output_schema: Output results JSON Schema
        requires_confirmation: Whether the action requires confirmation before execution
        meta: Dataset-specific metadata specific to this action
    """

    name: str
    description: str
    input_schema: JsonSchema
    output_schema: Optional[JsonSchema] = None
    requires_confirmation: bool = False
    meta: Optional[Dict[str, JsonData]] = Field(default_factory=dict)


class ToolSchema(BaseModel):
    """Tool definition.

    Tools contain a set of related actions.

    Attributes:
        tool_name: Unique identifier for the tool (unique within a tool database)
        name: Human-readable name of the tool (unique within a toolbox)
        description: Human-readable description of the tool
        actions: List of actions supported by this tool
        tool_type: Type of tool
        meta: Dataset-specific metadata specific to this tool (e.g. version, last update)
    """

    tool_name: str
    name: str
    description: str
    actions: List[Action]
    tool_type: ToolType = ToolType.MODULE
    meta: Optional[Dict[str, JsonData]] = Field(default_factory=dict)

    def actions_by_name(self) -> Dict[str, Action]:
        """Creates a mapping of action names to Action objects.

        Returns:
            Dict mapping action names to their corresponding Action objects
        """
        return {action.name: action for action in self.actions}

    def get_action(self, action: str) -> Action:
        """Gets an action by name.

        Args:
            action: Name of the action to retrieve

        Returns:
            The Action object with the specified name

        Raises:
            KeyError: If no action exists with the given name
        """
        return self.actions_by_name()[action]

    @staticmethod
    def load_native_format(path: str) -> 'ToolSchema':
        """Loads a tool from a native JSON format file.

        Args:
            path: Path to the JSON file containing the tool definition

        Returns:
            A ToolSchema instance created from the JSON file

        Raises:
            ValidationError: If the JSON does not match the expected schema
            IOError: If there are issues reading the file
        """
        with open(path) as f:
            content = f.read()
        return ToolSchema.model_validate_json(content)

    @staticmethod
    def _get_nested_key(mapping: dict, keys: list, default=None) -> Any:
        """Gets a value from a nested dictionary using a list of keys.

        Args:
            mapping: Dictionary to search in
            keys: List of keys defining the path to the desired value
            default: Value to return if the path is not found

        Returns:
            The value at the specified path, or the default if not found
        """
        current_node = mapping
        try:
            for key in keys:
                current_node = current_node[key]
        except KeyError:
            return default
        return current_node

    @classmethod
    def load_openapi_format(cls, tool_path: str) -> 'ToolSchema':
        """Loads a tool from an OpenAPI format file.

        Args:
            tool_path: Path to the OpenAPI specification file

        Returns:
            A ToolSchema instance created from the OpenAPI spec

        Raises:
            OpenAPIValidationError: If the tool does not conform to OpenAPI 3.0 spec
            ValueError: If required fields are missing
            IOError: If there are issues reading the file
        """
        spec_dict, _ = read_from_filename(tool_path)
        spec_dict = replace_refs(spec_dict, proxies=False, lazy_load=False)
        validate(spec_dict, cls=OpenAPIV30SpecValidator)

        actions = []
        for path, path_obj in spec_dict.get("paths", {}).items():
            for verb, verb_obj in path_obj.items():
                operation_id = verb_obj.get("operationId", "")
                if not operation_id:
                    raise ValueError(
                        f"operationId is required for each method of each path. Not found for {path}::{verb}"
                    )
                description = verb_obj.get("summary", "")
                if not description:
                    logging.warning(f"'summary' key is not found for {path}::{verb}")

                # Build input schema
                input_schema = {"type": "object", "properties": {}, "required": []}
                if verb == "post":
                    input_schema = (
                        cls._get_nested_key(
                            verb_obj, ["requestBody", "content", "application/json", "schema"], {}
                        )
                        or input_schema
                    )
                for param in verb_obj.get("parameters", []):
                    assert "name" in param
                    param_name = param["name"]
                    param_schema = param.get("schema", {})
                    param_schema["title"] = param_name
                    if "description" in param:
                        param_schema["description"] = param["description"]
                    input_schema["properties"][param_name] = param_schema
                    if param.get("required", False):
                        input_schema["required"].append(param_name)

                # Build output schema
                output_schema = {"oneOf": []}
                for response_status, response in verb_obj.get("responses", {}).items():
                    schema = cls._get_nested_key(
                        response, ["content", "application/json", "schema"], {}
                    )
                    schema.update(
                        title=response_status,
                        description=response["description"],
                    )
                    output_schema["oneOf"].append(schema)

                # Build final action
                action = Action.model_validate(
                    {
                        "name": operation_id,
                        "description": description,
                        "input_schema": input_schema,
                        "output_schema": output_schema,
                    }
                )
                actions.append(action)
        tool_name = cls._get_nested_key(spec_dict, ["info", "title"], "")
        if not tool_name:
            raise ValueError(f"Missing name for tool at {tool_path}")
        tool = ToolSchema(
            tool_name=tool_name,
            name=tool_name,
            description=cls._get_nested_key(spec_dict, ["info", "description"], ""),
            actions=actions,
        )
        return tool


class ToolDB(BaseModel):
    """Collection/database of tools.

    A database containing multiple tools and associated metadata.

    Attributes:
        tools: List of tools available in this tool database
        meta: Metadata associated with this tool database
    """

    tools: List[ToolSchema]
    meta: Optional[Dict[str, JsonData]] = Field(default_factory=dict)

    def tools_by_id(self) -> Dict[str, ToolSchema]:
        """Creates a mapping of tool IDs to ToolSchema objects.

        Returns:
            Dict mapping tool IDs to their corresponding ToolSchema objects
        """
        return {tool.tool_name: tool for tool in self.tools}

    def get_tool(self, tool_name: str) -> Optional[ToolSchema]:
        """Gets a tool by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            The ToolSchema object with the specified name, or None if not found
        """
        tools_by_id = self.tools_by_id()
        return tools_by_id[tool_name] if tool_name in tools_by_id else None

    def get_action(self, tool_name: str, action: str) -> Optional[Action]:
        """Gets an action from a specific tool.

        Args:
            tool_name: Name of the tool containing the action
            action: Name of the action to retrieve

        Returns:
            The Action object if found, None otherwise
        """
        tool = self.get_tool(tool_name)
        if tool:
            actions_by_name = tool.actions_by_name()
            if action in actions_by_name:
                return actions_by_name[action]
        return None
