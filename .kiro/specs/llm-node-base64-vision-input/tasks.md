# Implementation Plan: LLM Node Base64 Vision Input

## Overview

本实现计划将为 Dify 工作流编排的 LLM 节点视觉输入功能增加 base64 图片字符串输入支持。实现将分为后端核心功能、LLM 节点集成、测试和前端 UI 四个主要部分。

## Tasks

- [x] 1. 后端实体和异常类扩展
  - 扩展 `VisionConfig` 实体以支持 base64 输入模式
  - 添加新的异常类用于 base64 处理错误
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 实现 Base64 验证器
  - [x] 2.1 创建 `Base64Validator` 类
    - 实现 base64 格式验证
    - 实现 data URI scheme 解析
    - 实现图片格式检测和验证
    - _Requirements: 2.1, 2.2, 2.4_

  - [ ]* 2.2 编写 Base64Validator 单元测试
    - 测试有效的 base64 字符串
    - 测试 data URI scheme 解析
    - 测试各种图片格式
    - 测试无效输入的错误处理
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [ ]* 2.3 编写 Base64Validator 属性测试
    - **Property 1: Base64 格式验证正确性**
    - **Property 2: Base64 验证拒绝无效输入**
    - **Property 3: Data URI Scheme 解析正确性**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

- [x] 3. 实现 Base64 到 File 转换器
  - [x] 3.1 创建 `Base64ToFileConverter` 类
    - 实现 base64 到 File 对象的转换逻辑
    - 集成 `LLMFileSaver` 进行文件保存
    - 添加日志记录
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 3.2 编写 Base64ToFileConverter 单元测试
    - 测试成功转换场景
    - 测试 File 对象属性正确性
    - 测试文件保存器集成
    - 测试转换失败场景
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 3.3 编写 Base64ToFileConverter 属性测试
    - **Property 4: Base64 到 File 转换幂等性**
    - **Property 5: 文件存储一致性**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

- [ ] 4. Checkpoint - 验证核心组件功能
  - 确保所有核心组件测试通过，询问用户是否有问题

- [x] 5. LLMNode 集成
  - [x] 5.1 修改 LLMNode._run 方法
    - 根据 `input_mode` 选择文件获取逻辑
    - 集成 base64 文件获取流程
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [x] 5.2 实现 _fetch_base64_files 方法
    - 从变量池获取 base64 变量
    - 处理单个字符串和字符串数组
    - 调用转换器进行转换
    - 错误处理和日志记录
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 5.3 更新变量映射逻辑
    - 在 `_extract_variable_selector_to_variable_mapping` 中添加 base64 变量映射
    - _Requirements: 4.1_

  - [ ]* 5.4 编写 LLMNode base64 集成单元测试
    - 测试 base64 模式的文件获取
    - 测试文件变量模式的向后兼容
    - 测试两种模式的隔离性
    - 测试字符串数组处理
    - 测试错误处理流程
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 7.1, 7.2, 7.3_

  - [ ]* 5.5 编写 LLMNode 属性测试
    - **Property 6: 输入模式隔离性**
    - **Property 7: 文件列表合并正确性**
    - **Property 8: 错误日志完整性**
    - **Property 9: 向后兼容性保持**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 7.1, 7.2, 7.3**

- [x] 6. Checkpoint - 验证后端集成
  - 确保所有后端测试通过，询问用户是否有问题

- [ ]* 7. 集成测试
  - [ ]* 7.1 编写端到端集成测试
    - 测试完整的工作流执行（包含 base64 输入的 LLM 节点）
    - 测试多个 base64 图片的处理
    - 测试 base64 和文件变量混合使用
    - 测试错误场景的端到端流程
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3_

- [x] 8. 前端 UI 实现
  - [x] 8.1 修改视觉配置组件
    - 添加输入模式选择器（文件变量 / Base64 字符串）
    - 根据模式显示不同的变量选择器
    - 添加提示文案："请选择包含 base64 图片字符串的变量"
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 8.2 更新配置序列化逻辑
    - 序列化 `input_mode` 和 `base64_variable_selector`
    - 反序列化时设置默认值保证向后兼容
    - _Requirements: 6.4, 7.1, 7.2_

  - [ ]* 8.3 编写前端组件测试
    - 测试输入模式切换
    - 测试变量选择器显示和隐藏
    - 测试配置数据序列化和反序列化
    - 测试 UI 提示文案显示
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 9. 最终验证和文档
  - [x] 9.1 运行完整测试套件
    - 运行 `make lint` 和 `make type-check`
    - 运行所有单元测试
    - 运行前端测试
    - _Requirements: All_

  - [ ]* 9.2 更新文档
    - 更新 API 文档
    - 添加使用示例
    - 更新用户手册
    - _Requirements: All_

- [ ] 10. Final Checkpoint - 完成验证
  - 确保所有测试通过，询问用户是否准备好提交

## Notes

- 标记 `*` 的任务为可选任务，可以跳过以加快 MVP 开发
- 每个任务都引用了具体的需求编号以便追溯
- Checkpoint 任务确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边界情况
