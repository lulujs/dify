"""
Unit tests for NestedVariableSerializer.

Tests cover:
- Serialization of nested variable definitions to JSON-compatible dictionaries
- Deserialization of dictionaries to nested variable definitions
- Round-trip serialization (serialize then deserialize)
- Backward compatibility with non-nested variable definitions
- Error handling for invalid data
"""

import json

import pytest

from core.workflow.entities.nested_variable import NestedVariableDefinition, NestedVariableType
from core.workflow.entities.node_input import EnhancedVariableSelector, NodeInputDefinition, NodeOutputDefinition
from core.workflow.serializers.nested_variable_serializer import (
    NestedVariableDeserializationError,
    NestedVariableSerializer,
)


class TestSerializeDefinition:
    """Tests for serialize_definition method."""

    def test_serialize_simple_string_definition(self):
        definition = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
            description="User's name",
        )
        result = NestedVariableSerializer.serialize_definition(definition)

        assert result["name"] == "username"
        assert result["type"] == "string"
        assert result["required"] is True
        assert result["description"] == "User's name"
        assert "children" not in result
        assert "default_value" not in result

    def test_serialize_definition_with_default_value(self):
        definition = NestedVariableDefinition(
            name="count",
            type=NestedVariableType.INTEGER,
            required=False,
            default_value=10,
        )
        result = NestedVariableSerializer.serialize_definition(definition)

        assert result["name"] == "count"
        assert result["type"] == "integer"
        assert result["required"] is False
        assert result["default_value"] == 10

    def test_serialize_nested_object_definition(self):
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
        result = NestedVariableSerializer.serialize_definition(definition)

        assert result["name"] == "user"
        assert result["type"] == "object"
        assert "children" in result
        assert len(result["children"]) == 2
        assert result["children"][0]["name"] == "name"
        assert result["children"][0]["type"] == "string"
        assert result["children"][1]["name"] == "age"
        assert result["children"][1]["type"] == "integer"

    def test_serialize_deeply_nested_definition(self):
        definition = NestedVariableDefinition(
            name="level1",
            type=NestedVariableType.OBJECT,
            children=[
                NestedVariableDefinition(
                    name="level2",
                    type=NestedVariableType.OBJECT,
                    children=[
                        NestedVariableDefinition(
                            name="level3",
                            type=NestedVariableType.STRING,
                        ),
                    ],
                ),
            ],
        )
        result = NestedVariableSerializer.serialize_definition(definition)

        assert result["children"][0]["children"][0]["name"] == "level3"
        assert result["children"][0]["children"][0]["type"] == "string"

    def test_serialize_array_object_definition(self):
        definition = NestedVariableDefinition(
            name="users",
            type=NestedVariableType.ARRAY_OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="id",
                    type=NestedVariableType.INTEGER,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="email",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        result = NestedVariableSerializer.serialize_definition(definition)

        assert result["type"] == "array[object]"
        assert len(result["children"]) == 2


class TestDeserializeDefinition:
    """Tests for deserialize_definition method."""

    def test_deserialize_simple_definition(self):
        data = {
            "name": "username",
            "type": "string",
            "required": True,
            "description": "User's name",
        }
        result = NestedVariableSerializer.deserialize_definition(data)

        assert result.name == "username"
        assert result.type == NestedVariableType.STRING
        assert result.required is True
        assert result.description == "User's name"
        assert result.children is None

    def test_deserialize_definition_with_default_value(self):
        data = {
            "name": "count",
            "type": "integer",
            "required": False,
            "default_value": 10,
        }
        result = NestedVariableSerializer.deserialize_definition(data)

        assert result.name == "count"
        assert result.type == NestedVariableType.INTEGER
        assert result.default_value == 10

    def test_deserialize_nested_definition(self):
        data = {
            "name": "user",
            "type": "object",
            "required": True,
            "children": [
                {"name": "name", "type": "string", "required": True},
                {"name": "age", "type": "integer", "required": False},
            ],
        }
        result = NestedVariableSerializer.deserialize_definition(data)

        assert result.name == "user"
        assert result.type == NestedVariableType.OBJECT
        assert result.children is not None
        assert len(result.children) == 2
        assert result.children[0].name == "name"
        assert result.children[1].name == "age"

    def test_deserialize_missing_name_raises_error(self):
        data = {"type": "string", "required": True}
        with pytest.raises(NestedVariableDeserializationError, match="Missing required field 'name'"):
            NestedVariableSerializer.deserialize_definition(data)

    def test_deserialize_missing_type_raises_error(self):
        data = {"name": "test", "required": True}
        with pytest.raises(NestedVariableDeserializationError, match="Missing required field 'type'"):
            NestedVariableSerializer.deserialize_definition(data)

    def test_deserialize_invalid_type_raises_error(self):
        data = {"name": "test", "type": "invalid_type", "required": True}
        with pytest.raises(NestedVariableDeserializationError, match="Invalid variable type"):
            NestedVariableSerializer.deserialize_definition(data)

    def test_deserialize_with_defaults(self):
        data = {"name": "test", "type": "string"}
        result = NestedVariableSerializer.deserialize_definition(data)

        assert result.required is False
        assert result.description == ""
        assert result.default_value is None


class TestRoundTrip:
    """Tests for serialization round-trip (serialize then deserialize)."""

    def test_round_trip_simple_definition(self):
        original = NestedVariableDefinition(
            name="username",
            type=NestedVariableType.STRING,
            required=True,
            description="User's name",
        )
        serialized = NestedVariableSerializer.serialize_definition(original)
        deserialized = NestedVariableSerializer.deserialize_definition(serialized)

        assert deserialized.name == original.name
        assert deserialized.type == original.type
        assert deserialized.required == original.required
        assert deserialized.description == original.description

    def test_round_trip_nested_definition(self):
        original = NestedVariableDefinition(
            name="user",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="profile",
                    type=NestedVariableType.OBJECT,
                    children=[
                        NestedVariableDefinition(
                            name="bio",
                            type=NestedVariableType.STRING,
                        ),
                    ],
                ),
            ],
        )
        serialized = NestedVariableSerializer.serialize_definition(original)
        deserialized = NestedVariableSerializer.deserialize_definition(serialized)

        assert deserialized.name == original.name
        assert deserialized.children is not None
        assert len(deserialized.children) == 1
        assert deserialized.children[0].name == "profile"
        assert deserialized.children[0].children is not None
        assert deserialized.children[0].children[0].name == "bio"

    def test_round_trip_json_encoding(self):
        """Test that serialized data can be JSON encoded and decoded."""
        original = NestedVariableDefinition(
            name="data",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="items",
                    type=NestedVariableType.ARRAY_STRING,
                    default_value=["a", "b"],
                ),
            ],
        )
        serialized = NestedVariableSerializer.serialize_definition(original)

        # Encode to JSON string and decode back
        json_str = json.dumps(serialized)
        decoded = json.loads(json_str)

        deserialized = NestedVariableSerializer.deserialize_definition(decoded)
        assert deserialized.name == original.name
        assert deserialized.children is not None
        assert deserialized.children[0].default_value == ["a", "b"]


