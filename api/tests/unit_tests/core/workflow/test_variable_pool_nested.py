"""
Unit tests for nested variable support in VariablePool.

Tests the add_nested, get_nested, and set_nested methods that enable
hierarchical variable storage and retrieval with dot-notation paths.
"""

import pytest

from core.variables.segments import IntegerSegment, ObjectSegment, StringSegment
from core.workflow.entities.nested_variable import NestedVariableDefinition, NestedVariableType
from core.workflow.runtime import VariablePool
from core.workflow.system_variable import SystemVariable


@pytest.fixture
def pool() -> VariablePool:
    """Create a fresh VariablePool for each test."""
    return VariablePool(
        system_variables=SystemVariable(
            user_id="test_user_id",
            app_id="test_app_id",
            workflow_id="test_workflow_id",
        ),
        user_inputs={},
    )


class TestAddNested:
    """Tests for the add_nested method."""

    def test_add_nested_simple_object(self, pool: VariablePool):
        """Test adding a simple nested object without validation."""
        value = {"name": "John", "age": 30}
        pool.add_nested(["node_1", "user"], value)

        result = pool.get(["node_1", "user"])
        assert result is not None
        assert isinstance(result, ObjectSegment)
        assert result.value["name"] == "John"
        assert result.value["age"] == 30

    def test_add_nested_deep_object(self, pool: VariablePool):
        """Test adding a deeply nested object."""
        value = {
            "user": {
                "profile": {
                    "name": "John",
                    "contact": {
                        "email": "john@example.com",
                    },
                },
            },
        }
        pool.add_nested(["node_1", "data"], value)

        result = pool.get(["node_1", "data"])
        assert result is not None
        assert result.value["user"]["profile"]["name"] == "John"
        assert result.value["user"]["profile"]["contact"]["email"] == "john@example.com"

    def test_add_nested_with_valid_definition(self, pool: VariablePool):
        """Test adding a nested object with validation against a definition."""
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
        value = {"name": "John", "age": 30}
        pool.add_nested(["node_1", "user"], value, definition)

        result = pool.get(["node_1", "user"])
        assert result is not None
        assert result.value["name"] == "John"

    def test_add_nested_with_missing_required_field(self, pool: VariablePool):
        """Test that validation fails when a required field is missing."""
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
        value = {"age": 30}  # Missing required 'name' field

        with pytest.raises(ValueError, match="Required field 'user.name' is missing"):
            pool.add_nested(["node_1", "user"], value, definition)

    def test_add_nested_with_type_mismatch(self, pool: VariablePool):
        """Test that validation fails when a field has wrong type."""
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
        value = {"age": "thirty"}  # Wrong type: string instead of integer

        with pytest.raises(ValueError, match="Type mismatch at 'user.age'"):
            pool.add_nested(["node_1", "user"], value, definition)

    def test_add_nested_boolean_not_integer(self, pool: VariablePool):
        """Test that boolean is not accepted as integer."""
        definition = NestedVariableDefinition(
            name="data",
            type=NestedVariableType.OBJECT,
            children=[
                NestedVariableDefinition(
                    name="count",
                    type=NestedVariableType.INTEGER,
                    required=True,
                ),
            ],
        )
        value = {"count": True}  # Boolean should not be accepted as integer

        with pytest.raises(ValueError, match="expected integer, got boolean"):
            pool.add_nested(["node_1", "data"], value, definition)


class TestGetNested:
    """Tests for the get_nested method."""

    def test_get_nested_without_path(self, pool: VariablePool):
        """Test getting a nested variable without a path returns the whole object."""
        value = {"name": "John", "age": 30}
        pool.add(["node_1", "user"], value)

        result = pool.get_nested(["node_1", "user"])
        assert result is not None
        assert isinstance(result, ObjectSegment)
        assert result.value == value

    def test_get_nested_with_simple_path(self, pool: VariablePool):
        """Test getting a nested value with a simple dot-notation path."""
        value = {"name": "John", "age": 30}
        pool.add(["node_1", "user"], value)

        result = pool.get_nested(["node_1", "user"], "name")
        assert result is not None
        assert isinstance(result, StringSegment)
        assert result.value == "John"

    def test_get_nested_with_deep_path(self, pool: VariablePool):
        """Test getting a deeply nested value."""
        value = {
            "user": {
                "profile": {
                    "email": "john@example.com",
                },
            },
        }
        pool.add(["node_1", "data"], value)

        result = pool.get_nested(["node_1", "data"], "user.profile.email")
        assert result is not None
        assert isinstance(result, StringSegment)
        assert result.value == "john@example.com"

    def test_get_nested_nonexistent_path(self, pool: VariablePool):
        """Test that getting a non-existent path returns None."""
        value = {"name": "John"}
        pool.add(["node_1", "user"], value)

        result = pool.get_nested(["node_1", "user"], "nonexistent.path")
        assert result is None

    def test_get_nested_nonexistent_variable(self, pool: VariablePool):
        """Test that getting a non-existent variable returns None."""
        result = pool.get_nested(["node_1", "nonexistent"])
        assert result is None

    def test_get_nested_preserves_type_info(self, pool: VariablePool):
        """Test that type information is preserved when getting nested values."""
        value = {
            "string_val": "hello",
            "int_val": 42,
            "nested": {"bool_val": True},
        }
        pool.add(["node_1", "data"], value)

        string_result = pool.get_nested(["node_1", "data"], "string_val")
        assert string_result is not None
        assert isinstance(string_result, StringSegment)

        int_result = pool.get_nested(["node_1", "data"], "int_val")
        assert int_result is not None
        assert isinstance(int_result, IntegerSegment)


