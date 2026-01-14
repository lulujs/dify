# Requirements Document

## Introduction

为 Dify 工作流编排的 LLM 节点视觉输入功能增加 base64 图片字符串输入支持。当前 LLM 节点的视觉输入只支持从变量池中选择文件变量，本需求将增加直接输入 base64 编码图片字符串的能力。

## Glossary

- **LLM_Node**: 工作流中的大语言模型节点
- **Vision_Input**: LLM 节点的视觉输入功能，用于处理图片等多模态内容
- **Base64_String**: Base64 编码的图片数据字符串
- **Variable_Pool**: 工作流运行时的变量池，存储节点间传递的数据
- **File_Manager**: 文件管理器，负责文件的存储和转换

## Requirements

### Requirement 1: 支持 Base64 字符串输入配置

**User Story:** 作为工作流开发者，我希望在 LLM 节点的视觉输入中可以直接输入 base64 图片字符串变量，以便处理动态生成的图片数据。

#### Acceptance Criteria

1. WHEN 用户在前端配置 LLM 节点的视觉输入时，THE System SHALL 提供 base64 字符串输入选项
2. WHEN 用户选择 base64 字符串输入模式时，THE System SHALL 显示变量选择器用于选择包含 base64 字符串的变量
3. WHEN 用户配置完成时，THE System SHALL 保存 base64 输入配置到节点数据中

### Requirement 2: Base64 字符串验证

**User Story:** 作为系统管理员，我希望系统能验证 base64 字符串的合法性，以防止无效数据导致节点执行失败。

#### Acceptance Criteria

1. WHEN 后端接收到 base64 字符串时，THE System SHALL 验证字符串格式是否为有效的 base64 编码
2. WHEN base64 字符串解码后，THE System SHALL 验证数据是否为有效的图片格式（JPEG, PNG, GIF, WEBP）
3. IF base64 字符串验证失败，THEN THE System SHALL 抛出描述性错误信息
4. WHEN base64 字符串包含 data URI scheme 前缀时，THE System SHALL 正确解析并提取实际的 base64 数据

### Requirement 3: Base64 到 File 对象转换

**User Story:** 作为系统开发者，我希望 base64 字符串能够转换为标准的 File 对象，以便复用现有的文件处理逻辑。

#### Acceptance Criteria

1. WHEN base64 字符串验证通过后，THE System SHALL 将其转换为 File 对象
2. WHEN 转换 File 对象时，THE System SHALL 正确设置文件类型（image/jpeg, image/png 等）
3. WHEN 转换 File 对象时，THE System SHALL 生成唯一的文件标识符
4. WHEN 转换完成后，THE System SHALL 将 File 对象存储到文件系统中

### Requirement 4: 集成到现有视觉输入流程

**User Story:** 作为工作流开发者，我希望 base64 输入的图片能够与文件变量输入的图片一样被 LLM 处理，保持一致的用户体验。

#### Acceptance Criteria

1. WHEN LLM 节点执行时，THE System SHALL 从变量池中获取 base64 字符串变量
2. WHEN 获取到 base64 字符串后，THE System SHALL 验证并转换为 File 对象
3. WHEN 转换完成后，THE System SHALL 将 File 对象合并到文件列表中
4. WHEN 构建提示消息时，THE System SHALL 将 base64 转换的文件与其他文件一起处理

### Requirement 5: 错误处理和日志记录

**User Story:** 作为系统运维人员，我希望系统能够记录 base64 处理过程中的错误，以便快速定位问题。

#### Acceptance Criteria

1. WHEN base64 验证失败时，THE System SHALL 记录详细的错误日志
2. WHEN base64 转换失败时，THE System SHALL 记录失败原因和输入数据的摘要信息
3. IF 处理过程中发生异常，THEN THE System SHALL 返回用户友好的错误消息
4. WHEN 成功处理 base64 输入时，THE System SHALL 记录处理的文件数量和大小

### Requirement 6: 前端用户界面

**User Story:** 作为工作流开发者，我希望前端界面清晰地展示 base64 输入选项，并提供必要的提示信息。

#### Acceptance Criteria

1. WHEN 用户启用视觉输入时，THE UI SHALL 显示输入模式选择（文件变量 / Base64 字符串）
2. WHEN 用户选择 Base64 字符串模式时，THE UI SHALL 显示提示文案："请选择包含 base64 图片字符串的变量"
3. WHEN 用户选择变量时，THE UI SHALL 提供变量选择器组件
4. WHEN 配置保存时，THE UI SHALL 将 base64 输入配置序列化到节点配置中

### Requirement 7: 向后兼容性

**User Story:** 作为现有用户，我希望新功能不会影响我已有的工作流配置和执行。

#### Acceptance Criteria

1. WHEN 加载旧版本的工作流配置时，THE System SHALL 正确识别并使用文件变量输入模式
2. WHEN 新旧配置共存时，THE System SHALL 正确处理两种输入模式
3. WHEN 未配置 base64 输入时，THE System SHALL 保持原有的文件变量处理逻辑
