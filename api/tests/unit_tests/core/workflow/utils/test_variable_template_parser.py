import dataclasses

from core.workflow.nodes.base import variable_template_parser
from core.workflow.nodes.base.entities import VariableSelector


def test_extract_selectors_from_template():
    template = (
        "Hello, {{#sys.user_id#}}! Your query is {{#node_id.custom_query#}}. And your key is {{#env.secret_key#}}."
    )
    selectors = variable_template_parser.extract_selectors_from_template(template)
    assert selectors == [
        VariableSelector(variable="#sys.user_id#", value_selector=["sys", "user_id"]),
        VariableSelector(variable="#node_id.custom_query#", value_selector=["node_id", "custom_query"]),
        VariableSelector(variable="#env.secret_key#", value_selector=["env", "secret_key"]),
    ]


def test_extract_selectors_with_nested_paths():
    """Test extraction of selectors with nested object paths (e.g., user.profile.name)."""
    template = "Hello, {{#node_id.user.profile.name#}}! Your email is {{#node_id.user.profile.email#}}."
    selectors = variable_template_parser.extract_selectors_from_template(template)
    assert selectors == [
        VariableSelector(
            variable="#node_id.user.profile.name#",
            value_selector=["node_id", "user", "profile", "name"],
        ),
        VariableSelector(
            variable="#node_id.user.profile.email#",
            value_selector=["node_id", "user", "profile", "email"],
        ),
    ]


def test_extract_selectors_with_deep_nesting():
    """Test extraction of selectors with deep nesting (up to 5 levels as per requirements)."""
    template = "{{#node_id.level1.level2.level3.level4.level5#}}"
    selectors = variable_template_parser.extract_selectors_from_template(template)
    assert len(selectors) == 1
    assert selectors[0].value_selector == ["node_id", "level1", "level2", "level3", "level4", "level5"]


def test_variable_template_parser_nested_paths():
    """Test VariableTemplateParser with nested object paths."""
    template = "User: {{#start.user_data.name#}}, Age: {{#start.user_data.profile.age#}}"
    parser = variable_template_parser.VariableTemplateParser(template)

    # Test extract
    keys = parser.extract()
    assert "#start.user_data.name#" in keys
    assert "#start.user_data.profile.age#" in keys

    # Test extract_variable_selectors
    selectors = parser.extract_variable_selectors()
    assert len(selectors) == 2

    selector_map = {s.variable: s.value_selector for s in selectors}
    assert selector_map["#start.user_data.name#"] == ["start", "user_data", "name"]
    assert selector_map["#start.user_data.profile.age#"] == ["start", "user_data", "profile", "age"]


def test_variable_template_parser_format_with_nested_paths():
    """Test VariableTemplateParser.format() with nested path inputs."""
    template = "Hello, {{#node_id.user.profile.name#}}! Age: {{#node_id.user.profile.age#}}"
    parser = variable_template_parser.VariableTemplateParser(template)

    inputs = {
        "#node_id.user.profile.name#": "John",
        "#node_id.user.profile.age#": 25,
    }
    result = parser.format(inputs)
    assert result == "Hello, John! Age: 25"


def test_variable_template_parser_format_with_missing_nested_path():
    """Test VariableTemplateParser.format() when nested path is not in inputs."""
    template = "Hello, {{#node_id.user.profile.name#}}!"
    parser = variable_template_parser.VariableTemplateParser(template)

    # When key is not found, the original placeholder is preserved but with single braces
    # This is due to the remove_template_variables method which converts {{...}} to {...}
    inputs: dict[str, str] = {}
    result = parser.format(inputs)
    assert result == "Hello, {#node_id.user.profile.name#}!"


def test_invalid_references():
    @dataclasses.dataclass
    class TestCase:
        name: str
        template: str

    cases = [
        TestCase(
            name="lack of closing brace",
            template="Hello, {{#sys.user_id#",
        ),
        TestCase(
            name="lack of opening brace",
            template="Hello, #sys.user_id#}}",
        ),
        TestCase(
            name="lack selector name",
            template="Hello, {{#sys#}}",
        ),
        TestCase(
            name="empty node name part",
            template="Hello, {{#.user_id#}}",
        ),
    ]
    for idx, c in enumerate(cases, 1):
        fail_msg = f"Test case {c.name} failed, index={idx}"
        selectors = variable_template_parser.extract_selectors_from_template(c.template)
        assert selectors == [], fail_msg
        parser = variable_template_parser.VariableTemplateParser(c.template)
        assert parser.extract_variable_selectors() == [], fail_msg
