# Implementation Plan: Nested Variable Support

## Overview

本实现计划将嵌套变量支持功能分解为可执行的开发任务，按照后端核心 → 后端 API → 前端组件 → 集成测试的顺序进行。

## Tasks

- [x] 1. 创建嵌套变量核心数据结构
  - [x] 1.1 创建 `NestedVariableType` 枚举和 `NestedVariableDefinition` 模型
    - 在 `api/core/workflow/entities/` 目录下创建 `nested_variable.py`
    - 实现类型枚举、变量定义模型、名称验证器
    - _Requirements: 1.3, 1.4, 1.5, 2.1, 2.6_
  - [ ]* 1.2 编写属性测试：变量名称格式验证
    - **Property 4: Variable Name Format Validation**
    - **Validates: Requirements 2.6**
  - [x] 1.3 创建 `NodeInputDefinition` 和 `NodeOutputDefinition` 模型
    - 在 `api/core/workflow/entities/` 目录下创建 `node_input.py`
    - 实现增强的变量选择器和节点输入输出定义
    - _Requirements: 2.2, 2.3, 2.4_

- [-] 2. 实现嵌套变量验证器
  - [x] 2.1 创建 `NestedVariableValidator` 类
    - 在 `api/core/workflow/validators/` 目录下创建 `nested_variable_validator.py`
    - 实现定义验证和值验证方法
    - _Requirements: 1.7, 2.5, 6.1, 6.2, 6.3, 6.4_
  - [ ]* 2.2 编写属性测试：嵌套深度限制
    - **Property 2: Nesting Depth Enforcement**
    - **Validates: Requirements 1.7**
  - [ ]* 2.3 编写属性测试：子变量名称唯一性
    - **Property 3: Child Name Uniqueness**
    - **Validates: Requirements 2.1, 2.5**
  - [ ]* 2.4 编写属性测试：运行时验证完整性
    - **Property 10: Runtime Validation Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.4**

- [x] 3. Checkpoint - 核心数据结构验证
  - 确保所有测试通过，如有问题请询问用户

- [-] 4. 增强变量池支持嵌套操作
  - [x] 4.1 扩展 `VariablePool` 类支持嵌套变量
    - 修改 `api/core/workflow/runtime/variable_pool.py`
    - 添加 `add_nested`、`get_nested`、`set_nested` 方法
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  - [ ]* 4.2 编写属性测试：变量池存储和检索
    - **Property 5: Variable Pool Storage and Retrieval**
    - **Validates: Requirements 3.1, 3.2, 3.4**
  - [ ]* 4.3 编写属性测试：变量池不可变性
    - **Property 6: Variable Pool Immutability**
    - **Validates: Requirements 3.5**

- [x] 5. 增强变量模板解析器
  - [x] 5.1 扩展 `VariableTemplateParser` 支持嵌套路径
    - 修改 `api/core/workflow/nodes/base/variable_template_parser.py`
    - 支持 `{{#node_id.var.child.grandchild#}}` 格式
    - _Requirements: 4.4_
  - [ ]* 5.2 编写属性测试：模板解析器嵌套路径支持
    - **Property 7: Template Parser Nested Path Support**
    - **Validates: Requirements 4.4**

- [ ] 6. 实现序列化和反序列化
  - [x] 6.1 更新工作流序列化器支持嵌套变量
    - 修改相关序列化逻辑以处理嵌套结构
    - 确保向后兼容性
    - _Requirements: 5.1, 5.2, 5.3, 5.5_
  - [ ]* 6.2 编写属性测试：序列化往返
    - **Property 8: Serialization Round-Trip**
    - **Validates: Requirements 5.1, 5.2**
  - [ ]* 6.3 编写属性测试：向后兼容性
    - **Property 9: Backward Compatibility**
    - **Validates: Requirements 5.5**

- [x] 7. Checkpoint - 后端核心功能验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 8. 更新 API 接口
  - [x] 8.1 更新工作流 API 支持嵌套变量配置
    - 修改 `api/controllers/console/app/workflow.py`
    - 更新请求/响应模型以包含嵌套变量
    - _Requirements: 8.1, 8.2_
  - [x] 8.2 更新工作流运行 API 支持嵌套输入输出
    - 修改工作流执行相关 API
    - 支持嵌套对象作为输入参数和输出结果
    - _Requirements: 8.3, 8.4_
  - [ ]* 8.3 编写属性测试：API 往返
    - **Property 12: API Round-Trip**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 9. 创建前端类型定义
  - [x] 9.1 创建 TypeScript 类型定义
    - 在 `web/types/workflow/` 目录下创建 `nested-variable.ts`
    - 定义 `NestedVariableType`、`NestedVariableDefinition` 等类型
    - _Requirements: 1.3, 1.4_

