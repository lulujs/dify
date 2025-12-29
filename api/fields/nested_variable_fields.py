"""
Flask-RESTX field definitions for nested variable API responses.

This module provides field definitions for serializing nested variable
definitions in workflow API responses.
"""

from typing import Any

from flask_restx import fields


class NestedVariableDefinitionField(fields.Raw):
    """
    Custom field for serializing nested variable definitions.

    Handles recursive serialization of nested variable structures,
    including children for object and array[object] types.
    """

    def format(self, value: Any) -> dict[str, Any] | list[dict[str, Any]] | None:
        """
        Format a nested variable definition or list of definitions.

        Args:
            value: A NestedVariableDefinition, dict, or list of either

        Returns:
            Serialized nested variable definition(s)
        """
        if value is None:
            return None

        if isinstance(value, list):
            return [self._format_single(item) for item in value]

        return self._format_single(value)

    def _format_single(self, value: Any) -> dict[str, Any]:
        """
        Format a single nested variable definition.

        Args:
            value: A NestedVariableDefinition or dict

        Returns:
            Serialized nested variable definition
        """
        # Handle Pydantic model
        if hasattr(value, "model_dump"):
            data = value.model_dump()
        elif isinstance(value, dict):
            data = value
        else:
            raise TypeError(f"Unexpected type for nested variable: {type(value)}")

        result: dict[str, Any] = {
            "name": data.get("name", ""),
            "type": str(data.get("type", "")),
            "required": data.get("required", False),
            "description": data.get("description", ""),
        }

        # Include default_value if present
        if "default_value" in data and data["default_value"] is not None:
            result["default_value"] = data["default_value"]

        # Recursively format children
        children = data.get("children")
        if children:
            result["children"] = [self._format_single(child) for child in children]

        return result


# Field definitions for nested variable in API responses
nested_variable_definition_fields = {
    "name": fields.String(description="Variable name"),
    "type": fields.String(description="Variable type"),
    "required": fields.Boolean(description="Whether the variable is required"),
    "description": fields.String(description="Variable description"),
    "default_value": fields.Raw(description="Default value"),
    "children": fields.List(fields.Raw, description="Child variable definitions"),
}

# Field definitions for node input definition
node_input_definition_fields = {
    "name": fields.String(description="Input name"),
    "type": fields.String(description="Input type"),
    "required": fields.Boolean(description="Whether the input is required"),
    "description": fields.String(description="Input description"),
    "variable_selector": fields.Raw(description="Variable selector for referencing upstream outputs"),
    "children": fields.List(fields.Raw, description="Child variable definitions"),
    "default_value": fields.Raw(description="Default value"),
}

# Field definitions for node output definition
node_output_definition_fields = {
    "name": fields.String(description="Output name"),
    "type": fields.String(description="Output type"),
    "description": fields.String(description="Output description"),
    "children": fields.List(fields.Raw, description="Child variable definitions"),
}