class TestSerializeDefinitions:
    """Tests for serialize_definitions method."""

    def test_serialize_multiple_definitions(self):
        definitions = [
            NestedVariableDefinition(name="name", type=NestedVariableType.STRING),
            NestedVariableDefinition(name="age", type=NestedVariableType.INTEGER),
        ]
        result = NestedVariableSerializer.serialize_definitions(definitions)

        assert len(result) == 2
        assert result[0]["name"] == "name"
        assert result[1]["name"] == "age"

    def test_serialize_empty_list(self):
        result = NestedVariableSerializer.serialize_definitions([])
        assert result == []


class TestDeserializeDefinitions:
    """Tests for deserialize_definitions method."""

    def test_deserialize_multiple_definitions(self):
        data = [
            {"name": "name", "type": "string"},
            {"name": "age", "type": "integer"},
        ]
        result = NestedVariableSerializer.deserialize_definitions(data)

        assert len(result) == 2
        assert result[0].name == "name"
        assert result[1].name == "age"


class TestVariableSelector:
    """Tests for variable selector serialization."""

    def test_serialize_variable_selector(self):
        selector = EnhancedVariableSelector(
            variable="node1.output",
            value_selector=["node1", "output", "user", "name"],
        )
        result = NestedVariableSerializer.serialize_variable_selector(selector)

        assert result["variable"] == "node1.output"
        assert result["value_selector"] == ["node1", "output", "user", "name"]

    def test_deserialize_variable_selector(self):
        data = {
            "variable": "node1.output",
            "value_selector": ["node1", "output", "user", "name"],
        }
        result = NestedVariableSerializer.deserialize_variable_selector(data)

        assert result.variable == "node1.output"
        assert list(result.value_selector) == ["node1", "output", "user", "name"]

    def test_deserialize_variable_selector_missing_variable(self):
        data = {"value_selector": ["node1", "output"]}
        with pytest.raises(NestedVariableDeserializationError, match="Missing required field 'variable'"):
            NestedVariableSerializer.deserialize_variable_selector(data)


