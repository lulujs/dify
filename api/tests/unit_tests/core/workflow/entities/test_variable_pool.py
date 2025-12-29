from core.variables.segments import (
    BooleanSegment,
    IntegerSegment,
    NoneSegment,
    StringSegment,
)
from core.workflow.runtime import VariablePool


class TestVariablePoolGetAndNestedAttribute:
    #
    # _get_nested_attribute tests
    #
    def test__get_nested_attribute_existing_key(self):
        pool = VariablePool.empty()
        obj = {"a": 123}
        segment = pool._get_nested_attribute(obj, "a")
        assert segment is not None
        assert segment.value == 123

    def test__get_nested_attribute_missing_key(self):
        pool = VariablePool.empty()
        obj = {"a": 123}
        segment = pool._get_nested_attribute(obj, "b")
        assert segment is None

    def test__get_nested_attribute_non_dict(self):
        pool = VariablePool.empty()
        obj = ["not", "a", "dict"]
        segment = pool._get_nested_attribute(obj, "a")
        assert segment is None

    def test__get_nested_attribute_with_none_value(self):
        pool = VariablePool.empty()
        obj = {"a": None}
        segment = pool._get_nested_attribute(obj, "a")
        assert segment is not None
        assert isinstance(segment, NoneSegment)

    def test__get_nested_attribute_with_empty_string(self):
        pool = VariablePool.empty()
        obj = {"a": ""}
        segment = pool._get_nested_attribute(obj, "a")
        assert segment is not None
        assert isinstance(segment, StringSegment)
        assert segment.value == ""

    #
    # get tests
    #
    def test_get_simple_variable(self):
        pool = VariablePool.empty()
        pool.add(("node1", "var1"), "value1")
        segment = pool.get(("node1", "var1"))
        assert segment is not None
        assert segment.value == "value1"

    def test_get_missing_variable(self):
        pool = VariablePool.empty()
        result = pool.get(("node1", "unknown"))
        assert result is None

    def test_get_with_too_short_selector(self):
        pool = VariablePool.empty()
        result = pool.get(("only_node",))
        assert result is None

    def test_get_nested_object_attribute(self):
        pool = VariablePool.empty()
        obj_value = {"inner": "hello"}
        pool.add(("node1", "obj"), obj_value)

        # simulate selector with nested attr
        segment = pool.get(("node1", "obj", "inner"))
        assert segment is not None
        assert segment.value == "hello"

    def test_get_nested_object_missing_attribute(self):
        pool = VariablePool.empty()
        obj_value = {"inner": "hello"}
        pool.add(("node1", "obj"), obj_value)

        result = pool.get(("node1", "obj", "not_exist"))
        assert result is None

    def test_get_nested_object_attribute_with_falsy_values(self):
        pool = VariablePool.empty()
        obj_value = {
            "inner_none": None,
            "inner_empty": "",
            "inner_zero": 0,
            "inner_false": False,
        }
        pool.add(("node1", "obj"), obj_value)

        segment_none = pool.get(("node1", "obj", "inner_none"))
        assert segment_none is not None
        assert isinstance(segment_none, NoneSegment)

        segment_empty = pool.get(("node1", "obj", "inner_empty"))
        assert segment_empty is not None
        assert isinstance(segment_empty, StringSegment)
        assert segment_empty.value == ""

        segment_zero = pool.get(("node1", "obj", "inner_zero"))
        assert segment_zero is not None
        assert isinstance(segment_zero, IntegerSegment)
        assert segment_zero.value == 0

        segment_false = pool.get(("node1", "obj", "inner_false"))
        assert segment_false is not None
        assert isinstance(segment_false, BooleanSegment)
        assert segment_false.value is False


