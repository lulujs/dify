"""
Utility functions for handling nested variables in workflow API requests.

This module provides validation and conversion utilities for nested variable
definitions in workflow node configurations.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from core.workflow.entities.nested_variable import (
    MAX_NESTING_DEPTH,
    NestedVariableDefinition,
    NestedVariableType,
)
from core.workflow.validators.nested_variable_validator import (
    NestedVariableValidator,
    ValidationError,
)


class NestedVariableValidationError(ValueError):
    """Exception raised when nested variable validation fails."""

    def __init__(self, errors: list[ValidationError]):
        self.errors = errors
        messages = [str(e) for e in errors]
        super().__init__(f"Nested variable validation failed: {'; '.join(messages)}")


def parse_nested_variable_definition(data: Mapping[str, Any]) -> NestedVariableDefinition:
    """
    Parse a nested variable definition from a dictionary.

    Args:
        data: Dictionary containing nested variable definition data

    Returns:
        NestedVariableDefinition instance

    Raises:
        ValueError: If the data is invalid
    """
    return NestedVariableDefinition.model_validate(data)


def parse_nested_variable_definitions(
    data_list: Sequence[Mapping[str, Any]],
) -> list[NestedVariableDefinition]:
    """
    Parse a list of nested variable definitions from dictionaries.

    Args:
        data_list: List of dictionaries containing nested variable definition data

    Returns:
        List of NestedVariableDefinition instances

    Raises:
        ValueError: If any definition is invalid
    """
    return [parse_nested_variable_definition(data) for data in data_list]


def validate_nested_variable_definitions(
    definitions: Sequence[NestedVariableDefinition],
) -> None:
    """
    Validate a list of nested variable definitions.

    Args:
        definitions: List of nested variable definitions to validate

    Raises:
        NestedVariableValidationError: If validation fails
    """
    errors = NestedVariableValidator.validate_definitions(definitions)
    if errors:
        raise NestedVariableValidationError(errors)


def validate_nested_variable_values(
    values: dict[str, Any],
    definitions: Sequence[NestedVariableDefinition],
) -> None:
    """
    Validate runtime values against their nested variable definitions.

    Args:
        values: Dictionary mapping variable names to values
        definitions: List of nested variable definitions

    Raises:
        NestedVariableValidationError: If validation fails
    """
    errors = NestedVariableValidator.validate_values(values, definitions)
    if errors:
        raise NestedVariableValidationError(errors)


def extract_nested_variables_from_graph(graph: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """
    Extract nested variable definitions from a workflow graph.

    Scans all nodes in the graph and extracts any nested variable definitions
    from their configurations.

    Args:
        graph: Workflow graph dictionary

    Returns:
        Dictionary mapping node IDs to their nested variable definitions
    """
    result: dict[str, list[dict[str, Any]]] = {}

    nodes = graph.get("nodes", [])
    for node in nodes:
        node_id = node.get("id")
        node_data = node.get("data", {})

        # Check for variables with nested structure
        variables = node_data.get("variables", [])
        nested_vars = []

        for var in variables:
            if isinstance(var, dict) and var.get("children"):
                nested_vars.append(var)

        if nested_vars:
            result[node_id] = nested_vars

    return result


def validate_graph_nested_variables(graph: dict[str, Any]) -> list[ValidationError]:
    """
    Validate all nested variable definitions in a workflow graph.

    Only validates variables that:
    1. Have non-empty children array
    2. Use nestable types (object or array[object])

    Args:
        graph: Workflow graph dictionary

    Returns:
        List of validation errors, empty if all validations pass
    """
    all_errors: list[ValidationError] = []

    nodes = graph.get("nodes", [])
    for node in nodes:
        node_id = node.get("id", "unknown")
        node_data = node.get("data", {})

        # Check for variables with nested structure
        variables = node_data.get("variables", [])

        for var in variables:
            if isinstance(var, dict):
                # Only validate variables that have children and use nestable types
                children = var.get("children")
                var_type = var.get("type", "")

                # Skip validation for non-nested variables
                if not children or len(children) == 0:
                    continue

                # Skip validation for non-nestable types
                if not is_nested_variable_type(var_type):
                    continue

                try:
                    # Convert frontend format to NestedVariableDefinition format
                    # Frontend uses 'variable' field, NestedVariableDefinition uses 'name'
                    converted_var = _convert_to_nested_definition_format(var)
                    definition = parse_nested_variable_definition(converted_var)
                    errors = NestedVariableValidator.validate_definition(definition)
                    # Add node context to errors
                    for error in errors:
                        error.path = f"node[{node_id}].{error.path}"
                    all_errors.extend(errors)
                except ValueError as e:
                    all_errors.append(
                        ValidationError(
                            path=f"node[{node_id}].{var.get('variable', var.get('name', 'unknown'))}",
                            message=str(e),
                            error_code="INVALID_DEFINITION",
                        )
                    )

    return all_errors


def _convert_to_nested_definition_format(var: dict[str, Any]) -> dict[str, Any]:
    """
    Convert frontend variable format to NestedVariableDefinition format.

    Frontend uses 'variable' field, NestedVariableDefinition uses 'name'.
    Frontend uses different type names that need to be mapped.
    Also converts children recursively.

    Args:
        var: Variable dictionary in frontend format

    Returns:
        Variable dictionary in NestedVariableDefinition format
    """
    # Map frontend types to NestedVariableType values
    type_mapping = {
        # Frontend types -> NestedVariableType values
        "text-input": "string",
        "paragraph": "string",
        "select": "string",
        "number": "number",
        "checkbox": "boolean",
        "file": "file",
        "file-list": "array[file]",
    }

    frontend_type = var.get("type", "")
    mapped_type = type_mapping.get(frontend_type, frontend_type)

    result: dict[str, Any] = {
        "name": var.get("variable", var.get("name", "")),
        "type": mapped_type,
        "required": var.get("required", False),
        "description": var.get("description", ""),
    }

    if "default_value" in var:
        result["default_value"] = var["default_value"]
    elif "default" in var:
        result["default_value"] = var["default"]

    children = var.get("children")
    if children and len(children) > 0:
        result["children"] = [_convert_to_nested_definition_format(child) for child in children]

    return result


def serialize_nested_variable_definition(
    definition: NestedVariableDefinition,
) -> dict[str, Any]:
    """
    Serialize a nested variable definition to a dictionary.

    Args:
        definition: NestedVariableDefinition to serialize

    Returns:
        Dictionary representation of the definition
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
        result["children"] = [serialize_nested_variable_definition(child) for child in definition.children]

    return result


def is_nested_variable_type(type_str: str) -> bool:
    """
    Check if a type string represents a nestable variable type.

    Args:
        type_str: Variable type string

    Returns:
        True if the type supports nested children
    """
    # Check against NestedVariableType
    try:
        var_type = NestedVariableType(type_str)
        return var_type.is_nestable()
    except ValueError:
        pass

    return type_str in ("object", "array[object]")


def get_max_nesting_depth() -> int:
    """
    Get the maximum allowed nesting depth for nested variables.

    Returns:
        Maximum nesting depth
    """
    return MAX_NESTING_DEPTH
