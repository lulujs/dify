"""
Nested Variable Validator for workflow nodes.

This module provides validation utilities for nested variable definitions
and runtime values, ensuring they conform to the expected structure and types.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Final, override

from core.workflow.entities.nested_variable import (
    MAX_NESTING_DEPTH,
    NestedVariableDefinition,
    NestedVariableType,
)


@dataclass
class ValidationError:
    """Represents a validation error with path and details."""

    path: str
    message: str
    error_code: str

    @override
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message} at '{self.path}'"


class NestedVariableValidator:
    """
    Validator for nested variable definitions and values.

    Provides methods to validate:
    - Variable definitions (structure, depth, naming)
    - Runtime values against definitions (type checking, required fields)
    """

    # Error codes
    ERROR_MAX_DEPTH_EXCEEDED: Final[str] = "MAX_DEPTH_EXCEEDED"
    ERROR_INVALID_CHILDREN_TYPE: Final[str] = "INVALID_CHILDREN_TYPE"
    ERROR_DUPLICATE_CHILD_NAME: Final[str] = "DUPLICATE_CHILD_NAME"
    ERROR_REQUIRED_FIELD_MISSING: Final[str] = "REQUIRED_FIELD_MISSING"
    ERROR_TYPE_MISMATCH: Final[str] = "TYPE_MISMATCH"
    ERROR_INVALID_ARRAY_ELEMENT: Final[str] = "INVALID_ARRAY_ELEMENT"

    @classmethod
    def validate_definition(
        cls,
        definition: NestedVariableDefinition,
        current_depth: int = 1,
        path: str = "",
    ) -> list[ValidationError]:
        """
        Validate a nested variable definition.

        Checks:
        - Nesting depth does not exceed MAX_NESTING_DEPTH
        - Children are only present for nestable types (object, array[object])
        - Child variable names are unique within the same parent

        Args:
            definition: The variable definition to validate
            current_depth: Current nesting depth (starts at 1)
            path: Current path for error reporting

        Returns:
            List of ValidationError objects, empty if validation passes
        """
        errors: list[ValidationError] = []
        current_path = f"{path}.{definition.name}" if path else definition.name

        # Check nesting depth
        if current_depth > MAX_NESTING_DEPTH:
            errors.append(
                ValidationError(
                    path=current_path,
                    message=f"Maximum nesting depth of {MAX_NESTING_DEPTH} exceeded",
                    error_code=cls.ERROR_MAX_DEPTH_EXCEEDED,
                )
            )
            return errors

        # Validate children
        if definition.children:
            # Check if type supports children
            if not definition.type.is_nestable():
                errors.append(
                    ValidationError(
                        path=current_path,
                        message=f"Type '{definition.type}' does not support children",
                        error_code=cls.ERROR_INVALID_CHILDREN_TYPE,
                    )
                )
            else:
                # Check for duplicate child names
                names = [child.name for child in definition.children]
                seen: set[str] = set()
                duplicates: set[str] = set()
                for name in names:
                    if name in seen:
                        duplicates.add(name)
                    seen.add(name)

                if duplicates:
                    errors.append(
                        ValidationError(
                            path=current_path,
                            message=f"Duplicate child names: {duplicates}",
                            error_code=cls.ERROR_DUPLICATE_CHILD_NAME,
                        )
                    )

                # Recursively validate children
                for child in definition.children:
                    child_errors = cls.validate_definition(
                        child,
                        current_depth=current_depth + 1,
                        path=current_path,
                    )
                    errors.extend(child_errors)

        return errors

    @classmethod
    def validate_definitions(
        cls,
        definitions: Sequence[NestedVariableDefinition],
    ) -> list[ValidationError]:
        """
        Validate a list of nested variable definitions.

        Args:
            definitions: List of variable definitions to validate

        Returns:
            List of ValidationError objects, empty if all validations pass
        """
        errors: list[ValidationError] = []

        # Check for duplicate names at root level
        names = [d.name for d in definitions]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for name in names:
            if name in seen:
                duplicates.add(name)
            seen.add(name)

        if duplicates:
            errors.append(
                ValidationError(
                    path="",
                    message=f"Duplicate variable names at root level: {duplicates}",
                    error_code=cls.ERROR_DUPLICATE_CHILD_NAME,
                )
            )

        # Validate each definition
        for definition in definitions:
            definition_errors = cls.validate_definition(definition)
            errors.extend(definition_errors)

        return errors

    @classmethod
    def validate_value(
        cls,
        value: Any,
        definition: NestedVariableDefinition,
        path: str = "",
    ) -> list[ValidationError]:
        """
        Validate a runtime value against its definition.

        Checks:
        - Required fields are present
        - Values match expected types
        - Nested structures conform to their definitions

        Args:
            value: The runtime value to validate
            definition: The variable definition to validate against
            path: Current path for error reporting

        Returns:
            List of ValidationError objects, empty if validation passes
        """
        errors: list[ValidationError] = []
        current_path = f"{path}.{definition.name}" if path else definition.name

        # Check required field
        if value is None:
            if definition.required:
                errors.append(
                    ValidationError(
                        path=current_path,
                        message="Required field is missing",
                        error_code=cls.ERROR_REQUIRED_FIELD_MISSING,
                    )
                )
            return errors

        # Type validation
        type_error = cls._validate_type(value, definition.type, current_path)
        if type_error:
            errors.append(type_error)
            return errors

        # Validate nested children for object types
        if definition.children and isinstance(value, dict):
            for child_def in definition.children:
                child_value = value.get(child_def.name)
                child_errors = cls.validate_value(child_value, child_def, current_path)
                errors.extend(child_errors)

        # Validate array elements for array[object] type
        if definition.type == NestedVariableType.ARRAY_OBJECT and definition.children:
            if isinstance(value, list):
                for i, item in enumerate(value):
                    item_path = f"{current_path}[{i}]"
                    if not isinstance(item, dict):
                        errors.append(
                            ValidationError(
                                path=item_path,
                                message="Array element must be an object",
                                error_code=cls.ERROR_INVALID_ARRAY_ELEMENT,
                            )
                        )
                    else:
                        for child_def in definition.children:
                            child_value = item.get(child_def.name)
                            child_errors = cls.validate_value(child_value, child_def, item_path)
                            errors.extend(child_errors)

        return errors

    @classmethod
    def validate_values(
        cls,
        values: dict[str, Any],
        definitions: Sequence[NestedVariableDefinition],
    ) -> list[ValidationError]:
        """
        Validate a dictionary of values against their definitions.

        Args:
            values: Dictionary mapping variable names to values
            definitions: List of variable definitions

        Returns:
            List of ValidationError objects, empty if all validations pass
        """
        errors: list[ValidationError] = []

        for definition in definitions:
            value = values.get(definition.name)
            value_errors = cls.validate_value(value, definition)
            errors.extend(value_errors)

        return errors

    @classmethod
    def _validate_type(
        cls,
        value: Any,
        expected_type: NestedVariableType,
        path: str,
    ) -> ValidationError | None:
        """
        Validate that a value matches the expected type.

        Args:
            value: The value to check
            expected_type: The expected variable type
            path: Current path for error reporting

        Returns:
            ValidationError if type mismatch, None otherwise
        """
        type_validators: dict[NestedVariableType, tuple[type | tuple[type, ...], str]] = {
            NestedVariableType.STRING: (str, "string"),
            NestedVariableType.INTEGER: (int, "integer"),
            NestedVariableType.NUMBER: ((int, float), "number"),
            NestedVariableType.BOOLEAN: (bool, "boolean"),
            NestedVariableType.OBJECT: (dict, "object"),
            NestedVariableType.ARRAY_STRING: (list, "array[string]"),
            NestedVariableType.ARRAY_INTEGER: (list, "array[integer]"),
            NestedVariableType.ARRAY_NUMBER: (list, "array[number]"),
            NestedVariableType.ARRAY_OBJECT: (list, "array[object]"),
            NestedVariableType.ARRAY_BOOLEAN: (list, "array[boolean]"),
            NestedVariableType.ARRAY_FILE: (list, "array[file]"),
        }

        validator = type_validators.get(expected_type)
        if validator:
            expected_python_type, type_name = validator

            # Special case: bool is a subclass of int in Python
            if expected_type == NestedVariableType.INTEGER and isinstance(value, bool):
                return ValidationError(
                    path=path,
                    message=f"Expected {type_name}, got boolean",
                    error_code=cls.ERROR_TYPE_MISMATCH,
                )

            # Special case: for NUMBER type, exclude bool
            if expected_type == NestedVariableType.NUMBER and isinstance(value, bool):
                return ValidationError(
                    path=path,
                    message=f"Expected {type_name}, got boolean",
                    error_code=cls.ERROR_TYPE_MISMATCH,
                )

            if not isinstance(value, expected_python_type):
                return ValidationError(
                    path=path,
                    message=f"Expected {type_name}, got {type(value).__name__}",
                    error_code=cls.ERROR_TYPE_MISMATCH,
                )

            # Additional validation for array element types
            if expected_type.is_array() and isinstance(value, list):
                element_error = cls._validate_array_elements(value, expected_type, path)
                if element_error:
                    return element_error

        return None

    @classmethod
    def _validate_array_elements(
        cls,
        value: list[Any],
        array_type: NestedVariableType,
        path: str,
    ) -> ValidationError | None:
        """
        Validate that array elements match the expected element type.

        Args:
            value: The array value
            array_type: The array type (e.g., array[string])
            path: Current path for error reporting

        Returns:
            ValidationError if element type mismatch, None otherwise
        """
        element_type_map: dict[NestedVariableType, tuple[type | tuple[type, ...], str]] = {
            NestedVariableType.ARRAY_STRING: (str, "string"),
            NestedVariableType.ARRAY_INTEGER: (int, "integer"),
            NestedVariableType.ARRAY_NUMBER: ((int, float), "number"),
            NestedVariableType.ARRAY_BOOLEAN: (bool, "boolean"),
            NestedVariableType.ARRAY_OBJECT: (dict, "object"),
        }

        element_validator = element_type_map.get(array_type)
        if element_validator:
            expected_element_type, element_type_name = element_validator

            for i, element in enumerate(value):
                # Special case: bool is a subclass of int
                if array_type == NestedVariableType.ARRAY_INTEGER and isinstance(element, bool):
                    return ValidationError(
                        path=f"{path}[{i}]",
                        message=f"Array element expected {element_type_name}, got boolean",
                        error_code=cls.ERROR_TYPE_MISMATCH,
                    )

                # Special case: for NUMBER array, exclude bool
                if array_type == NestedVariableType.ARRAY_NUMBER and isinstance(element, bool):
                    return ValidationError(
                        path=f"{path}[{i}]",
                        message=f"Array element expected {element_type_name}, got boolean",
                        error_code=cls.ERROR_TYPE_MISMATCH,
                    )

                if not isinstance(element, expected_element_type):
                    return ValidationError(
                        path=f"{path}[{i}]",
                        message=f"Array element expected {element_type_name}, got {type(element).__name__}",
                        error_code=cls.ERROR_TYPE_MISMATCH,
                    )

        return None

    @override
    def __repr__(self) -> str:
        return "NestedVariableValidator()"
