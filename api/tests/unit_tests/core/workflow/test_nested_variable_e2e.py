"""
End-to-end tests for nested variable support.

This test suite covers the complete flow of nested variable definition and passing:
- Defining nested variables with complex structures
- Storing and retrieving nested variables in the variable pool
- Validating nested variable values at runtime
- Serializing and deserializing nested variable definitions
- API round-trip for nested variable configurations

These tests verify that all components work together correctly to support
complex object and array structures in workflow node inputs and outputs.

Requirements covered: 8.1, 8.2, 8.3, 8.4
"""

import json

import pytest

from core.variables.segments import IntegerSegment, ObjectSegment, StringSegment
from core.workflow.entities.nested_variable import (
    MAX_NESTING_DEPTH,
    NestedVariableDefinition,
    NestedVariableType,
)
from core.workflow.entities.node_input import (
    EnhancedVariableSelector,
    NodeInputDefinition,
    NodeOutputDefinition,
)
from core.workflow.runtime import VariablePool
from core.workflow.serializers.nested_variable_serializer import (
    NestedVariableSerializer,
)
from core.workflow.system_variable import SystemVariable
from core.workflow.validators.nested_variable_validator import (
    NestedVariableValidator,
)


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


class TestCompleteNestedVariableFlow:
    """
    End-to-end tests for the complete nested variable flow.

    Tests the full lifecycle: define -> validate -> store -> retrieve -> serialize
    """

    def test_complete_user_profile_flow(self, pool: VariablePool):
        """
        Test complete flow with a realistic user profile structure.

        This test simulates a workflow where:
        1. A Start node defines a nested user profile input
        2. The input is validated against the definition
        3. The value is stored in the variable pool
        4. Downstream nodes can access nested values
        5. The definition can be serialized and deserialized
        """
        # Step 1: Define the nested variable structure
        user_profile_definition = NestedVariableDefinition(
            name="user_profile",
            type=NestedVariableType.OBJECT,
            required=True,
            description="User profile with nested structure",
            children=[
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                    description="User's full name",
                ),
                NestedVariableDefinition(
                    name="age",
                    type=NestedVariableType.INTEGER,
                    required=False,
                    description="User's age",
                ),
                NestedVariableDefinition(
                    name="contact",
                    type=NestedVariableType.OBJECT,
                    required=True,
                    children=[
                        NestedVariableDefinition(
                            name="email",
                            type=NestedVariableType.STRING,
                            required=True,
                        ),
                        NestedVariableDefinition(
                            name="phone",
                            type=NestedVariableType.STRING,
                            required=False,
                        ),
                    ],
                ),
                NestedVariableDefinition(
                    name="tags",
                    type=NestedVariableType.ARRAY_STRING,
                    required=False,
                    default_value=[],
                ),
            ],
        )

        # Step 2: Validate the definition structure
        definition_errors = NestedVariableValidator.validate_definition(user_profile_definition)
        assert len(definition_errors) == 0, f"Definition validation failed: {definition_errors}"

        # Step 3: Create a valid input value
        user_input = {
            "name": "John Doe",
            "age": 30,
            "contact": {
                "email": "john@example.com",
                "phone": "+1234567890",
            },
            "tags": ["developer", "python"],
        }

        # Step 4: Validate the input value against the definition
        value_errors = NestedVariableValidator.validate_value(user_input, user_profile_definition)
        assert len(value_errors) == 0, f"Value validation failed: {value_errors}"

        # Step 5: Store in variable pool with validation
        pool.add_nested(["start_node", "user_profile"], user_input, user_profile_definition)

        # Step 6: Retrieve the complete object
        result = pool.get(["start_node", "user_profile"])
        assert result is not None
        assert isinstance(result, ObjectSegment)
        assert result.value["name"] == "John Doe"

        # Step 7: Access nested values using dot-notation
        email = pool.get_nested(["start_node", "user_profile"], "contact.email")
        assert email is not None
        assert isinstance(email, StringSegment)
        assert email.value == "john@example.com"

        name = pool.get_nested(["start_node", "user_profile"], "name")
        assert name is not None
        assert name.value == "John Doe"

        age = pool.get_nested(["start_node", "user_profile"], "age")
        assert age is not None
        assert isinstance(age, IntegerSegment)
        assert age.value == 30

        # Step 8: Serialize the definition
        serialized = NestedVariableSerializer.serialize_definition(user_profile_definition)
        assert serialized["name"] == "user_profile"
        assert serialized["type"] == "object"
        assert len(serialized["children"]) == 4

        # Step 9: Verify JSON encoding works
        json_str = json.dumps(serialized)
        assert json_str is not None

        # Step 10: Deserialize back
        deserialized = NestedVariableSerializer.deserialize_definition(json.loads(json_str))
        assert deserialized.name == user_profile_definition.name
        assert deserialized.type == user_profile_definition.type
        assert deserialized.children is not None
        assert user_profile_definition.children is not None
        assert len(deserialized.children) == len(user_profile_definition.children)

    def test_array_object_flow(self, pool: VariablePool):
        """
        Test complete flow with array[object] type.

        Simulates a workflow with a list of items, each having nested structure.
        """
        # Define array[object] structure
        items_definition = NestedVariableDefinition(
            name="items",
            type=NestedVariableType.ARRAY_OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="id",
                    type=NestedVariableType.INTEGER,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="name",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="price",
                    type=NestedVariableType.NUMBER,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="metadata",
                    type=NestedVariableType.OBJECT,
                    required=False,
                    children=[
                        NestedVariableDefinition(
                            name="category",
                            type=NestedVariableType.STRING,
                            required=False,
                        ),
                    ],
                ),
            ],
        )

        # Validate definition
        definition_errors = NestedVariableValidator.validate_definition(items_definition)
        assert len(definition_errors) == 0

        # Create valid input
        items_input = [
            {"id": 1, "name": "Item 1", "price": 10.99, "metadata": {"category": "electronics"}},
            {"id": 2, "name": "Item 2", "price": 20.50},
        ]

        # Validate input
        value_errors = NestedVariableValidator.validate_value(items_input, items_definition)
        assert len(value_errors) == 0

        # Store and retrieve
        pool.add_nested(["node_1", "items"], items_input, items_definition)
        result = pool.get(["node_1", "items"])
        assert result is not None
        assert len(result.value) == 2
        assert result.value[0]["name"] == "Item 1"

        # Serialize round-trip
        serialized = NestedVariableSerializer.serialize_definition(items_definition)
        json_str = json.dumps(serialized)
        deserialized = NestedVariableSerializer.deserialize_definition(json.loads(json_str))
        assert deserialized.type == NestedVariableType.ARRAY_OBJECT
        assert deserialized.children is not None
        assert len(deserialized.children) == 4

    def test_node_input_output_flow(self, pool: VariablePool):
        """
        Test complete flow with NodeInputDefinition and NodeOutputDefinition.

        Simulates passing nested variables between nodes.
        """
        # Define node output from upstream node
        upstream_output = NodeOutputDefinition(
            name="processed_data",
            type=NestedVariableType.OBJECT,
            description="Processed data from upstream node",
            children=[
                NestedVariableDefinition(
                    name="result",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="score",
                    type=NestedVariableType.NUMBER,
                    required=True,
                ),
            ],
        )

        # Store upstream output in pool
        upstream_value = {"result": "success", "score": 95.5}
        pool.add(["upstream_node", "processed_data"], upstream_value)

        # Define node input that references upstream output
        downstream_input = NodeInputDefinition(
            name="input_data",
            type=NestedVariableType.OBJECT,
            required=True,
            variable_selector=EnhancedVariableSelector(
                variable="upstream_node.processed_data",
                value_selector=["upstream_node", "processed_data"],
            ),
            children=[
                NestedVariableDefinition(
                    name="result",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
                NestedVariableDefinition(
                    name="score",
                    type=NestedVariableType.NUMBER,
                    required=True,
                ),
            ],
        )

        # Retrieve using variable selector path
        assert downstream_input.variable_selector is not None
        selector_path = downstream_input.variable_selector.value_selector
        retrieved = pool.get(list(selector_path))
        assert retrieved is not None
        assert retrieved.value["result"] == "success"
        assert retrieved.value["score"] == 95.5

        # Access nested value
        score = pool.get_nested(list(selector_path), "score")
        assert score is not None
        assert score.value == 95.5

        # Serialize node input/output
        serialized_output = NestedVariableSerializer.serialize_node_output(upstream_output)
        serialized_input = NestedVariableSerializer.serialize_node_input(downstream_input)

        # JSON round-trip
        output_json = json.dumps(serialized_output)
        input_json = json.dumps(serialized_input)

        restored_output = NestedVariableSerializer.deserialize_node_output(json.loads(output_json))
        restored_input = NestedVariableSerializer.deserialize_node_input(json.loads(input_json))

        assert restored_output.name == upstream_output.name
        assert restored_input.variable_selector is not None
        assert restored_input.variable_selector.variable == "upstream_node.processed_data"


class TestValidationErrorFlow:
    """Tests for validation error handling in the complete flow."""

    def test_missing_required_field_error(self, pool: VariablePool):
        """Test that missing required fields are properly caught."""
        definition = NestedVariableDefinition(
            name="data",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(
                    name="required_field",
                    type=NestedVariableType.STRING,
                    required=True,
                ),
            ],
        )

        # Missing required field
        invalid_input = {}

        # Validator should catch this
        errors = NestedVariableValidator.validate_value(invalid_input, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_REQUIRED_FIELD_MISSING

        # Variable pool should also catch this
        with pytest.raises(ValueError, match="Required field"):
            pool.add_nested(["node_1", "data"], invalid_input, definition)

    def test_type_mismatch_error(self, pool: VariablePool):
        """Test that type mismatches are properly caught."""
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

        # Wrong type
        invalid_input = {"count": "not_a_number"}

        errors = NestedVariableValidator.validate_value(invalid_input, definition)
        assert len(errors) == 1
        assert errors[0].error_code == NestedVariableValidator.ERROR_TYPE_MISMATCH

        with pytest.raises(ValueError, match="Type mismatch"):
            pool.add_nested(["node_1", "data"], invalid_input, definition)

    def test_nested_validation_error_path(self, pool: VariablePool):
        """Test that validation errors include correct nested paths."""
        definition = NestedVariableDefinition(
            name="root",
            type=NestedVariableType.OBJECT,
            children=[
                NestedVariableDefinition(
                    name="level1",
                    type=NestedVariableType.OBJECT,
                    children=[
                        NestedVariableDefinition(
                            name="level2",
                            type=NestedVariableType.STRING,
                            required=True,
                        ),
                    ],
                ),
            ],
        )

        # Missing deeply nested required field
        invalid_input = {"level1": {}}

        errors = NestedVariableValidator.validate_value(invalid_input, definition)
        assert len(errors) == 1
        assert "root.level1.level2" in errors[0].path


class TestDepthLimitFlow:
    """Tests for nesting depth limit enforcement."""

    def test_max_depth_validation(self):
        """Test that definitions exceeding max depth are rejected."""

        def create_nested(depth: int) -> NestedVariableDefinition:
            """Create a nested structure with the specified depth.

            depth=1 creates a single level (just a string)
            depth=2 creates object -> string (2 levels)
            etc.
            """
            if depth == 1:
                return NestedVariableDefinition(
                    name=f"level_{depth}",
                    type=NestedVariableType.STRING,
                )
            return NestedVariableDefinition(
                name=f"level_{depth}",
                type=NestedVariableType.OBJECT,
                children=[create_nested(depth - 1)],
            )

        # Create structure at max depth - should be valid
        # MAX_NESTING_DEPTH=5 means 5 levels are allowed
        valid_definition = create_nested(MAX_NESTING_DEPTH)
        errors = NestedVariableValidator.validate_definition(valid_definition)
        assert len(errors) == 0, f"Expected no errors for depth {MAX_NESTING_DEPTH}, got: {errors}"

        # Create structure exceeding max depth - should fail
        # depth=6 means 6 levels, which exceeds MAX_NESTING_DEPTH=5
        invalid_definition = create_nested(MAX_NESTING_DEPTH + 1)
        errors = NestedVariableValidator.validate_definition(invalid_definition)
        depth_errors = [e for e in errors if e.error_code == NestedVariableValidator.ERROR_MAX_DEPTH_EXCEEDED]
        assert len(depth_errors) > 0, f"Expected depth errors for depth {MAX_NESTING_DEPTH + 1}"


class TestImmutabilityFlow:
    """Tests for variable pool immutability with nested variables."""

    def test_set_nested_maintains_immutability(self, pool: VariablePool):
        """Test that set_nested creates new copies without modifying originals."""
        original_value = {
            "user": {
                "name": "Original",
                "profile": {"email": "original@example.com"},
            }
        }
        pool.add(["node_1", "data"], original_value)

        # Get original segment
        original_segment = pool.get(["node_1", "data"])
        assert original_segment is not None
        original_dict = dict(original_segment.value)

        # Modify via set_nested
        success = pool.set_nested(["node_1", "data"], "user.profile.email", "modified@example.com")
        assert success is True

        # Original dict should still have original value
        assert original_dict["user"]["profile"]["email"] == "original@example.com"

        # Pool should have new value
        modified = pool.get_nested(["node_1", "data"], "user.profile.email")
        assert modified is not None
        assert modified.value == "modified@example.com"


class TestBackwardCompatibilityFlow:
    """Tests for backward compatibility with non-nested variables."""

    def test_simple_variable_still_works(self, pool: VariablePool):
        """Test that simple (non-nested) variables still work correctly."""
        # Simple string variable
        pool.add(["node_1", "simple_string"], "hello")
        result = pool.get(["node_1", "simple_string"])
        assert result is not None
        assert result.value == "hello"

        # Simple integer variable
        pool.add(["node_1", "simple_int"], 42)
        result = pool.get(["node_1", "simple_int"])
        assert result is not None
        assert result.value == 42

    def test_flat_object_without_definition(self, pool: VariablePool):
        """Test that flat objects work without nested variable definitions."""
        flat_object = {"key1": "value1", "key2": 123}
        pool.add(["node_1", "flat_object"], flat_object)

        result = pool.get(["node_1", "flat_object"])
        assert result is not None
        assert result.value["key1"] == "value1"

        # Can still access nested values
        key1 = pool.get(["node_1", "flat_object", "key1"])
        assert key1 is not None
        assert key1.value == "value1"

    def test_minimal_definition_deserialization(self):
        """Test that minimal definitions (just name and type) deserialize correctly."""
        minimal_data = {"name": "test", "type": "string"}
        definition = NestedVariableSerializer.deserialize_definition(minimal_data)

        assert definition.name == "test"
        assert definition.type == NestedVariableType.STRING
        assert definition.required is False
        assert definition.description == ""
        assert definition.default_value is None
        assert definition.children is None


class TestAPIRoundTripFlow:
    """
    Tests for API round-trip scenarios.

    Simulates the complete flow of:
    1. Receiving nested variable configuration from API
    2. Processing and validating
    3. Returning nested variable results
    """

    def test_workflow_configuration_round_trip(self):
        """
        Test complete workflow configuration round-trip.

        Simulates receiving a workflow configuration with nested variables
        from the API, processing it, and returning results.
        """
        # Simulate API request payload with nested variable configuration
        api_request = {
            "nodes": [
                {
                    "id": "start_node",
                    "type": "start",
                    "data": {
                        "variables": [
                            {
                                "name": "user_data",
                                "type": "object",
                                "required": True,
                                "children": [
                                    {"name": "name", "type": "string", "required": True},
                                    {
                                        "name": "preferences",
                                        "type": "object",
                                        "children": [
                                            {"name": "theme", "type": "string", "default_value": "light"},
                                            {"name": "notifications", "type": "boolean", "default_value": True},
                                        ],
                                    },
                                ],
                            }
                        ]
                    },
                }
            ]
        }

        # Deserialize the configuration
        node_data = api_request["nodes"][0]["data"]
        variables_data = node_data["variables"]

        definitions = NestedVariableSerializer.deserialize_definitions(variables_data)
        assert len(definitions) == 1
        assert definitions[0].name == "user_data"
        assert definitions[0].children is not None
        assert len(definitions[0].children) == 2

        # Validate the definitions
        for definition in definitions:
            errors = NestedVariableValidator.validate_definition(definition)
            assert len(errors) == 0

        # Simulate workflow execution with input
        workflow_input = {
            "user_data": {
                "name": "Test User",
                "preferences": {
                    "theme": "dark",
                    "notifications": False,
                },
            }
        }

        # Validate input against definitions
        for definition in definitions:
            value = workflow_input.get(definition.name)
            errors = NestedVariableValidator.validate_value(value, definition)
            assert len(errors) == 0

        # Serialize for API response
        serialized_definitions = NestedVariableSerializer.serialize_definitions(definitions)

        # Verify JSON encoding works
        response_json = json.dumps(
            {
                "nodes": [
                    {
                        "id": "start_node",
                        "type": "start",
                        "data": {"variables": serialized_definitions},
                    }
                ],
                "outputs": workflow_input,
            }
        )

        # Parse response and verify
        response = json.loads(response_json)
        assert response["outputs"]["user_data"]["name"] == "Test User"
        assert response["outputs"]["user_data"]["preferences"]["theme"] == "dark"

    def test_workflow_run_with_nested_input_output(self, pool: VariablePool):
        """
        Test workflow run with nested input and output.

        Simulates:
        1. Receiving nested input from API
        2. Processing through variable pool
        3. Returning nested output
        """
        # API input
        api_input = {
            "request": {
                "method": "POST",
                "headers": {"Content-Type": "application/json", "Authorization": "Bearer token"},
                "body": {"action": "process", "data": {"items": [1, 2, 3]}},
            }
        }

        # Define input structure
        input_definition = NestedVariableDefinition(
            name="request",
            type=NestedVariableType.OBJECT,
            required=True,
            children=[
                NestedVariableDefinition(name="method", type=NestedVariableType.STRING, required=True),
                NestedVariableDefinition(name="headers", type=NestedVariableType.OBJECT, required=False),
                NestedVariableDefinition(name="body", type=NestedVariableType.OBJECT, required=True),
            ],
        )

        # Validate and store input
        errors = NestedVariableValidator.validate_value(api_input["request"], input_definition)
        assert len(errors) == 0

        pool.add_nested(["start", "request"], api_input["request"], input_definition)

        # Access nested values during processing
        method = pool.get_nested(["start", "request"], "method")
        assert method is not None
        assert method.value == "POST"

        body_action = pool.get_nested(["start", "request"], "body.action")
        assert body_action is not None
        assert body_action.value == "process"

        # Create output
        output_value = {
            "status": "success",
            "result": {
                "processed_items": 3,
                "summary": {"total": 6, "average": 2.0},
            },
        }

        pool.add(["end", "response"], output_value)

        # Retrieve output for API response
        response = pool.get(["end", "response"])
        assert response is not None
        assert response.value["status"] == "success"
        assert response.value["result"]["processed_items"] == 3

        # Serialize for API response
        api_response = json.dumps({"output": response.value})
        parsed_response = json.loads(api_response)
        assert parsed_response["output"]["result"]["summary"]["total"] == 6


class TestDSLExportImportFlow:
    """
    Tests for DSL export/import with nested variables.

    Simulates the complete flow of:
    1. Creating a workflow with nested variable definitions
    2. Exporting the workflow to DSL (YAML)
    3. Importing the DSL back
    4. Verifying nested variable definitions are preserved
    """

    def test_dsl_round_trip_with_nested_variables(self):
        """
        Test that nested variable definitions survive DSL export/import round-trip.

        This test verifies that:
        1. Nested variable definitions in Start node are properly serialized to YAML
        2. The YAML can be parsed back
        3. The nested structure is preserved after round-trip
        """
        import yaml

        # Create a workflow graph with nested variable definitions in Start node
        workflow_graph = {
            "nodes": [
                {
                    "id": "start_node",
                    "type": "start",
                    "data": {
                        "type": "start",
                        "title": "Start",
                        "variables": [
                            {
                                "variable": "simple_text",
                                "label": "Simple Text",
                                "type": "text-input",
                                "required": True,
                            },
                            {
                                "variable": "user_profile",
                                "label": "User Profile",
                                "type": "object",
                                "required": True,
                                "children": [
                                    {
                                        "name": "name",
                                        "type": "string",
                                        "required": True,
                                        "description": "User's full name",
                                    },
                                    {
                                        "name": "age",
                                        "type": "integer",
                                        "required": False,
                                    },
                                    {
                                        "name": "contact",
                                        "type": "object",
                                        "required": True,
                                        "children": [
                                            {
                                                "name": "email",
                                                "type": "string",
                                                "required": True,
                                            },
                                            {
                                                "name": "phone",
                                                "type": "string",
                                                "required": False,
                                            },
                                        ],
                                    },
                                ],
                            },
                            {
                                "variable": "items",
                                "label": "Items List",
                                "type": "array[object]",
                                "required": False,
                                "children": [
                                    {
                                        "name": "id",
                                        "type": "integer",
                                        "required": True,
                                    },
                                    {
                                        "name": "name",
                                        "type": "string",
                                        "required": True,
                                    },
                                    {
                                        "name": "price",
                                        "type": "number",
                                        "required": False,
                                    },
                                ],
                            },
                        ],
                    },
                },
                {
                    "id": "end_node",
                    "type": "end",
                    "data": {
                        "type": "end",
                        "title": "End",
                        "outputs": [],
                    },
                },
            ],
            "edges": [
                {
                    "id": "edge_1",
                    "source": "start_node",
                    "target": "end_node",
                }
            ],
        }

        # Simulate DSL export structure
        dsl_export = {
            "version": "0.5.0",
            "kind": "app",
            "app": {
                "name": "Test Workflow App",
                "mode": "workflow",
                "icon": "🤖",
                "icon_background": "#FFEAD5",
                "description": "Test app with nested variables",
            },
            "workflow": {
                "graph": workflow_graph,
                "features": {},
                "environment_variables": [],
                "conversation_variables": [],
            },
        }

        # Export to YAML
        yaml_content = yaml.dump(dsl_export, allow_unicode=True)
        assert yaml_content is not None
        assert len(yaml_content) > 0

        # Import from YAML
        imported_data = yaml.safe_load(yaml_content)

        # Verify structure is preserved
        assert imported_data["version"] == "0.5.0"
        assert imported_data["app"]["mode"] == "workflow"
        assert "workflow" in imported_data
        assert "graph" in imported_data["workflow"]

        # Verify nodes are preserved
        nodes = imported_data["workflow"]["graph"]["nodes"]
        assert len(nodes) == 2

        # Find start node
        start_node = next((n for n in nodes if n["id"] == "start_node"), None)
        assert start_node is not None

        # Verify variables are preserved
        variables = start_node["data"]["variables"]
        assert len(variables) == 3

        # Verify simple variable
        simple_var = next((v for v in variables if v["variable"] == "simple_text"), None)
        assert simple_var is not None
        assert simple_var["type"] == "text-input"

        # Verify nested object variable
        user_profile_var = next((v for v in variables if v["variable"] == "user_profile"), None)
        assert user_profile_var is not None
        assert user_profile_var["type"] == "object"
        assert "children" in user_profile_var
        assert len(user_profile_var["children"]) == 3

        # Verify deeply nested structure
        contact_child = next((c for c in user_profile_var["children"] if c["name"] == "contact"), None)
        assert contact_child is not None
        assert contact_child["type"] == "object"
        assert "children" in contact_child
        assert len(contact_child["children"]) == 2

        email_child = next((c for c in contact_child["children"] if c["name"] == "email"), None)
        assert email_child is not None
        assert email_child["type"] == "string"
        assert email_child["required"] is True

        # Verify array[object] variable
        items_var = next((v for v in variables if v["variable"] == "items"), None)
        assert items_var is not None
        assert items_var["type"] == "array[object]"
        assert "children" in items_var
        assert len(items_var["children"]) == 3

    def test_dsl_import_with_nested_variable_validation(self):
        """
        Test that imported nested variables can be validated.

        This test verifies that after DSL import, the nested variable
        definitions can be properly validated using NestedVariableValidator.
        """
        import yaml

        # DSL content with nested variables
        dsl_content = """
version: "0.5.0"
kind: app
app:
  name: Test App
  mode: workflow
workflow:
  graph:
    nodes:
      - id: start
        type: start
        data:
          type: start
          variables:
            - variable: config
              label: Configuration
              type: object
              required: true
              children:
                - name: database
                  type: object
                  required: true
                  children:
                    - name: host
                      type: string
                      required: true
                    - name: port
                      type: integer
                      required: true
                      default_value: 5432
                - name: cache
                  type: object
                  required: false
                  children:
                    - name: enabled
                      type: boolean
                      default_value: true
                    - name: ttl
                      type: integer
                      default_value: 3600
    edges: []
  features: {}
"""

        # Parse YAML
        imported_data = yaml.safe_load(dsl_content)

        # Extract nested variable definition
        start_node = imported_data["workflow"]["graph"]["nodes"][0]
        config_var = start_node["data"]["variables"][0]

        # Convert to NestedVariableDefinition for validation
        # Note: The DSL uses 'variable' as the name field for top-level variables
        nested_def_data = {
            "name": config_var["variable"],
            "type": config_var["type"],
            "required": config_var.get("required", False),
            "children": config_var.get("children", []),
        }

        definition = NestedVariableSerializer.deserialize_definition(nested_def_data)

        # Validate the definition
        errors = NestedVariableValidator.validate_definition(definition)
        assert len(errors) == 0, f"Validation errors: {errors}"

        # Verify structure
        assert definition.name == "config"
        assert definition.type == NestedVariableType.OBJECT
        assert definition.children is not None
        assert len(definition.children) == 2

        # Verify nested children
        db_child = next((c for c in definition.children if c.name == "database"), None)
        assert db_child is not None
        assert db_child.children is not None
        assert len(db_child.children) == 2

        # Validate a sample input value
        valid_input = {
            "database": {
                "host": "localhost",
                "port": 5432,
            },
            "cache": {
                "enabled": True,
                "ttl": 7200,
            },
        }

        value_errors = NestedVariableValidator.validate_value(valid_input, definition)
        assert len(value_errors) == 0

        # Test invalid input
        invalid_input = {
            "database": {
                "host": "localhost",
                # missing required 'port'
            },
        }

        value_errors = NestedVariableValidator.validate_value(invalid_input, definition)
        assert len(value_errors) > 0

    def test_dsl_export_preserves_all_nested_properties(self):
        """
        Test that DSL export preserves all nested variable properties.

        Verifies that description, default_value, required, and other
        properties are preserved through the export/import cycle.
        """
        import yaml

        # Create definition with all properties
        definition = NestedVariableDefinition(
            name="settings",
            type=NestedVariableType.OBJECT,
            required=True,
            description="Application settings",
            children=[
                NestedVariableDefinition(
                    name="theme",
                    type=NestedVariableType.STRING,
                    required=False,
                    description="UI theme",
                    default_value="light",
                ),
                NestedVariableDefinition(
                    name="notifications",
                    type=NestedVariableType.OBJECT,
                    required=False,
                    description="Notification settings",
                    children=[
                        NestedVariableDefinition(
                            name="email",
                            type=NestedVariableType.BOOLEAN,
                            required=False,
                            default_value=True,
                            description="Enable email notifications",
                        ),
                        NestedVariableDefinition(
                            name="frequency",
                            type=NestedVariableType.STRING,
                            required=False,
                            default_value="daily",
                            description="Notification frequency",
                        ),
                    ],
                ),
            ],
        )

        # Serialize to dict (as would be stored in workflow graph)
        serialized = NestedVariableSerializer.serialize_definition(definition)

        # Create DSL structure
        dsl_data = {
            "version": "0.5.0",
            "kind": "app",
            "app": {"name": "Test", "mode": "workflow"},
            "workflow": {
                "graph": {
                    "nodes": [
                        {
                            "id": "start",
                            "data": {
                                "type": "start",
                                "variables": [
                                    {
                                        "variable": serialized["name"],
                                        "type": serialized["type"],
                                        "required": serialized["required"],
                                        "description": serialized["description"],
                                        "children": serialized["children"],
                                    }
                                ],
                            },
                        }
                    ],
                    "edges": [],
                },
                "features": {},
            },
        }

        # Export to YAML and import back
        yaml_str = yaml.dump(dsl_data, allow_unicode=True)
        imported = yaml.safe_load(yaml_str)

        # Extract and verify
        var_data = imported["workflow"]["graph"]["nodes"][0]["data"]["variables"][0]

        assert var_data["variable"] == "settings"
        assert var_data["type"] == "object"
        assert var_data["required"] is True
        assert var_data["description"] == "Application settings"

        # Verify children
        children = var_data["children"]
        assert len(children) == 2

        theme_child = next((c for c in children if c["name"] == "theme"), None)
        assert theme_child is not None
        assert theme_child["default_value"] == "light"
        assert theme_child["description"] == "UI theme"

        notifications_child = next((c for c in children if c["name"] == "notifications"), None)
        assert notifications_child is not None
        assert notifications_child["description"] == "Notification settings"
        assert len(notifications_child["children"]) == 2

        email_child = next((c for c in notifications_child["children"] if c["name"] == "email"), None)
        assert email_child is not None
        assert email_child["default_value"] is True
        assert email_child["description"] == "Enable email notifications"

    def test_dsl_backward_compatibility_with_flat_variables(self):
        """
        Test that DSL import works with both flat and nested variables.

        Verifies backward compatibility: workflows with only flat variables
        should continue to work, and mixed workflows should handle both.
        """
        import yaml

        # DSL with mixed flat and nested variables
        dsl_content = """
version: "0.5.0"
kind: app
app:
  name: Mixed Variables App
  mode: workflow
workflow:
  graph:
    nodes:
      - id: start
        type: start
        data:
          type: start
          variables:
            - variable: name
              label: Name
              type: text-input
              required: true
            - variable: age
              label: Age
              type: number
              required: false
            - variable: profile
              label: Profile
              type: object
              required: false
              children:
                - name: bio
                  type: string
                  required: false
                - name: website
                  type: string
                  required: false
    edges: []
  features: {}
"""

        imported = yaml.safe_load(dsl_content)
        variables = imported["workflow"]["graph"]["nodes"][0]["data"]["variables"]

        # Verify flat variables
        name_var = next((v for v in variables if v["variable"] == "name"), None)
        assert name_var is not None
        assert name_var["type"] == "text-input"
        assert "children" not in name_var or name_var.get("children") is None

        age_var = next((v for v in variables if v["variable"] == "age"), None)
        assert age_var is not None
        assert age_var["type"] == "number"

        # Verify nested variable
        profile_var = next((v for v in variables if v["variable"] == "profile"), None)
        assert profile_var is not None
        assert profile_var["type"] == "object"
        assert "children" in profile_var
        assert len(profile_var["children"]) == 2


class TestVariableEntityChildrenPreservation:
    """
    Tests for VariableEntity children field preservation.

    These tests verify that the children field is properly preserved when
    VariableEntity is validated through Pydantic, which is critical for
    the save/publish workflow to work correctly.
    """

    def test_variable_entity_preserves_children_on_validation(self):
        """
        Test that VariableEntity preserves children field when validated.

        This is the core fix for the issue where nested variables were lost
        on save/publish because VariableEntity didn't have a children field.
        """
        from core.app.app_config.entities import VariableEntity

        # Create variable data with children (as would come from frontend)
        variable_data = {
            "variable": "user_profile",
            "label": "User Profile",
            "type": "object",
            "required": True,
            "children": [
                {
                    "variable": "name",
                    "label": "Name",
                    "type": "text-input",
                    "required": True,
                },
                {
                    "variable": "contact",
                    "label": "Contact",
                    "type": "object",
                    "required": False,
                    "children": [
                        {
                            "variable": "email",
                            "label": "Email",
                            "type": "text-input",
                            "required": True,
                        },
                    ],
                },
            ],
        }

        # Validate through Pydantic
        entity = VariableEntity.model_validate(variable_data)

        # Verify children are preserved
        assert entity.children is not None
        assert len(entity.children) == 2

        # Verify nested children
        contact_child = next((c for c in entity.children if c.variable == "contact"), None)
        assert contact_child is not None
        assert contact_child.children is not None
        assert len(contact_child.children) == 1
        assert contact_child.children[0].variable == "email"

    def test_start_node_data_preserves_nested_variables(self):
        """
        Test that StartNodeData preserves nested variable children.

        This test verifies the complete flow from node data to StartNodeData
        validation, ensuring children are not stripped.
        """
        from core.workflow.nodes.start.entities import StartNodeData

        # Create start node data with nested variables (as stored in workflow graph)
        node_data = {
            "type": "start",
            "title": "Start",
            "variables": [
                {
                    "variable": "simple_input",
                    "label": "Simple Input",
                    "type": "text-input",
                    "required": True,
                },
                {
                    "variable": "nested_object",
                    "label": "Nested Object",
                    "type": "object",
                    "required": True,
                    "children": [
                        {
                            "variable": "field1",
                            "label": "Field 1",
                            "type": "text-input",
                            "required": True,
                        },
                        {
                            "variable": "field2",
                            "label": "Field 2",
                            "type": "number",
                            "required": False,
                        },
                    ],
                },
            ],
        }

        # Validate through StartNodeData
        start_data = StartNodeData.model_validate(node_data)

        # Verify variables are preserved
        assert len(start_data.variables) == 2

        # Verify simple variable
        simple_var = next((v for v in start_data.variables if v.variable == "simple_input"), None)
        assert simple_var is not None
        assert simple_var.children is None

        # Verify nested variable with children
        nested_var = next((v for v in start_data.variables if v.variable == "nested_object"), None)
        assert nested_var is not None
        assert nested_var.children is not None
        assert len(nested_var.children) == 2

    def test_variable_entity_type_supports_nestable_types(self):
        """
        Test that VariableEntityType includes nestable types (object, array[object]).
        """
        from core.app.app_config.entities import VariableEntityType

        # Verify new types exist
        assert VariableEntityType.OBJECT == "object"
        assert VariableEntityType.ARRAY_OBJECT == "array[object]"

        # Verify is_nestable method
        assert VariableEntityType.OBJECT.is_nestable() is True
        assert VariableEntityType.ARRAY_OBJECT.is_nestable() is True
        assert VariableEntityType.TEXT_INPUT.is_nestable() is False
        assert VariableEntityType.NUMBER.is_nestable() is False

    def test_variable_entity_serialization_round_trip(self):
        """
        Test that VariableEntity with children survives serialization round-trip.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType

        # Create entity with nested children
        entity = VariableEntity(
            variable="config",
            label="Configuration",
            type=VariableEntityType.OBJECT,
            required=True,
            children=[
                VariableEntity(
                    variable="setting1",
                    label="Setting 1",
                    type=VariableEntityType.TEXT_INPUT,
                    required=True,
                ),
                VariableEntity(
                    variable="nested",
                    label="Nested",
                    type=VariableEntityType.OBJECT,
                    required=False,
                    children=[
                        VariableEntity(
                            variable="deep_setting",
                            label="Deep Setting",
                            type=VariableEntityType.NUMBER,
                            required=False,
                        ),
                    ],
                ),
            ],
        )

        # Serialize to dict
        serialized = entity.model_dump()

        # Verify children are in serialized output
        assert "children" in serialized
        assert len(serialized["children"]) == 2

        # Deserialize back
        restored = VariableEntity.model_validate(serialized)

        # Verify structure is preserved
        assert restored.variable == "config"
        assert restored.children is not None
        assert len(restored.children) == 2

        nested_child = next((c for c in restored.children if c.variable == "nested"), None)
        assert nested_child is not None
        assert nested_child.children is not None
        assert len(nested_child.children) == 1
        assert nested_child.children[0].variable == "deep_setting"

    def test_workflow_graph_preserves_nested_variables_through_json(self):
        """
        Test that nested variables in workflow graph survive JSON serialization.

        This simulates the actual save flow where the graph is stored as JSON.
        """
        import json

        # Create workflow graph with nested variables
        workflow_graph = {
            "nodes": [
                {
                    "id": "start_node",
                    "data": {
                        "type": "start",
                        "variables": [
                            {
                                "variable": "user_data",
                                "label": "User Data",
                                "type": "object",
                                "required": True,
                                "children": [
                                    {
                                        "variable": "name",
                                        "label": "Name",
                                        "type": "text-input",
                                        "required": True,
                                    },
                                    {
                                        "variable": "preferences",
                                        "label": "Preferences",
                                        "type": "object",
                                        "children": [
                                            {
                                                "variable": "theme",
                                                "label": "Theme",
                                                "type": "text-input",
                                                "default": "light",
                                            },
                                        ],
                                    },
                                ],
                            },
                        ],
                    },
                },
            ],
            "edges": [],
        }

        # Serialize to JSON (as done in workflow save)
        json_str = json.dumps(workflow_graph)

        # Deserialize (as done when loading workflow)
        restored_graph = json.loads(json_str)

        # Verify nested structure is preserved
        start_node = restored_graph["nodes"][0]
        variables = start_node["data"]["variables"]
        assert len(variables) == 1

        user_data_var = variables[0]
        assert user_data_var["variable"] == "user_data"
        assert "children" in user_data_var
        assert len(user_data_var["children"]) == 2

        preferences_child = next(
            (c for c in user_data_var["children"] if c["variable"] == "preferences"),
            None,
        )
        assert preferences_child is not None
        assert "children" in preferences_child
        assert len(preferences_child["children"]) == 1
        assert preferences_child["children"][0]["variable"] == "theme"


class TestFrontendTypeMapping:
    """Tests for frontend type to NestedVariableType mapping in validation."""

    def test_convert_frontend_types_to_nested_definition_format(self):
        """
        Test that frontend variable types are correctly mapped to NestedVariableType values.

        Frontend uses different type names (json_object, text-input, etc.) that need
        to be converted to NestedVariableType values (object, string, etc.) for validation.
        """
        from controllers.console.app.nested_variable_utils import _convert_to_nested_definition_format

        # Test json_object -> object mapping
        frontend_var = {
            "variable": "user_data",
            "label": "User Data",
            "type": "json_object",
            "required": True,
            "children": [
                {
                    "variable": "name",
                    "label": "Name",
                    "type": "text-input",
                    "required": True,
                },
                {
                    "variable": "age",
                    "label": "Age",
                    "type": "number",
                    "required": False,
                },
            ],
        }

        converted = _convert_to_nested_definition_format(frontend_var)

        # Verify type mappings
        assert converted["name"] == "user_data"
        assert converted["type"] == "object"  # json_object -> object
        assert converted["required"] is True

        # Verify children type mappings
        assert len(converted["children"]) == 2
        assert converted["children"][0]["name"] == "name"
        assert converted["children"][0]["type"] == "string"  # text-input -> string
        assert converted["children"][1]["name"] == "age"
        assert converted["children"][1]["type"] == "number"  # number stays number

    def test_validate_graph_with_frontend_types(self):
        """
        Test that validate_graph_nested_variables correctly handles frontend types.

        This simulates the actual API request where frontend sends json_object
        and text-input types that need to be validated.
        """
        from controllers.console.app.nested_variable_utils import validate_graph_nested_variables

        # Simulate a workflow graph from frontend with json_object type
        graph = {
            "nodes": [
                {
                    "id": "1766852370227",
                    "type": "start",
                    "data": {
                        "type": "start",
                        "variables": [
                            {
                                "variable": "a",
                                "label": "a",
                                "type": "json_object",
                                "required": True,
                                "description": "",
                                "children": [
                                    {
                                        "variable": "var_1766974",
                                        "label": "var_1766974",
                                        "type": "text-input",
                                        "required": False,
                                        "description": "",
                                        "children": [],
                                    }
                                ],
                            }
                        ],
                    },
                }
            ],
            "edges": [],
        }

        # Should not raise any errors - types should be correctly mapped
        errors = validate_graph_nested_variables(graph)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"

    def test_all_frontend_type_mappings(self):
        """Test all supported frontend type mappings."""
        from controllers.console.app.nested_variable_utils import _convert_to_nested_definition_format

        type_mappings = [
            ("json_object", "object"),
            ("text-input", "string"),
            ("paragraph", "string"),
            ("select", "string"),
            ("number", "number"),
            ("checkbox", "boolean"),
            ("file", "file"),
            ("file-list", "array[file]"),
            # Types that should pass through unchanged
            ("string", "string"),
            ("integer", "integer"),
            ("object", "object"),
            ("array[object]", "array[object]"),
        ]

        for frontend_type, expected_type in type_mappings:
            var = {"variable": "test", "type": frontend_type}
            converted = _convert_to_nested_definition_format(var)
            assert converted["type"] == expected_type, (
                f"Expected {frontend_type} -> {expected_type}, got {converted['type']}"
            )


class TestDSLImportWithNestedVariables:
    """Tests for importing DSL with nested variables - reproducing real-world issues."""

    def test_import_dsl_with_json_object_nested_variable(self):
        """
        Test importing a DSL with json_object type nested variable.

        This reproduces the exact structure from the user's DSL that was causing 500 errors.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType

        # This is the exact structure from the user's DSL
        dsl_variable = {
            "children": [
                {
                    "children": [],
                    "description": "",
                    "required": False,
                    "type": "text-input",
                    "variable": "var_1766974683066",
                }
            ],
            "default": "",
            "hint": "",
            "label": "a",
            "max_length": 48,
            "options": [],
            "placeholder": "",
            "required": True,
            "type": "json_object",
            "variable": "a",
        }

        # This should not raise an error - VariableEntity should handle this
        variable = VariableEntity.model_validate(dsl_variable)

        assert variable.variable == "a"
        assert variable.type == VariableEntityType.JSON_OBJECT
        assert variable.children is not None
        assert len(variable.children) == 1
        assert variable.children[0].variable == "var_1766974683066"
        assert variable.children[0].type == VariableEntityType.TEXT_INPUT

    def test_import_dsl_child_without_label(self):
        """
        Test that child variables without label field are handled correctly.

        The DSL children don't have 'label' field, only 'variable'.
        """
        from core.app.app_config.entities import VariableEntity

        # Child variable from DSL - no label field
        child_var = {
            "children": [],
            "description": "",
            "required": False,
            "type": "text-input",
            "variable": "var_1766974683066",
        }

        # Should work with default empty label
        child = VariableEntity.model_validate(child_var)
        assert child.variable == "var_1766974683066"
        assert child.label == ""  # Default empty string

    def test_start_node_data_with_dsl_nested_variables(self):
        """
        Test that StartNodeData correctly validates DSL with nested variables.
        """
        from core.workflow.nodes.start.entities import StartNodeData

        # Exact structure from the DSL's start node data
        start_node_data = {
            "title": "用户输入",
            "type": "start",
            "variables": [
                {
                    "children": [
                        {
                            "children": [],
                            "description": "",
                            "required": False,
                            "type": "text-input",
                            "variable": "var_1766974683066",
                        }
                    ],
                    "default": "",
                    "hint": "",
                    "label": "a",
                    "max_length": 48,
                    "options": [],
                    "placeholder": "",
                    "required": True,
                    "type": "json_object",
                    "variable": "a",
                }
            ],
        }

        # This should not raise an error
        node_data = StartNodeData.model_validate(start_node_data)

        assert len(node_data.variables) == 1
        assert node_data.variables[0].variable == "a"
        assert node_data.variables[0].children is not None
        assert len(node_data.variables[0].children) == 1

    def test_validate_graph_with_dsl_structure(self):
        """
        Test validate_graph_nested_variables with the exact DSL structure.
        """
        from controllers.console.app.nested_variable_utils import validate_graph_nested_variables

        # Exact graph structure from the DSL
        graph = {
            "nodes": [
                {
                    "id": "1766852370227",
                    "type": "custom",
                    "data": {
                        "title": "用户输入",
                        "type": "start",
                        "variables": [
                            {
                                "children": [
                                    {
                                        "children": [],
                                        "description": "",
                                        "required": False,
                                        "type": "text-input",
                                        "variable": "var_1766974683066",
                                    }
                                ],
                                "default": "",
                                "hint": "",
                                "label": "a",
                                "max_length": 48,
                                "options": [],
                                "placeholder": "",
                                "required": True,
                                "type": "json_object",
                                "variable": "a",
                            }
                        ],
                    },
                }
            ],
            "edges": [],
        }

        errors = validate_graph_nested_variables(graph)
        assert len(errors) == 0, f"Expected no errors, got: {errors}"


class TestBaseAppGeneratorNestedVariables:
    """Tests for BaseAppGenerator handling of nested variable types."""

    def test_validate_inputs_with_json_object_type(self):
        """
        Test that _validate_inputs correctly handles json_object type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        # Create a json_object variable entity
        variable_entity = VariableEntity(
            variable="user_data",
            label="User Data",
            type=VariableEntityType.JSON_OBJECT,
            required=True,
        )

        # Valid input - a dict
        value = {"name": "John", "age": 30}
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_with_object_type(self):
        """
        Test that _validate_inputs correctly handles object type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="config",
            label="Config",
            type=VariableEntityType.OBJECT,
            required=True,
        )

        value = {"setting1": "value1", "nested": {"key": "value"}}
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_with_array_object_type(self):
        """
        Test that _validate_inputs correctly handles array[object] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="items",
            label="Items",
            type=VariableEntityType.ARRAY_OBJECT,
            required=True,
        )

        value = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_rejects_non_dict_for_object_type(self):
        """
        Test that _validate_inputs rejects non-dict values for object types.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="user_data",
            label="User Data",
            type=VariableEntityType.JSON_OBJECT,
            required=True,
        )

        # Invalid input - a string instead of dict
        with pytest.raises(ValueError, match="must be an object"):
            generator._validate_inputs(variable_entity=variable_entity, value="not a dict")

    def test_validate_inputs_rejects_non_list_for_array_object_type(self):
        """
        Test that _validate_inputs rejects non-list values for array[object] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="items",
            label="Items",
            type=VariableEntityType.ARRAY_OBJECT,
            required=True,
        )

        # Invalid input - a dict instead of list
        with pytest.raises(ValueError, match="must be an array of objects"):
            generator._validate_inputs(variable_entity=variable_entity, value={"id": 1})

    def test_prepare_user_inputs_allows_nested_objects(self):
        """
        Test that _prepare_user_inputs allows dict values for nested object types.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variables = [
            VariableEntity(
                variable="user_data",
                label="User Data",
                type=VariableEntityType.JSON_OBJECT,
                required=True,
            ),
            VariableEntity(
                variable="name",
                label="Name",
                type=VariableEntityType.TEXT_INPUT,
                required=True,
            ),
        ]

        user_inputs = {
            "user_data": {"name": "John", "age": 30},
            "name": "Test",
        }

        # This should not raise an error
        result = generator._prepare_user_inputs(
            user_inputs=user_inputs,
            variables=variables,
            tenant_id="test_tenant",
        )

        assert result["user_data"] == {"name": "John", "age": 30}
        assert result["name"] == "Test"

    def test_prepare_user_inputs_with_dsl_structure(self):
        """
        Test _prepare_user_inputs with the exact DSL structure from user's workflow.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        # Create variable entity matching the DSL structure
        variables = [
            VariableEntity(
                variable="a",
                label="a",
                type=VariableEntityType.JSON_OBJECT,
                required=True,
                max_length=48,
                children=[
                    VariableEntity(
                        variable="var_1766974683066",
                        type=VariableEntityType.TEXT_INPUT,
                        required=False,
                    )
                ],
            )
        ]

        # User input with nested object
        user_inputs = {
            "a": {"var_1766974683066": "test value"},
        }

        # This should not raise an error
        result = generator._prepare_user_inputs(
            user_inputs=user_inputs,
            variables=variables,
            tenant_id="test_tenant",
        )

        assert result["a"] == {"var_1766974683066": "test value"}


class TestArrayTypeValidation:
    """Tests for new array type validation (array[string], array[number], array[boolean])."""

    def test_validate_inputs_with_array_string_type(self):
        """
        Test that _validate_inputs correctly handles array[string] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="tags",
            label="Tags",
            type=VariableEntityType.ARRAY_STRING,
            required=True,
        )

        # Valid input - a list of strings
        value = ["tag1", "tag2", "tag3"]
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_with_array_number_type(self):
        """
        Test that _validate_inputs correctly handles array[number] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="scores",
            label="Scores",
            type=VariableEntityType.ARRAY_NUMBER,
            required=True,
        )

        # Valid input - a list of numbers (int and float)
        value = [1, 2.5, 3, 4.7]
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_with_array_boolean_type(self):
        """
        Test that _validate_inputs correctly handles array[boolean] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="flags",
            label="Flags",
            type=VariableEntityType.ARRAY_BOOLEAN,
            required=True,
        )

        # Valid input - a list of booleans
        value = [True, False, True]
        result = generator._validate_inputs(variable_entity=variable_entity, value=value)
        assert result == value

    def test_validate_inputs_rejects_non_list_for_array_string(self):
        """
        Test that _validate_inputs rejects non-list values for array[string] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="tags",
            label="Tags",
            type=VariableEntityType.ARRAY_STRING,
            required=True,
        )

        # Invalid input - a string instead of list
        with pytest.raises(ValueError, match="must be an array of strings"):
            generator._validate_inputs(variable_entity=variable_entity, value="not a list")

    def test_validate_inputs_rejects_wrong_element_type_for_array_string(self):
        """
        Test that _validate_inputs rejects list with non-string elements for array[string] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="tags",
            label="Tags",
            type=VariableEntityType.ARRAY_STRING,
            required=True,
        )

        # Invalid input - list with numbers instead of strings
        with pytest.raises(ValueError, match="must be an array of strings"):
            generator._validate_inputs(variable_entity=variable_entity, value=[1, 2, 3])

    def test_validate_inputs_rejects_wrong_element_type_for_array_number(self):
        """
        Test that _validate_inputs rejects list with non-number elements for array[number] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="scores",
            label="Scores",
            type=VariableEntityType.ARRAY_NUMBER,
            required=True,
        )

        # Invalid input - list with strings instead of numbers
        with pytest.raises(ValueError, match="must be an array of numbers"):
            generator._validate_inputs(variable_entity=variable_entity, value=["a", "b", "c"])

    def test_validate_inputs_rejects_wrong_element_type_for_array_boolean(self):
        """
        Test that _validate_inputs rejects list with non-boolean elements for array[boolean] type.
        """
        from core.app.app_config.entities import VariableEntity, VariableEntityType
        from core.app.apps.base_app_generator import BaseAppGenerator

        generator = BaseAppGenerator()

        variable_entity = VariableEntity(
            variable="flags",
            label="Flags",
            type=VariableEntityType.ARRAY_BOOLEAN,
            required=True,
        )

        # Invalid input - list with strings instead of booleans
        with pytest.raises(ValueError, match="must be an array of booleans"):
            generator._validate_inputs(variable_entity=variable_entity, value=["true", "false"])

    def test_variable_entity_type_includes_array_types(self):
        """
        Test that VariableEntityType includes the new array types.
        """
        from core.app.app_config.entities import VariableEntityType

        # Verify new types exist
        assert VariableEntityType.ARRAY_STRING == "array[string]"
        assert VariableEntityType.ARRAY_NUMBER == "array[number]"
        assert VariableEntityType.ARRAY_BOOLEAN == "array[boolean]"

        # Verify they are not nestable (only array[object] is nestable)
        assert VariableEntityType.ARRAY_STRING.is_nestable() is False
        assert VariableEntityType.ARRAY_NUMBER.is_nestable() is False
        assert VariableEntityType.ARRAY_BOOLEAN.is_nestable() is False