class TestNodeInputDefinition:
    """Tests for node input definition serialization."""

    def test_serialize_node_input(self):
        node_input = NodeInputDefinition(
            name="user_data",
            type=NestedVariableType.OBJECT,
            required=True,
            description="User input data",
            variable_selector=EnhancedVariableSelector(
                variable="start.input",
                value_selector=["start", "input"],
            ),
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )
        result = NestedVariableSerializer.serialize_node_input(node_input)

        assert result["name"] == "user_data"
        assert result["type"] == "object"
        assert result["required"] is True
        assert "variable_selector" in result
        assert "children" in result
        assert len(result["children"]) == 1

    def test_deserialize_node_input(self):
        data = {
            "name": "user_data",
            "type": "object",
            "required": True,
            "variable_selector": {
                "variable": "start.input",
                "value_selector": ["start", "input"],
            },
            "children": [
                {"name": "name", "type": "string", "required": True},
            ],
        }
        result = NestedVariableSerializer.deserialize_node_input(data)

        assert result.name == "user_data"
        assert result.type == NestedVariableType.OBJECT
        assert result.variable_selector is not None
        assert result.children is not None
        assert len(result.children) == 1


class TestNodeOutputDefinition:
    """Tests for node output definition serialization."""

    def test_serialize_node_output(self):
        node_output = NodeOutputDefinition(
            name="result",
            type=NestedVariableType.OBJECT,
            description="Processing result",
            children=[
                NestedVariableDefinition(
                    name="status",
                    type=NestedVariableType.STRING,
                ),
                NestedVariableDefinition(
                    name="data",
                    type=NestedVariableType.OBJECT,
                    children=[
                        NestedVariableDefinition(
                            name="id",
                            type=NestedVariableType.INTEGER,
                        ),
                    ],
                ),
            ],
        )
        result = NestedVariableSerializer.serialize_node_output(node_output)

        assert result["name"] == "result"
        assert result["type"] == "object"
        assert len(result["children"]) == 2

    def test_deserialize_node_output(self):
        data = {
            "name": "result",
            "type": "object",
            "description": "Processing result",
            "children": [
                {"name": "status", "type": "string"},
            ],
        }
        result = NestedVariableSerializer.deserialize_node_output(data)

        assert result.name == "result"
        assert result.type == NestedVariableType.OBJECT
        assert result.children is not None


class TestIsNestedVariableData:
    """Tests for is_nested_variable_data method."""

    def test_data_with_children_is_nested(self):
        data = {
            "name": "user",
            "type": "object",
            "children": [{"name": "name", "type": "string"}],
        }
        assert NestedVariableSerializer.is_nested_variable_data(data) is True

    def test_data_with_nested_type_is_nested(self):
        data = {"name": "user", "type": "object"}
        assert NestedVariableSerializer.is_nested_variable_data(data) is True

    def test_data_with_simple_type_not_nested(self):
        # Simple types without children are still considered nested variable data
        # if they use NestedVariableType enum values
        data = {"name": "name", "type": "string"}
        assert NestedVariableSerializer.is_nested_variable_data(data) is True

    def test_data_with_unknown_type_not_nested(self):
        data = {"name": "name", "type": "unknown_type"}
        assert NestedVariableSerializer.is_nested_variable_data(data) is False