class TestVariablePoolGetNotModifyVariableDictionary:
    _NODE_ID = "start"
    _VAR_NAME = "name"

    def test_convert_to_template_should_not_introduce_extra_keys(self):
        pool = VariablePool.empty()
        pool.add([self._NODE_ID, self._VAR_NAME], 0)
        pool.convert_template("The start.name is {{#start.name#}}")
        assert "The start" not in pool.variable_dictionary

    def test_get_should_not_modify_variable_dictionary(self):
        pool = VariablePool.empty()
        pool.get([self._NODE_ID, self._VAR_NAME])
        assert len(pool.variable_dictionary) == 1  # only contains `sys` node id
        assert "start" not in pool.variable_dictionary

        pool = VariablePool.empty()
        pool.add([self._NODE_ID, self._VAR_NAME], "Joe")
        pool.get([self._NODE_ID, "count"])
        start_subdict = pool.variable_dictionary[self._NODE_ID]
        assert "count" not in start_subdict


class TestVariablePoolNestedPathSupport:
    """Test nested path support for variable pool operations."""

    def test_get_deeply_nested_attribute(self):
        """Test accessing deeply nested attributes (up to 5 levels)."""
        pool = VariablePool.empty()
        nested_obj = {"level1": {"level2": {"level3": {"level4": {"level5": "deep_value"}}}}}
        pool.add(("node1", "data"), nested_obj)

        # Access 5 levels deep
        segment = pool.get(("node1", "data", "level1", "level2", "level3", "level4", "level5"))
        assert segment is not None
        assert segment.value == "deep_value"

    def test_convert_template_with_nested_paths(self):
        """Test convert_template with nested object paths."""
        pool = VariablePool.empty()
        pool.add(("node1", "user"), {"name": "John", "profile": {"email": "john@example.com", "age": 25}})

        template = (
            "Hello, {{#node1.user.name#}}! Email: {{#node1.user.profile.email#}}, Age: {{#node1.user.profile.age#}}"
        )
        result = pool.convert_template(template)

        assert result.text == "Hello, John! Email: john@example.com, Age: 25"

    def test_convert_template_with_nonexistent_nested_path(self):
        """Test convert_template when nested path doesn't exist."""
        pool = VariablePool.empty()
        pool.add(("node1", "user"), {"name": "John"})

        # Non-existent nested path should be treated as text
        template = "{{#node1.user.nonexistent.path#}}"
        result = pool.convert_template(template)

        # When path doesn't exist, it's treated as plain text
        assert result.text == "node1.user.nonexistent.path"

    def test_get_nested_method_with_dot_notation(self):
        """Test get_nested method with dot-notation path."""
        pool = VariablePool.empty()
        pool.add(("node1", "data"), {"user": {"profile": {"name": "Alice"}}})

        # Using get_nested with dot-notation
        segment = pool.get_nested(("node1", "data"), "user.profile.name")
        assert segment is not None
        assert segment.value == "Alice"

        # Without nested_path, returns the whole object
        segment_full = pool.get_nested(("node1", "data"))
        assert segment_full is not None
        assert isinstance(segment_full.value, dict)

    def test_set_nested_method(self):
        """Test set_nested method for updating nested values."""
        pool = VariablePool.empty()
        pool.add(("node1", "data"), {"user": {"name": "Original"}})

        # Update nested value
        success = pool.set_nested(("node1", "data"), "user.name", "Updated")
        assert success is True

        # Verify the update
        segment = pool.get(("node1", "data", "user", "name"))
        assert segment is not None
        assert segment.value == "Updated"

    def test_set_nested_creates_intermediate_paths(self):
        """Test that set_nested creates intermediate paths if they don't exist."""
        pool = VariablePool.empty()
        pool.add(("node1", "data"), {})

        # Set a nested value where intermediate paths don't exist
        success = pool.set_nested(("node1", "data"), "new.nested.path", "value")
        assert success is True

        # Verify the nested structure was created
        segment = pool.get(("node1", "data", "new", "nested", "path"))
        assert segment is not None
        assert segment.value == "value"
