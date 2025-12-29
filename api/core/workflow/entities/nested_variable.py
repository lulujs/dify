"""
Nested Variable entities for workflow nodes.

This module provides data structures for defining nested/hierarchical variables
that can contain child variables, enabling complex object and array structures
in workflow node inputs and outputs.
"""

import re
from collections.abc import Sequence
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_NESTING_DEPTH = 5


class NestedVariableType(StrEnum):
    """Supported types for nested variables."""

    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    FILE = "file"
    ARRAY_STRING = "array[string]"
    ARRAY_INTEGER = "array[integer]"
    ARRAY_NUMBER = "array[number]"
    ARRAY_OBJECT = "array[object]"
    ARRAY_BOOLEAN = "array[boolean]"
    ARRAY_FILE = "array[file]"

    def is_nestable(self) -> bool:
        """Check if this type supports child variables."""
        return self in (NestedVariableType.OBJECT, NestedVariableType.ARRAY_OBJECT)

    def is_array(self) -> bool:
        """Check if this is an array type."""
        return self.value.startswith("array[")


# Regex pattern for valid variable names: starts with letter, contains only alphanumeric and underscores
VARIABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


class NestedVariableDefinition(BaseModel):
    """
    Definition of a nested variable.

    Supports hierarchical structures where Object and Array<Object> types
    can contain child variable definitions.
    """

    name: str = Field(description="Variable name")
    type: NestedVariableType = Field(description="Variable type")
    required: bool = Field(default=False, description="Whether the variable is required")
    description: str = Field(default="", description="Variable description")
    default_value: Any = Field(default=None, description="Default value")
    children: Sequence["NestedVariableDefinition"] | None = Field(
        default=None,
        description="Child variable definitions, only for object and array[object] types",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that variable name follows the required pattern."""
        if not VARIABLE_NAME_PATTERN.match(v):
            raise ValueError(
                f"Variable name '{v}' must start with a letter and contain only alphanumeric characters and underscores"
            )
        return v

    @model_validator(mode="after")
    def validate_children_for_type(self) -> "NestedVariableDefinition":
        """Validate that children are only allowed for nestable types."""
        if self.children is not None and len(self.children) > 0:
            if not self.type.is_nestable():
                raise ValueError(f"Children are only allowed for 'object' and 'array[object]' types, got '{self.type}'")
            # Validate child variable names are unique within the same parent
            names = [child.name for child in self.children]
            if len(names) != len(set(names)):
                duplicates = [name for name in names if names.count(name) > 1]
                raise ValueError(
                    f"Child variable names must be unique within the same parent. Duplicates: {set(duplicates)}"
                )
        return self

    def get_max_depth(self) -> int:
        """Calculate the maximum nesting depth of this variable definition."""
        if not self.children:
            return 1
        return 1 + max(child.get_max_depth() for child in self.children)

    def validate_depth(self, max_depth: int = MAX_NESTING_DEPTH) -> list[str]:
        """
        Validate that nesting depth does not exceed the maximum.

        Returns:
            List of error messages, empty if validation passes.
        """
        errors: list[str] = []
        current_depth = self.get_max_depth()
        if current_depth > max_depth:
            errors.append(f"Maximum nesting depth of {max_depth} exceeded at '{self.name}' (depth: {current_depth})")
        return errors

    def __repr__(self) -> str:
        children_count = len(self.children) if self.children else 0
        return f"NestedVariableDefinition(name={self.name!r}, type={self.type}, children={children_count})"


# Rebuild model to allow recursive type references
NestedVariableDefinition.model_rebuild()