- [x] 10. 实现前端嵌套变量编辑器
  - [x] 10.1 创建 `NestedVariableEditor` 组件
    - 在 `web/app/components/workflow/nodes/` 目录下创建组件
    - 实现变量列表渲染、添加、删除功能
    - _Requirements: 7.1, 7.4, 7.5_
  - [x] 10.2 实现变量行组件 `VariableRow`
    - 实现单个变量的编辑界面
    - 包含名称输入、类型选择、必填开关
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 10.3 实现子变量添加功能
    - 为 Object 和 Array<Object> 类型显示添加子项按钮
    - 实现递归嵌套渲染
    - _Requirements: 1.1, 1.2, 1.6_
  - [x] 10.4 实现展开/折叠功能
    - 为嵌套类型添加展开/折叠控制
    - _Requirements: 7.2_
  - [ ]* 10.5 编写属性测试：级联删除
    - **Property 11: Cascade Delete**
    - **Validates: Requirements 7.5**

- [x] 11. 实现前端变量选择器增强
  - [x] 11.1 更新 `VariableSelector` 组件支持嵌套路径
    - 修改变量选择器以显示嵌套结构树
    - 支持选择嵌套路径
    - _Requirements: 4.1, 4.2_
  - [x] 11.2 实现类型兼容性验证
    - 在选择嵌套路径时验证类型兼容性
    - _Requirements: 4.3_

- [x] 12. 集成到现有节点
  - [x] 12.1 更新 Start 节点支持嵌套变量输入
    - 修改 Start 节点配置面板
    - 集成嵌套变量编辑器
    - _Requirements: 1.1, 1.2_
  - [x] 12.2 更新其他支持变量的节点
    - 更新 Code、HTTP、Tool 等节点
    - 确保嵌套变量在各节点间正确传递
    - _Requirements: 4.1_

- [x] 13. 添加国际化支持
  - [x] 13.1 添加中英文翻译
    - 在 `web/i18n/en-US/` 和 `web/i18n/zh-Hans/` 添加相关文案
    - 包括类型名称、按钮文本、错误消息等
    - _Requirements: 7.1_

- [x] 14. Checkpoint - 前端功能验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 15. 端到端测试
  - [x]* 15.1 编写端到端测试用例
    - 测试完整的嵌套变量定义和传递流程
    - 测试 API 调用和响应
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 16. 修复嵌套变量保存/发布丢失问题
  - [x] 16.1 为 `VariableEntity` 添加 `children` 字段
    - 修改 `api/core/app/app_config/entities.py`
    - 添加 `OBJECT` 和 `ARRAY_OBJECT` 类型到 `VariableEntityType`
    - 添加 `is_nestable()` 方法
    - 添加递归 `children` 字段支持嵌套结构
    - _Requirements: 1.1, 1.2, 5.1, 5.2_
  - [x] 16.2 编写测试验证 `VariableEntity` 保留 `children` 字段
    - 测试 `VariableEntity` 通过 Pydantic 验证时保留 `children`
    - 测试 `StartNodeData` 验证时保留嵌套变量
    - 测试序列化往返保留嵌套结构
    - _Requirements: 5.1, 5.2, 5.5_

- [x] 17. Final Checkpoint - 完整功能验证
  - 确保所有测试通过，如有问题请询问用户

- [x] 18. 修复 Array[Object] 类型识别 Bug
  - [x] 18.1 修复 `getVarType` 函数中的类型识别问题
    - 修改 `web/app/components/workflow/nodes/_base/components/variable/utils.ts`
    - 当变量有 `children.schema.properties` 且 `valueSelector.length === 2` 时，返回原始 `targetVar.type` 而不是默认的 `VarType.object`
    - 确保 `array[object]` 类型的变量在有子变量时仍然保持 `array[object]` 类型
    - _Requirements: 4.6, 4.7_
  - [x] 18.2 修复相关组件中的类型识别
    - 修改 `web/app/components/workflow/nodes/_base/components/variable/var-reference-vars.tsx`
    - 修改 `web/app/components/workflow/nodes/_base/components/variable/object-child-tree-panel/picker/field.tsx`
    - _Requirements: 4.6, 4.7_

- [x] 19. Configuration 页面添加新变量类型支持
  - [x] 19.1 更新变量类型选择器
    - 修改 `web/app/components/app/configuration/config-var/select-var-type.tsx`
    - 添加 `object`、`array[object]`、`array[string]`、`array[number]`、`array[boolean]` 类型选项
    - _Requirements: 1.3, 1.4_
  - [x] 19.2 更新变量配置模态框
    - 修改 `web/app/components/app/configuration/config-var/config-modal/index.tsx`
    - 支持复杂类型的子变量定义
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4_
  - [x] 19.3 更新变量列表组件
    - 修改 `web/app/components/app/configuration/config-var/index.tsx`
    - 正确显示复杂类型变量
    - _Requirements: 7.1_

- [x] 20. 调试与预览页面支持新类型输入
  - [x] 20.1 更新 PromptValuePanel 组件
    - 修改 `web/app/components/app/configuration/prompt-value-panel/index.tsx`
    - 支持 `object`、`array[object]`、`array[string]`、`array[number]`、`array[boolean]` 类型的输入
    - _Requirements: 7.1, 8.3_
  - [x] 20.2 更新 debug 模型类型定义
    - 修改 `web/models/debug.ts`
    - 添加 `PromptVariableChild` 类型支持嵌套结构
    - _Requirements: 9.1_

