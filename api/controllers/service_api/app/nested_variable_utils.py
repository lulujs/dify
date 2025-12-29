"""
Utility functions for handling nested variables in service API workflow requests.

This module provides validation utilities for nested variable inputs
in workflow execution requests.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from core.workflow.entities.nested_variable import (
    NestedVariableDefinition,
)
from core.workflow.validators.nested_variable_validator import (
    NestedVariableValidator,
    ValidationError,
)
from models.workflow import Workflow
from services.workflow_service import WorkflowService


class NestedVariableInputValidationError(ValueError):
    """Exception raised when nested variable input validation fails."""

    def __init__(self, errors: list[ValidationError]):
        self.errors = errors
        messages = [str(e) for e in errors]
        super().__init__(f"Nested variable input validation failed: {'; '.join(messages)}")


def extract_nested_variable_definitions_from_workflow(
    workflow: Workflow,
) -> list[NestedVariableDefinition]:
    """
    Extract nested variable definitions from a workflow's start node.

    Args:
        workflow: The workflow to extract definitions from

    Returns:
        List of nested variable definitions from the start node
    """
    graph = workflow.graph_dict
    nodes = graph.get("nodes", [])

    for node in nodes:
        node_data = node.get("data", {})
        node_type = node_data.get("type")

        # Look for start node
        if node_type == "start":
            variables = node_data.get("variables", [])
            definitions = []

            for var in variables:
                if isinstance(var, dict):
                    # Check if this variable has nested children
                    if var.get("children"):
                        try:
                            definition = NestedVariableDefinition.model_validate(var)
                            definitions.append(definition)
                        except ValueError:
                            # Skip invalid definitions
                            pass

            return definitions

    return []


def validate_nested_inputs(
    inputs: Mapping[str, Any],
    definitions: Sequence[NestedVariableDefinition],
) -> list[ValidationError]:
    """
    Validate input values against nested variable definitions.

    Args:
        inputs: Input values to validate
        definitions: Nested variable definitions to validate against

    Returns:
        List of validation errors, empty if all validations pass
    """
    return NestedVariableValidator.validate_values(dict(inputs), definitions)


def validate_workflow_nested_inputs(
    app_model: Any,
    inputs: Mapping[str, Any],
    workflow_id: str | None = None,
) -> None:
    """
    Validate workflow inputs against nested variable definitions.

    This function extracts nested variable definitions from the workflow
    and validates the provided inputs against them.

    Args:
        app_model: The app model
        inputs: Input values to validate
        workflow_id: Optional specific workflow ID to use

    Raises:
        NestedVariableInputValidationError: If validation fails
    """
    workflow_service = WorkflowService()

    # Get the workflow
    if workflow_id:
        workflow = workflow_service.get_published_workflow_by_id(
            app_model=app_model,
            workflow_id=workflow_id,
        )
    else:
        workflow = workflow_service.get_published_workflow(app_model=app_model)

    if not workflow:
        return  # No workflow to validate against

    # Extract nested variable definitions
    definitions = extract_nested_variable_definitions_from_workflow(workflow)

    if not definitions:
        return  # No nested variables to validate

    # Validate inputs
    errors = validate_nested_inputs(inputs, definitions)

    if errors:
        raise NestedVariableInputValidationError(errors)
