# Requirements Document

## Introduction

本文档定义了 Dify 工作流节点中支持复杂对象与数组嵌套变量传递的功能需求。该功能允许用户在节点的输入/输出配置中定义具有层级结构的变量，当选择 Object 或 Array<Object> 类型时，可以添加子变量来定义内部结构。

## Glossary

- **Nested_Variable**: 嵌套变量，指具有层级结构的变量，可以包含子变量
- **Variable_Definition**: 变量定义，描述变量的名称、类型、是否必填等属性
- **Child_Variable**: 子变量，Object 或 Array<Object> 类型变量内部的字段定义
- **Variable_Pool**: 变量池，工作流运行时存储和管理变量的核心组件
- **Variable_Selector**: 变量选择器，用于引用其他节点输出变量的路径表达式
- **Node_Input**: 节点输入，节点接收的变量配置
- **Node_Output**: 节点输出，节点产生的变量配置
- **Workflow_Node**: 工作流节点，工作流中的执行单元

## Requirements

### Requirement 1: 嵌套变量类型定义

**User Story:** As a workflow designer, I want to define nested variable structures for Object and Array<Object> types, so that I can model complex data structures in my workflows.

#### Acceptance Criteria

1. WHEN a user selects Object type for a variable, THE Variable_Definition_UI SHALL display an "Add Child" button to add sub-variables
2. WHEN a user selects Array<Object> type for a variable, THE Variable_Definition_UI SHALL display an "Add Child" button to define the object element structure
3. THE Variable_Definition_UI SHALL support the following primitive types for child variables: String, Integer, Number, Boolean, File
4. THE Variable_Definition_UI SHALL support the following array types for child variables: Array<String>, Array<Integer>, Array<Number>, Array<Object>, Array<Boolean>, Array<File>
5. THE Variable_Definition_UI SHALL support Object type for child variables to enable multi-level nesting
6. WHEN a child variable is added, THE Variable_Definition_UI SHALL display it with proper indentation to indicate hierarchy
7. THE Variable_Definition_UI SHALL allow a maximum nesting depth of 5 levels to prevent overly complex structures

### Requirement 2: 子变量属性配置

**User Story:** As a workflow designer, I want to configure properties for each child variable, so that I can specify validation rules and metadata.

#### Acceptance Criteria

1. FOR EACH child variable, THE Variable_Definition_UI SHALL allow setting a unique name within its parent scope
2. FOR EACH child variable, THE Variable_Definition_UI SHALL allow selecting a type from the supported types list
3. FOR EACH child variable, THE Variable_Definition_UI SHALL allow marking it as required or optional
4. FOR EACH child variable, THE Variable_Definition_UI SHALL allow setting a description
5. WHEN a child variable name conflicts with a sibling, THE Variable_Definition_UI SHALL display a validation error
6. THE Variable_Definition_UI SHALL validate that child variable names follow the pattern: alphanumeric characters and underscores, starting with a letter

### Requirement 3: 嵌套变量的变量池存储

**User Story:** As a workflow engine, I want to store nested variables in the variable pool, so that they can be accessed by downstream nodes.

#### Acceptance Criteria

1. WHEN a node outputs a nested variable, THE Variable_Pool SHALL store the complete nested structure
2. THE Variable_Pool SHALL support accessing nested values using dot-notation selectors (e.g., `node_id.variable.child.grandchild`)
3. WHEN accessing a non-existent nested path, THE Variable_Pool SHALL return None without throwing an error
4. THE Variable_Pool SHALL preserve the type information for each level of nesting
5. WHEN a nested variable is updated, THE Variable_Pool SHALL maintain immutability by creating a new copy

### Requirement 4: 嵌套变量的节点间传递

**User Story:** As a workflow designer, I want to pass nested variables between nodes, so that I can build complex data processing pipelines.

#### Acceptance Criteria

1. WHEN configuring a node input, THE Variable_Selector_UI SHALL allow selecting nested paths from upstream node outputs
2. THE Variable_Selector_UI SHALL display the nested structure as an expandable tree
3. WHEN a nested path is selected, THE Variable_Selector_UI SHALL validate type compatibility with the target input
4. THE Variable_Template_Parser SHALL support nested path references in template strings (e.g., `{{#node_id.user.profile.name#}}`)
5. WHEN a referenced nested path does not exist at runtime, THE Workflow_Engine SHALL use the default value if configured, or return an empty value
6. WHEN selecting an Array<Object> type variable with children, THE Variable_Selector_UI SHALL preserve the original array[object] type instead of converting it to object type
7. WHEN determining the type of a variable with children, THE Type_Resolver SHALL return the original variable type (object or array[object]) rather than defaulting to object

