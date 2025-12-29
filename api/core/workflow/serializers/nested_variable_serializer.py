"""
Nested Variable Serializer.

This module provides serialization and deserialization utilities for nested variable
definitions, ensuring proper JSON encoding/decoding while maintaining backward
compatibility with existing non-nested variable definitions.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from core.workflow.entities.nested_variable import NestedVariableDefinition, NestedVariableType
from core.workflow.entities.node_input import EnhancedVariableSelector, NodeInputDefinition, NodeOutputDefinition


class NestedVariableSerializationError(Exception):
    """Exception raised when serialization fails."""

    pass


class NestedVariableDeserializationError(Exception):
    """Exception raised when deserialization fails."""

    pass


class NestedVariableSerializer:
    """
    Serializer for nested variable definitions.

    Provides methods to serialize nested variable definitions to JSON-compatible
    dictionaries and deserialize them back, with support for backward compatibility
    with existing non-nested variable definitions.
    """

    @classmethod
    def serialize_definition(cls, definition: NestedVariableDefinition) -> dict[str, Any]:
        """
        Serialize a NestedVariableDefinition to a JSON-compatible dictionary.

        Args:
            definition: The nested variable definition to serialize.

        Returns:
            A dictionary representation suitable for JSON encoding.
        """
        result: dict[str, Any] = {
            "name": definition.name,
            "type": definition.type.value,
            "required": definition.required,
            "description": definition.description,
        }

        if definition.default_value is not None:
            result["default_value"] = definition.default_value

        if definition.children:
            result["children"] = [cls.serialize_definition(child) for child in definition.children]

        return result

    @classmethod
    def deserialize_definition(cls, data: Mapping[str, Any]) -> NestedVariableDefinition:
        """
        Deserialize a dictionary to a NestedVariableDefinition.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A NestedVariableDefinition instance.

        Raises:
            NestedVariableDeserializationError: If the data is invalid.
        """
        try:
            name = data.get("name")
            if not name:
                raise NestedVariableDeserializationError("Missing required field 'name'")

            type_str = data.get("type")
            if not type_str:
                raise NestedVariableDeserializationError("Missing required field 'type'")

            try:
                var_type = NestedVariableType(type_str)
            except ValueError:
                raise NestedVariableDeserializationError(f"Invalid variable type: {type_str}")

            children = None
            if data.get("children"):
                children_data = data["children"]
                if not isinstance(children_data, list):
                    raise NestedVariableDeserializationError("Field 'children' must be a list")
                children = [cls.deserialize_definition(child) for child in children_data]

            return NestedVariableDefinition(
                name=name,
                type=var_type,
                required=data.get("required", False),
                description=data.get("description", ""),
                default_value=data.get("default_value"),
                children=children,
            )
        except NestedVariableDeserializationError:
            raise
        except Exception as e:
            raise NestedVariableDeserializationError(f"Failed to deserialize nested variable definition: {e}")

    @classmethod
    def serialize_definitions(cls, definitions: Sequence[NestedVariableDefinition]) -> list[dict[str, Any]]:
        """
        Serialize a sequence of NestedVariableDefinitions to a list of dictionaries.

        Args:
            definitions: The sequence of definitions to serialize.

        Returns:
            A list of dictionary representations.
        """
        return [cls.serialize_definition(d) for d in definitions]

    @classmethod
    def deserialize_definitions(cls, data: Sequence[Mapping[str, Any]]) -> list[NestedVariableDefinition]:
        """
        Deserialize a sequence of dictionaries to NestedVariableDefinitions.

        Args:
            data: The sequence of dictionaries to deserialize.

        Returns:
            A list of NestedVariableDefinition instances.

        Raises:
            NestedVariableDeserializationError: If any item is invalid.
        """
        return [cls.deserialize_definition(item) for item in data]

    @classmethod
    def serialize_variable_selector(cls, selector: EnhancedVariableSelector) -> dict[str, Any]:
        """
        Serialize an EnhancedVariableSelector to a dictionary.

        Args:
            selector: The variable selector to serialize.

        Returns:
            A dictionary representation.
        """
        return {
            "variable": selector.variable,
            "value_selector": list(selector.value_selector),
        }

    @classmethod
    def deserialize_variable_selector(cls, data: Mapping[str, Any]) -> EnhancedVariableSelector:
        """
        Deserialize a dictionary to an EnhancedVariableSelector.

        Args:
            data: The dictionary to deserialize.

        Returns:
            An EnhancedVariableSelector instance.

        Raises:
            NestedVariableDeserializationError: If the data is invalid.
        """
        try:
            variable = data.get("variable")
            if variable is None:
                raise NestedVariableDeserializationError("Missing required field 'variable'")

            value_selector = data.get("value_selector")
            if value_selector is None:
                raise NestedVariableDeserializationError("Missing required field 'value_selector'")

            if not isinstance(value_selector, list):
                raise NestedVariableDeserializationError("Field 'value_selector' must be a list")

            return EnhancedVariableSelector(
                variable=variable,
                value_selector=value_selector,
            )
        except NestedVariableDeserializationError:
            raise
        except Exception as e:
            raise NestedVariableDeserializationError(f"Failed to deserialize variable selector: {e}")

    @classmethod
    def serialize_node_input(cls, node_input: NodeInputDefinition) -> dict[str, Any]:
        """
        Serialize a NodeInputDefinition to a dictionary.

        Args:
            node_input: The node input definition to serialize.

        Returns:
            A dictionary representation.
        """
        result: dict[str, Any] = {
            "name": node_input.name,
            "type": node_input.type.value,
            "required": node_input.required,
            "description": node_input.description,
        }

        if node_input.variable_selector:
            result["variable_selector"] = cls.serialize_variable_selector(node_input.variable_selector)

        if node_input.children:
            result["children"] = cls.serialize_definitions(node_input.children)

        if node_input.default_value is not None:
            result["default_value"] = node_input.default_value

        return result

    @classmethod
    def deserialize_node_input(cls, data: Mapping[str, Any]) -> NodeInputDefinition:
        """
        Deserialize a dictionary to a NodeInputDefinition.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A NodeInputDefinition instance.

        Raises:
            NestedVariableDeserializationError: If the data is invalid.
        """
        try:
            name = data.get("name")
            if not name:
                raise NestedVariableDeserializationError("Missing required field 'name'")

            type_str = data.get("type")
            if not type_str:
                raise NestedVariableDeserializationError("Missing required field 'type'")

            try:
                var_type = NestedVariableType(type_str)
            except ValueError:
                raise NestedVariableDeserializationError(f"Invalid variable type: {type_str}")

            variable_selector = None
            if data.get("variable_selector"):
                variable_selector = cls.deserialize_variable_selector(data["variable_selector"])

            children = None
            if data.get("children"):
                children = cls.deserialize_definitions(data["children"])

            return NodeInputDefinition(
                name=name,
                type=var_type,
                required=data.get("required", False),
                description=data.get("description", ""),
                variable_selector=variable_selector,
                children=children,
                default_value=data.get("default_value"),
            )
        except NestedVariableDeserializationError:
            raise
        except Exception as e:
            raise NestedVariableDeserializationError(f"Failed to deserialize node input definition: {e}")

    @classmethod
    def serialize_node_output(cls, node_output: NodeOutputDefinition) -> dict[str, Any]:
        """
        Serialize a NodeOutputDefinition to a dictionary.

        Args:
            node_output: The node output definition to serialize.

        Returns:
            A dictionary representation.
        """
        result: dict[str, Any] = {
            "name": node_output.name,
            "type": node_output.type.value,
            "description": node_output.description,
        }

        if node_output.children:
            result["children"] = cls.serialize_definitions(node_output.children)

        return result

    @classmethod
    def deserialize_node_output(cls, data: Mapping[str, Any]) -> NodeOutputDefinition:
        """
        Deserialize a dictionary to a NodeOutputDefinition.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A NodeOutputDefinition instance.

        Raises:
            NestedVariableDeserializationError: If the data is invalid.
        """
        try:
            name = data.get("name")
            if not name:
                raise NestedVariableDeserializationError("Missing required field 'name'")

            type_str = data.get("type")
            if not type_str:
                raise NestedVariableDeserializationError("Missing required field 'type'")

            try:
                var_type = NestedVariableType(type_str)
            except ValueError:
                raise NestedVariableDeserializationError(f"Invalid variable type: {type_str}")

            children = None
            if data.get("children"):
                children = cls.deserialize_definitions(data["children"])

            return NodeOutputDefinition(
                name=name,
                type=var_type,
                description=data.get("description", ""),
                children=children,
            )
        except NestedVariableDeserializationError:
            raise
        except Exception as e:
            raise NestedVariableDeserializationError(f"Failed to deserialize node output definition: {e}")

    @classmethod
    def is_nested_variable_data(cls, data: Mapping[str, Any]) -> bool:
        """
        Check if the data represents a nested variable definition.

        This is used for backward compatibility to distinguish between
        old-style flat variable definitions and new nested definitions.

        Args:
            data: The dictionary to check.

        Returns:
            True if the data contains nested variable indicators.
        """
        # Check if the type is one of the nested variable types
        type_str = data.get("type")
        if type_str:
            try:
                var_type = NestedVariableType(type_str)
                # If it has children or is a nestable type with children field
                if "children" in data:
                    return True
                # If the type is from our NestedVariableType enum
                return var_type in NestedVariableType
            except ValueError:
                pass
        return False

    @classmethod
    def validate_serialized_definition(cls, data: Mapping[str, Any]) -> list[str]:
        """
        Validate a serialized nested variable definition.

        Args:
            data: The dictionary to validate.

        Returns:
            A list of validation error messages, empty if valid.
        """
        errors: list[str] = []

        if not data.get("name"):
            errors.append("Missing required field 'name'")

        type_str = data.get("type")
        if not type_str:
            errors.append("Missing required field 'type'")
        else:
            try:
                var_type = NestedVariableType(type_str)

                # Validate children only allowed for nestable types
                if data.get("children"):
                    if not var_type.is_nestable():
                        errors.append(f"Children not allowed for type '{type_str}'")
                    else:
                        # Recursively validate children
                        for i, child in enumerate(data["children"]):
                            child_errors = cls.validate_serialized_definition(child)
                            for err in child_errors:
                                errors.append(f"children[{i}]: {err}")

                        # Check for duplicate child names
                        child_names = [c.get("name") for c in data["children"] if c.get("name")]
                        if len(child_names) != len(set(child_names)):
                            errors.append("Duplicate child variable names")

            except ValueError:
                errors.append(f"Invalid variable type: {type_str}")

        return errors