class TestSetNested:
    """Tests for the set_nested method."""

    def test_set_nested_simple_value(self, pool: VariablePool):
        """Test setting a simple nested value."""
        value = {"name": "John", "age": 30}
        pool.add(["node_1", "user"], value)

        success = pool.set_nested(["node_1", "user"], "name", "Jane")
        assert success is True

        result = pool.get_nested(["node_1", "user"], "name")
        assert result is not None
        assert result.value == "Jane"

    def test_set_nested_deep_value(self, pool: VariablePool):
        """Test setting a deeply nested value."""
        value = {
            "user": {
                "profile": {
                    "email": "old@example.com",
                },
            },
        }
        pool.add(["node_1", "data"], value)

        success = pool.set_nested(["node_1", "data"], "user.profile.email", "new@example.com")
        assert success is True

        result = pool.get_nested(["node_1", "data"], "user.profile.email")
        assert result is not None
        assert result.value == "new@example.com"

    def test_set_nested_creates_intermediate_dicts(self, pool: VariablePool):
        """Test that set_nested creates intermediate dictionaries if needed."""
        value = {"existing": "value"}
        pool.add(["node_1", "data"], value)

        success = pool.set_nested(["node_1", "data"], "new.nested.path", "created")
        assert success is True

        result = pool.get_nested(["node_1", "data"], "new.nested.path")
        assert result is not None
        assert result.value == "created"

    def test_set_nested_maintains_immutability(self, pool: VariablePool):
        """Test that set_nested creates a new copy and doesn't modify the original."""
        original_value = {"name": "John", "nested": {"value": "original"}}
        pool.add(["node_1", "user"], original_value)

        # Get the original segment
        original_segment = pool.get(["node_1", "user"])
        assert original_segment is not None
        original_dict = dict(original_segment.value)

        # Modify via set_nested
        pool.set_nested(["node_1", "user"], "nested.value", "modified")

        # The original_dict should still have the original value
        # (since we made a copy before the modification)
        assert original_dict["nested"]["value"] == "original"

        # But the pool should have the new value
        result = pool.get_nested(["node_1", "user"], "nested.value")
        assert result is not None
        assert result.value == "modified"

    def test_set_nested_nonexistent_variable(self, pool: VariablePool):
        """Test that set_nested returns False for non-existent variable."""
        success = pool.set_nested(["node_1", "nonexistent"], "path", "value")
        assert success is False

    def test_set_nested_non_object_variable(self, pool: VariablePool):
        """Test that set_nested returns False for non-object variables."""
        pool.add(["node_1", "string_var"], "just a string")

        success = pool.set_nested(["node_1", "string_var"], "path", "value")
        assert success is False

    def test_set_nested_path_through_non_dict(self, pool: VariablePool):
        """Test that set_nested returns False when path goes through non-dict."""
        value = {"name": "John"}  # 'name' is a string, not a dict
        pool.add(["node_1", "user"], value)

        success = pool.set_nested(["node_1", "user"], "name.nested", "value")
        assert success is False


class TestNestedArrayValidation:
    """Tests for array[object] validation in nested variables."""

    def test_add_nested_array_object_valid(self, pool: VariablePool):
        """Test adding a valid array[object] with validation."""
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        value = [{"name": "John"}, {"name": "Jane"}]
        pool.add_nested(["node_1", "users"], value, definition)

        result = pool.get(["node_1", "users"])
        assert result is not None
        assert len(result.value) == 2

    def test_add_nested_array_object_missing_required(self, pool: VariablePool):
        """Test that validation fails when array element is missing required field."""
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        value = [{"name": "John"}, {"age": 30}]  # Second element missing 'name'

        with pytest.raises(ValueError, match=r"Required field 'users\[1\].name' is missing"):
            pool.add_nested(["node_1", "users"], value, definition)

    def test_add_nested_array_object_non_dict_element(self, pool: VariablePool):
        """Test that validation fails when array element is not a dict."""
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        value = [{"name": "John"}, "not a dict"]

        with pytest.raises(ValueError, match=r"Array element at 'users\[1\]' must be an object"):
            pool.add_nested(["node_1", "users"], value, definition)