### Requirement 5: 嵌套变量的序列化与反序列化

**User Story:** As a system, I want to serialize and deserialize nested variable definitions, so that workflow configurations can be saved and loaded correctly.

#### Acceptance Criteria

1. THE Workflow_Serializer SHALL serialize nested variable definitions to JSON format preserving the complete hierarchy
2. THE Workflow_Deserializer SHALL reconstruct nested variable definitions from JSON format
3. WHEN deserializing, THE Workflow_Deserializer SHALL validate the structure against the schema
4. IF deserialization encounters invalid data, THEN THE Workflow_Deserializer SHALL return a descriptive error message
5. THE serialization format SHALL be backward compatible with existing non-nested variable definitions

### Requirement 6: 嵌套变量的运行时验证

**User Story:** As a workflow engine, I want to validate nested variable values at runtime, so that type mismatches are caught early.

#### Acceptance Criteria

1. WHEN a node receives input, THE Workflow_Engine SHALL validate the value structure against the nested variable definition
2. IF a required child variable is missing, THEN THE Workflow_Engine SHALL report a validation error with the specific path
3. IF a child variable has an incorrect type, THEN THE Workflow_Engine SHALL report a type mismatch error with expected and actual types
4. THE Workflow_Engine SHALL support optional child variables that may be absent in the input
5. WHEN validation fails, THE Workflow_Engine SHALL provide a clear error message indicating the problematic path and reason

### Requirement 7: 前端嵌套变量编辑器

**User Story:** As a workflow designer, I want an intuitive UI to edit nested variable structures, so that I can easily define complex data models.

#### Acceptance Criteria

1. THE Nested_Variable_Editor SHALL display child variables with visual indentation and connecting lines
2. THE Nested_Variable_Editor SHALL provide expand/collapse controls for Object and Array<Object> types
3. THE Nested_Variable_Editor SHALL allow drag-and-drop reordering of child variables within the same parent
4. THE Nested_Variable_Editor SHALL provide a delete button for each child variable
5. WHEN deleting a parent variable, THE Nested_Variable_Editor SHALL also remove all its child variables
6. THE Nested_Variable_Editor SHALL display type icons to distinguish different variable types visually

### Requirement 8: API 接口支持

**User Story:** As an API consumer, I want to interact with nested variables through the API, so that I can programmatically configure workflows.

#### Acceptance Criteria

1. THE Workflow_API SHALL accept nested variable definitions in the node configuration payload
2. THE Workflow_API SHALL return nested variable definitions in the workflow export response
3. THE Workflow_Run_API SHALL accept nested object values as input parameters
4. THE Workflow_Run_API SHALL return nested object values in the output response
5. THE API_Documentation SHALL include examples of nested variable configurations

### Requirement 9: JSON 编辑模式支持

**User Story:** As a workflow designer, I want to switch between form mode and JSON mode when editing complex variables, so that I can choose the most convenient way to input data.

#### Acceptance Criteria

1. FOR complex variable types (object, array[object], array[string], array[number], array[boolean]) with children, THE Input_UI SHALL display mode switcher buttons
2. WHEN form mode is selected, THE Input_UI SHALL display structured form inputs for each field
3. WHEN JSON mode is selected, THE Input_UI SHALL display a JSON code editor
4. THE JSON_Editor SHALL validate JSON syntax and parse valid JSON into structured data
5. THE mode switcher SHALL be available in workflow test run, configuration debug panel, and share pages
6. THE mode preference SHALL be maintained per variable during the editing session

### Requirement 10: LLM 节点输入变量支持

**User Story:** As a workflow designer, I want to define input variables in LLM nodes similar to code execution nodes, so that I can pass structured data to LLM prompts.

#### Acceptance Criteria

1. THE LLM_Node_Panel SHALL display an "Input Variables" section
2. THE Input_Variables_Section SHALL allow adding, editing, and removing input variables
3. EACH input variable SHALL have a name and a variable selector to reference upstream node outputs
4. THE LLM_Node_Execution SHALL resolve input variables and make them available in the prompt context
5. THE Input_Variables SHALL support all variable types including nested structures
