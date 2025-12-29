"""
Unit tests for NestedVariableValidator.

Tests cover:
- Definition validation (depth, children types, duplicate names)
- Value validation (required fields, type checking, nested structures)
"""

from core.workflow.entities.nested_variable import (
    MAX_NESTING_DEPTH,
    NestedVariableDefinition,
    NestedVariableType,
)
from core.workflow.validators.nested_variable_validator import (
    NestedVariableValidator,
    ValidationError,
)


class TestValidationError:
    """Tests for ValidationError dataclass."""

    def test_str_representation(self):
        error = ValidationError(
            path="user.profile.name",
            message="Required field is missing",
            error_code="REQUIRED_FIELD_MISSING",
        )
        assert str(error) == "REQUIRED_FIELD_MISSING: Required field is missing at 'user.profile.name'"


class TestValidateDefinition:
    """Tests for validate_definition method."""

    def test_valid_simple_definition(self):
        definition = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_definition(definition)
        assert len(errors) == 0

    def test_valid_nested_definition(self):
        definition = NestedVariableDefinition(
            name="user",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="age",
                    type=NestedVariableType.INTEGER,
                    required=False,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_definition(definition)
        assert len(errors) == 0

    def test_max_depth_exceeded(self):
        # Create a deeply nested structure that exceeds MAX_NESTING_DEPTH
        def create_nested(depth: int) -> NestedVariableDefinition:
            if depth == 0:
                return NestedVariableDefinition(
                    name=f"level_{depth}",
                    type=NestedVariableType.STRING,
                )
            return NestedVariableDefinition(
                name=f"level_{depth}",
                type=NestedVariableType.OBJECT,
                children=[create_nested(depth - 1)],
            )

        # Create structure with depth = MAX_NESTING_DEPTH + 1
        definition = create_nested(MAX_NESTING_DEPTH + 1)
        errors = NestedVariableValidator.validate_definition(definition)

        # Should have at least one depth error
        depth_errors = [e for e in errors if e.error_code == NestedVariableValidator.ERROR_MAX_DEPTH_EXCEEDED]
        assert len(depth_errors) > 0

    def test_children_on_non_nestable_type(self):
        # This should be caught by pydantic validation, but we test the validator too
        # We need to bypass pydantic validation to test this
        definition = NestedVariableDefinition(
            name="invalid",
            type=NestedVariableType.OBJECT,  # Use valid type first
            children=[
                NestedVariableDefinition(
                    name="child",
                    type=NestedVariableType.STRING,
                ),
            ],
        )
        # Manually change type to test validator
        object.__setattr__(definition, "type", NestedVariableType.STRING)

        errors = NestedVariableValidator.validate_definition(definition)
        invalid_children_errors = [
            e for e in errors if e.error_code == NestedVariableValidator.ERROR_INVALID_CHILDREN_TYPE
        ]
        assert len(invalid_children_errors) == 1


class TestValidateDefinitions:
    """Tests for validate_definitions method."""

    def test_valid_definitions_list(self):
        definitions = [
            NestedVariableDefinition(
                name="name",
                type=NestedVariableType.STRING,
                required=True,
            ),
            NestedVariableDefinition(
                name="age",
                type=NestedVariableType.INTEGER,
                required=False,
            ),
        ]
        errors = NestedVariableValidator.validate_definitions(definitions)
        assert len(errors) == 0

    def test_duplicate_names_at_root(self):
        definitions = [
            NestedVariableDefinition(
                name="name",
                type=NestedVariableType.STRING,
            ),
            NestedVariableDefinition(
                name="name",  # Duplicate
                type=NestedVariableType.INTEGER,
            ),
        ]
        errors = NestedVariableValidator.validate_definitions(definitions)
        duplicate_errors = [e for e in errors if e.error_code == NestedVariableValidator.ERROR_DUPLICATE_CHILD_NAME]
        assert len(duplicate_errors) == 1


class TestValidateValue:
    """Tests for validate_value method."""

    def test_valid_string_value(self):
        definition = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_value("john_doe", definition)
        assert len(errors) == 0

    def test_required_field_missing(self):
        definition = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(None, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_REQUIRED_FIELD_MISSING

    def test_optional_field_missing(self):
        definition = NestedVariableDefinition(
            name="nickname",
            type=NestedVariableType.STRING,
            required=False,
        )
        errors = NestedVariableValidator.validate_value(None, definition)
        assert len(errors) == 0

    def test_type_mismatch_string(self):
        definition = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(123, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_type_mismatch_integer_with_bool(self):
        """Boolean should not be accepted as integer."""
        definition = NestedVariableDefinition(
            name="count",
            type=NestedVariableType.INTEGER,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(True, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_valid_integer_value(self):
        definition = NestedVariableDefinition(
            name="count",
            type=NestedVariableType.INTEGER,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(42, definition)
        assert len(errors) == 0

    def test_valid_number_value(self):
        definition = NestedVariableDefinition(
            name="price",
            type=NestedVariableType.NUMBER,
            required=True,
        )
        # Both int and float should be valid for NUMBER type
        errors_int = NestedVariableValidator.validate_value(42, definition)
        errors_float = NestedVariableValidator.validate_value(42.5, definition)
        assert len(errors_int) == 0
        assert len(errors_float) == 0

    def test_type_mismatch_number_with_bool(self):
        """Boolean should not be accepted as number."""
        definition = NestedVariableDefinition(
            name="price",
            type=NestedVariableType.NUMBER,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(False, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_valid_boolean_value(self):
        definition = NestedVariableDefinition(
            name="active",
            type=NestedVariableType.BOOLEAN,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(True, definition)
        assert len(errors) == 0

    def test_valid_object_value(self):
        definition = NestedVariableDefinition(
            name="user",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value({"name": "John"}, definition)
        assert len(errors) == 0

    def test_nested_required_field_missing(self):
        definition = NestedVariableDefinition(
            name="user",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value({}, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_REQUIRED_FIELD_MISSING
        assert "user.name" in errors[0].path

    def test_nested_type_mismatch(self):
        definition = NestedVariableDefinition(
            name="user",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="age",
                    type=NestedVariableType.INTEGER,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value({"age": "not_a_number"}, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_valid_array_string(self):
        definition = NestedVariableDefinition(
            name="tags",
            type=NestedVariableType.ARRAY_STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(["tag1", "tag2"], definition)
        assert len(errors) == 0

    def test_array_string_with_invalid_element(self):
        definition = NestedVariableDefinition(
            name="tags",
            type=NestedVariableType.ARRAY_STRING,
            required=True,
        )
        errors = NestedVariableValidator.validate_value(["tag1", 123], definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_valid_array_object(self):
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value(
            [{"name": "John"}, {"name": "Jane"}],
            definition,
        )
        assert len(errors) == 0

    def test_array_object_with_missing_required_field(self):
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value(
            [{"name": "John"}, {}],  # Second element missing required field
            definition,
        )
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_REQUIRED_FIELD_MISSING
        assert "users[1].name" in errors[0].path

    def test_array_object_with_non_object_element(self):
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        errors = NestedVariableValidator.validate_value(
            [{"name": "John"}, "not_an_object"],
            definition,
        )
        assert len(errors) == 1
        # Non-object element in array[object] is caught as TYPE_MISMATCH during array element validation
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH


class TestValidateValues:
    """Tests for validate_values method."""

    def test_valid_values_dict(self):
        definitions = [
            NestedVariableDefinition(
                name="name",
                type=NestedVariableType.STRING,
                required=True,
            ),
            NestedVariableDefinition(
                name="age",
                type=NestedVariableType.INTEGER,
                required=False,
            ),
        ]
        values = {"name": "John", "age": 30}
        errors = NestedVariableValidator.validate_values(values, definitions)
        assert len(errors) == 0

    def test_missing_required_value(self):
        definitions = [
            NestedVariableDefinition(
                name="name",
                type=NestedVariableType.STRING,
                required=True,
            ),
        ]
        values: dict[str, str] = {}
        errors = NestedVariableValidator.validate_values(values, definitions)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_REQUIRED_FIELD_MISSING


class TestArrayElementValidation:
    """Tests for array element type validation."""

    def test_array_integer_with_bool_element(self):
        """Boolean should not be accepted in integer array."""
        definition = NestedVariableDefinition(
            name="numbers",
            type=NestedVariableType.ARRAY_INTEGER,
            required=True,
        )
        errors = NestedVariableValidator.validate_value([1, 2, True], definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_array_number_with_bool_element(self):
        """Boolean should not be accepted in number array."""
        definition = NestedVariableDefinition(
            name="numbers",
            type=NestedVariableType.ARRAY_NUMBER,
            required=True,
        )
        errors = NestedVariableValidator.validate_value([1.5, 2, False], definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

    def test_valid_array_boolean(self):
        definition = NestedVariableDefinition(
            name="flags",
            type=NestedVariableType.ARRAY_BOOLEAN,
            required=True,
        )
        errors = NestedVariableValidator.validate_value([True, False, True], definition)
        assert len(errors) == 0
