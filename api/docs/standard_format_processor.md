# StandardFormatProcessor 使用说明

## 概述

`StandardFormatProcessor` 是一个响应增强处理器，用于将API响应转换为标准化格式。它支持阻塞模式和流式输出两种响应类型。

## 功能特性

### 1. 阻塞模式响应格式化

对于阻塞模式的响应，处理器会将原始响应转换为以下格式：

```json
{
  "returnCode": "SUC0000",  // HTTP 200时为"SUC0000"，其他状态为"FAIL000"
  "errorMsg": null,
  "body": {                 // 包含原始响应数据
    "workflow_run_id": "wr_123456",
    "status": "succeeded",
    "data": { ... }
  }
}
```

### 2. 流式响应格式化

对于流式输出，处理器会生成以下格式的数据块：

**数据块格式：**
```json
{
  "returnCode": "SUC0000",  // HTTP 200时为"SUC0000"，其他状态为"FAIL000"
  "errorMsg": null,
  "data": { ... },         // 包含原始数据块内容
  "type": "DATA"
}
```

**结束块格式：**
```json
{
  "returnCode": "SUC0000",
  "errorMsg": null,
  "data": null,            // 结束时为null
  "type": "DONE"
}
```

## 使用方法

### 1. 注册处理器

```python
from core.response_enhancement import get_registry, StandardFormatProcessor

# 获取处理器注册表
registry = get_registry()

# 注册标准格式处理器
registry.register("standard_format", StandardFormatProcessor())
```

### 2. 应用到API端点

```python
from core.response_enhancement import response_enhancer

@response_enhancer(processors=['standard_format'])
def your_api_method(self, app_model: App, end_user: EndUser):
    # 你的业务逻辑
    return {"message": "Hello, world!"}
```

### 3. 配置文件设置

在 `response_enhancement.yaml` 配置文件中：

```yaml
global:
  enabled: true
  default_processors: ['standard_format']

endpoints:
  - pattern: "/completion-messages"
    processors: ['standard_format']
    enabled: true
    
  - pattern: "/chat-messages"
    processors: ['standard_format']
    enabled: true
```

## 支持的响应类型

- **字典响应** (`dict`): 直接处理Python字典对象，原始数据保存在 `body` 字段中
- **Flask响应** (`Response`): 处理Flask Response对象，解析JSON内容并保存在 `body` 字段中，保持原有状态码和头部
- **流式响应** (`Generator`): 处理生成器对象，支持SSE格式，原始数据块保存在 `data` 字段中

## 状态码处理

- **HTTP 200**: `returnCode` 设置为 `"SUC0000"`
- **其他状态码**: `returnCode` 设置为 `"FAIL000"`

## 错误处理

处理器包含完善的错误处理机制：

1. **流式响应错误**: 如果流式处理过程中出现异常，会自动发送错误块
2. **类型检查**: 只处理支持的响应类型，其他类型会被跳过
3. **优雅降级**: 处理失败时返回原始响应，不影响业务功能

## 示例代码

查看 `api/examples/standard_format_demo.py` 文件获取完整的使用示例。

运行演示：
```bash
cd api
uv run python examples/standard_format_demo.py
```

## 测试

运行处理器测试：
```bash
uv run --project api pytest -v api/tests/unit_tests/core/response_enhancement/processors/test_standard_format.py
```

## 注意事项

1. 处理器会将原始响应内容包装在标准化格式中：
   - 字典和Flask JSON响应：原始数据保存在 `body` 字段
   - 流式响应：原始数据块保存在 `data` 字段（DONE类型的data为null）
2. 原始响应的HTTP状态码和头部信息会被保留
3. 流式响应会自动添加DONE类型的结束块
4. 如果Flask Response的JSON解析失败，会使用空的 `body` 对象作为后备方案