"""
Node Input and Output definition entities for workflow nodes.

This module provides enhanced data structures for defining node inputs and outputs
with support for nested variable structures and variable selectors.
"""

from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel, Field

from .nested_variable import NestedVariableDefinition, NestedVariableType


class EnhancedVariableSelector(BaseModel):
    """
    Enhanced variable selector with support for nested paths.

    Allows referencing nested values from upstream node outputs using
    dot-notation paths (e.g., node_id.user.profile.name).
    """

    variable: str = Field(description="Variable reference string")
    value_selector: Sequence[str] = Field(description="Variable selector path segments")

    def get_full_path(self) -> str:
        """Get the complete path as a dot-separated string."""
        return ".".join(self.value_selector)

    def __repr__(self) -> str:
        return f"EnhancedVariableSelector(path={self.get_full_path()!r})"


class NodeInputDefinition(BaseModel):
    """
    Definition of a node input.

    Supports both simple and nested variable structures, with optional
    variable selector for referencing upstream node outputs.
    """

    name: str = Field(description="Input name")
    type: NestedVariableType = Field(description="Input type")
    required: bool = Field(default=False, description="Whether the input is required")
    description: str = Field(default="", description="Input description")
    variable_selector: EnhancedVariableSelector | None = Field(
        default=None,
        description="Variable selector for referencing upstream outputs",
    )
    children: Sequence[NestedVariableDefinition] | None = Field(
        default=None,
        description="Child variable definitions for object and array[object] types",
    )
    default_value: Any = Field(default=None, description="Default value")

    def __repr__(self) -> str:
        return f"NodeInputDefinition(name={self.name!r}, type={self.type}, required={self.required})"


class NodeOutputDefinition(BaseModel):
    """
    Definition of a node output.

    Supports both simple and nested variable structures for defining
    the output schema of a workflow node.
    """

    name: str = Field(description="Output name")
    type: NestedVariableType = Field(description="Output type")
    description: str = Field(default="", description="Output description")
    children: Sequence[NestedVariableDefinition] | None = Field(
        default=None,
        description="Child variable definitions for object and array[object] types",
    )

    def __repr__(self) -> str:
        return f"NodeOutputDefinition(name={self.name!r}, type={self.type})"