- [x] 21. 修复发布时子变量定义未保存的 Bug
  - [x] 21.1 更新前端模型配置工具函数
    - 修改 `web/utils/model-config.ts`
    - 确保 `children` 字段在发布时被正确序列化
    - _Requirements: 5.1, 5.2_
  - [x] 21.2 更新后端变量管理器
    - 修改 `api/core/app/app_config/easy_ui_based_app/variables/manager.py`
    - 支持解析和保存嵌套变量定义
    - _Requirements: 5.1, 5.2, 5.3_

- [x] 22. LLM 节点增加输入变量功能
  - [x] 22.1 更新 LLM 节点类型定义
    - 修改 `web/app/components/workflow/nodes/llm/types.ts`
    - 添加 `input_variables` 字段
    - _Requirements: 4.1_
  - [x] 22.2 更新 LLM 节点配置逻辑
    - 修改 `web/app/components/workflow/nodes/llm/use-config.ts`
    - 实现输入变量的增删改逻辑
    - _Requirements: 4.1, 4.2_
  - [x] 22.3 更新 LLM 节点面板
    - 修改 `web/app/components/workflow/nodes/llm/panel.tsx`
    - 添加输入变量配置 UI
    - _Requirements: 7.1_
  - [x] 22.4 更新后端 LLM 节点实体和执行逻辑
    - 修改 `api/core/workflow/nodes/llm/entities.py`
    - 修改 `api/core/workflow/nodes/llm/node.py`
    - 支持输入变量的解析和执行
    - _Requirements: 8.3, 8.4_

- [x] 23. ShareLayout 分享页面支持新复杂变量类型输入
  - [x] 23.1 更新 text-generation run-once 组件
    - 修改 `web/app/components/share/text-generation/run-once/index.tsx`
    - 支持复杂类型变量的输入
    - _Requirements: 7.1, 8.3_
  - [x] 23.2 更新 embedded-chatbot inputs-form 组件
    - 修改 `web/app/components/base/chat/embedded-chatbot/inputs-form/content.tsx`
    - 支持复杂类型变量的输入
    - _Requirements: 7.1, 8.3_
  - [x] 23.3 更新 chat-with-history inputs-form 组件
    - 修改 `web/app/components/base/chat/chat-with-history/inputs-form/content.tsx`
    - 支持复杂类型变量的输入
    - _Requirements: 7.1, 8.3_

- [x] 24. 将 json_object 类型重命名为 object
  - [x] 24.1 更新前端类型定义
    - 修改 `web/app/components/workflow/types.ts`
    - 将 `json_object` 改为 `object`
    - _Requirements: 1.3_
  - [x] 24.2 更新后端类型定义和处理逻辑
    - 修改 `api/controllers/console/app/nested_variable_utils.py`
    - 修改 `api/core/app/app_config/entities.py`
    - 修改 `api/core/app/app_config/easy_ui_based_app/variables/manager.py`
    - 修改 `api/core/app/apps/base_app_generator.py`
    - _Requirements: 1.3, 5.5_

- [x] 25. Workflow Test Run 复杂变量支持 JSON 编辑模式
  - [x] 25.1 更新 FormItem 组件
    - 修改 `web/app/components/workflow/nodes/_base/components/before-run-form/form-item.tsx`
    - 添加表单模式/JSON 模式切换功能
    - _Requirements: 7.1_
  - [x] 25.2 更新后端输入值解析
    - 修改 `api/core/app/apps/base_app_generator.py`
    - 支持 JSON 字符串输入的解析
    - _Requirements: 8.3_

- [x] 26. ShareLayout 分享页面复杂变量添加 JSON 编辑模式
  - [x] 26.1 更新 text-generation run-once 组件
    - 修改 `web/app/components/share/text-generation/run-once/index.tsx`
    - 添加 JSON 编辑模式切换
    - _Requirements: 7.1_
  - [x] 26.2 更新 embedded-chatbot inputs-form 组件
    - 修改 `web/app/components/base/chat/embedded-chatbot/inputs-form/content.tsx`
    - 添加 JSON 编辑模式切换
    - _Requirements: 7.1_
  - [x] 26.3 更新 chat-with-history inputs-form 组件
    - 修改 `web/app/components/base/chat/chat-with-history/inputs-form/content.tsx`
    - 添加 JSON 编辑模式切换
    - _Requirements: 7.1_

- [x] 27. Configuration 页面调试与预览功能添加 JSON 编辑模式
  - [x] 27.1 更新 PromptValuePanel 组件
    - 修改 `web/app/components/app/configuration/prompt-value-panel/index.tsx`
    - 添加 `InputMode` 类型和 `inputModes` 状态
    - 添加 `getInputMode` / `setInputMode` 函数
    - 添加 `handleJsonChange` / `getJsonValue` 函数
    - 为复杂变量类型添加模式切换按钮
    - _Requirements: 7.1_

## Notes

- 任务标记 `*` 的为可选测试任务，可根据时间安排决定是否实现
- 每个 Checkpoint 用于验证阶段性成果，确保质量
- 属性测试使用 Hypothesis 库，需要在测试环境中安装
- 前端测试使用 Jest 和 React Testing Library