class TestValidateSerializedDefinition:
    """Tests for validate_serialized_definition method."""

    def test_valid_definition_no_errors(self):
        data = {"name": "test", "type": "string", "required": True}
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert len(errors) == 0

    def test_missing_name_error(self):
        data = {"type": "string"}
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("name" in e for e in errors)

    def test_missing_type_error(self):
        data = {"name": "test"}
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("type" in e for e in errors)

    def test_invalid_type_error(self):
        data = {"name": "test", "type": "invalid"}
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("Invalid variable type" in e for e in errors)

    def test_children_on_non_nestable_type_error(self):
        data = {
            "name": "test",
            "type": "string",
            "children": [{"name": "child", "type": "string"}],
        }
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("Children not allowed" in e for e in errors)

    def test_duplicate_child_names_error(self):
        data = {
            "name": "test",
            "type": "object",
            "children": [
                {"name": "child", "type": "string"},
                {"name": "child", "type": "integer"},
            ],
        }
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("Duplicate" in e for e in errors)

    def test_nested_validation_errors(self):
        data = {
            "name": "test",
            "type": "object",
            "children": [
                {"type": "string"},  # Missing name
            ],
        }
        errors = NestedVariableSerializer.validate_serialized_definition(data)
        assert any("children[0]" in e for e in errors)


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing variable definitions."""

    def test_deserialize_minimal_definition(self):
        """Test that minimal definitions (just name and type) work."""
        data = {"name": "test", "type": "string"}
        result = NestedVariableSerializer.deserialize_definition(data)

        assert result.name == "test"
        assert result.type == NestedVariableType.STRING
        assert result.required is False
        assert result.description == ""
        assert result.default_value is None
        assert result.children is None

    def test_all_primitive_types_supported(self):
        """Test that all primitive types can be serialized and deserialized."""
        primitive_types = [
            NestedVariableType.STRING,
            NestedVariableType.INTEGER,
            NestedVariableType.NUMBER,
            NestedVariableType.BOOLEAN,
            NestedVariableType.FILE,
        ]
        for var_type in primitive_types:
            definition = NestedVariableDefinition(name="test", type=var_type)
            serialized = NestedVariableSerializer.serialize_definition(definition)
            deserialized = NestedVariableSerializer.deserialize_definition(serialized)
            assert deserialized.type == var_type

    def test_all_array_types_supported(self):
        """Test that all array types can be serialized and deserialized."""
        array_types = [
            NestedVariableType.ARRAY_STRING,
            NestedVariableType.ARRAY_INTEGER,
            NestedVariableType.ARRAY_NUMBER,
            NestedVariableType.ARRAY_BOOLEAN,
            NestedVariableType.ARRAY_FILE,
            NestedVariableType.ARRAY_OBJECT,
        ]
        for var_type in array_types:
            definition = NestedVariableDefinition(name="test", type=var_type)
            serialized = NestedVariableSerializer.serialize_definition(definition)
            deserialized = NestedVariableSerializer.deserialize_definition(serialized)
            assert deserialized.type == var_type


class TestPydanticNativeSerialization:
    """Tests for Pydantic native serialization methods."""

    def test_model_dump_produces_json_compatible_dict(self):
        """Test that model_dump() produces JSON-compatible output."""
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
        dumped = definition.model_dump()

        # Should be JSON serializable
        json_str = json.dumps(dumped)
        assert json_str is not None

        # Should be able to load back
        loaded = json.loads(json_str)
        assert loaded["name"] == "user"
        assert loaded["type"] == "object"

    def test_model_dump_json_produces_valid_json(self):
        """Test that model_dump_json() produces valid JSON string."""
        definition = NestedVariableDefinition(
            name="data",
            type=NestedVariableType.ARRAY_OBJECT,
            children=[
                NestedVariableDefinition(
                    name="id",
                    type=NestedVariableType.INTEGER,
                ),
            ],
        )
        json_str = definition.model_dump_json()

        # Should be valid JSON
        loaded = json.loads(json_str)
        assert loaded["name"] == "data"
        assert loaded["type"] == "array[object]"

    def test_model_validate_from_dict(self):
        """Test that model_validate() can reconstruct from dict."""
        data = {
            "name": "user",
            "type": "object",
            "required": True,
            "description": "User data",
            "children": [
                {
                    "name": "email",
                    "type": "string",
                    "required": True,
                },
            ],
        }
        definition = NestedVariableDefinition.model_validate(data)

        assert definition.name == "user"
        assert definition.type == NestedVariableType.OBJECT
        assert definition.children is not None
        assert len(definition.children) == 1
        assert definition.children[0].name == "email"

    def test_model_validate_json_from_string(self):
        """Test that model_validate_json() can reconstruct from JSON string."""
        json_str = '{"name": "count", "type": "integer", "required": false, "description": ""}'
        definition = NestedVariableDefinition.model_validate_json(json_str)

        assert definition.name == "count"
        assert definition.type == NestedVariableType.INTEGER
        assert definition.required is False

    def test_pydantic_round_trip(self):
        """Test complete round-trip using Pydantic methods."""
        original = NestedVariableDefinition(
            name="config",
            type=NestedVariableType.OBJECT,
            required=True,
            description="Configuration object",
            default_value={"key": "value"},
            children=[
                NestedVariableDefinition(
                    name="settings",
                    type=NestedVariableType.OBJECT,
                    children=[
                        NestedVariableDefinition(
                            name="enabled",
                            type=NestedVariableType.BOOLEAN,
                            default_value=True,
                        ),
                    ],
                ),
            ],
        )

        # Serialize to JSON string
        json_str = original.model_dump_json()

        # Deserialize back
        restored = NestedVariableDefinition.model_validate_json(json_str)

        # Verify equality
        assert restored.name == original.name
        assert restored.type == original.type
        assert restored.required == original.required
        assert restored.description == original.description
        assert restored.default_value == original.default_value
        assert restored.children is not None
        assert len(restored.children) == 1
        assert restored.children[0].name == "settings"
        assert restored.children[0].children is not None
        assert restored.children[0].children[0].name == "enabled"
        assert restored.children[0].children[0].default_value is True

    def test_node_input_pydantic_round_trip(self):
        """Test NodeInputDefinition round-trip using Pydantic methods."""
        original = NodeInputDefinition(
            name="input_data",
            type=NestedVariableType.OBJECT,
            required=True,
            variable_selector=EnhancedVariableSelector(
                variable="start.output",
                value_selector=["start", "output"],
            ),
            children=[
                NestedVariableDefinition(
                    name="field1",
                    type=NestedVariableType.STRING,
                ),
            ],
        )

        json_str = original.model_dump_json()
        restored = NodeInputDefinition.model_validate_json(json_str)

        assert restored.name == original.name
        assert restored.variable_selector is not None
        assert restored.variable_selector.variable == "start.output"
        assert restored.children is not None
        assert len(restored.children) == 1

    def test_node_output_pydantic_round_trip(self):
        """Test NodeOutputDefinition round-trip using Pydantic methods."""
        original = NodeOutputDefinition(
            name="output_data",
            type=NestedVariableType.OBJECT,
            description="Output from processing",
            children=[
                NestedVariableDefinition(
                    name="result",
                    type=NestedVariableType.STRING,
                ),
            ],
        )

        json_str = original.model_dump_json()
        restored = NodeOutputDefinition.model_validate_json(json_str)

        assert restored.name == original.name
        assert restored.description == original.description
        assert restored.children is not None
        assert len(restored.children) == 1
