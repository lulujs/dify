# 提示词模板组件使用示例

## 基础使用

### 1. 在 LLM 节点中使用

提示词模板选择器已经集成到 LLM 节点的配置面板中，用户可以直接使用：

#### Chat 模型
对于 Chat 模型，模板选择器按钮显示在消息列表的顶部：

```
┌─────────────────────────────────────┐
│ 提示词              [模板图标按钮]  │
├─────────────────────────────────────┤
│ System Message                      │
│ ┌─────────────────────────────────┐ │
│ │ You are a helpful assistant...  │ │
│ └─────────────────────────────────┘ │
│                                     │
│ User Message                        │
│ ┌─────────────────────────────────┐ │
│ │ {{input}}                       │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

#### Completion 模型
对于 Completion 模型，模板选择器按钮显示在编辑器的工具栏中：

```
┌─────────────────────────────────────┐
│ Prompt  [生成器] [模板] [变量] ... │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ Your prompt here...             │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

## 用户操作流程

### 步骤 1: 打开模板选择器
点击模板图标按钮（网格图标），打开模板选择模态框。

### 步骤 2: 浏览模板
在模态框中浏览所有可用的预设模板：

```
┌──────────────────────────────────────────────────────┐
│ 提示词模板                                    [X]    │
│ 从预设的提示词模板中选择，快速配置您的 LLM 节点。   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ [图标]       │  │ [图标]       │                │
│  │ Python调试器 │  │ 翻译助手     │                │
│  │ 生成和调试... │  │ 多语言翻译... │                │
│  └──────────────┘  └──────────────┘                │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐                │
│  │ [图标]       │  │ [图标]       │                │
│  │ 会议总结     │  │ 写作润色     │                │
│  │ 提炼会议要点 │  │ 改进写作质量 │                │
│  └──────────────┘  └──────────────┘                │
│                                                      │
├──────────────────────────────────────────────────────┤
│                          [取消]  [应用]             │
└──────────────────────────────────────────────────────┘
```

### 步骤 3: 选择模板
点击任意模板卡片进行选择，选中的模板会显示蓝色边框和勾选标记。

### 步骤 4: 应用模板
点击"应用"按钮，系统会弹出确认对话框：

```
┌──────────────────────────────────┐
│ 应用模板？                       │
├──────────────────────────────────┤
│ 应用此模板将替换您当前的提示词   │
│ 配置。                           │
├──────────────────────────────────┤
│              [取消]  [确认]      │
└──────────────────────────────────┘
```

### 步骤 5: 确认应用
点击"确认"后，模板内容会自动填充到提示词编辑器中。

## 模板示例

### Python Debugger 模板

**适用场景**: 代码调试和生成

**Chat 模型输出**:
```json
[
  {
    "role": "system",
    "text": "You are an expert Python programmer and debugger. Help users understand, debug, and optimize their Python code. Provide clear explanations and suggest best practices."
  }
]
```

**Completion 模型输出**:
```
You are an expert Python programmer and debugger. Help users understand, debug, and optimize their Python code. Provide clear explanations and suggest best practices.
```

### Translation 模板

**适用场景**: 多语言翻译

**Chat 模型输出**:
```json
[
  {
    "role": "system",
    "text": "You are a professional translator. Translate the user's input accurately while maintaining the original tone and context. Support multiple languages including English, Chinese, Spanish, French, German, Japanese, and Korean."
  }
]
```

### Meeting Takeaways 模板

**适用场景**: 会议记录总结

**Chat 模型输出**:
```json
[
  {
    "role": "system",
    "text": "You are a meeting summarization expert. Extract key discussion points, decisions made, and action items from meeting transcripts. Present the information in a clear, structured format."
  }
]
```

## 自定义模板示例

如果您想添加自己的模板，可以参考以下代码：

```typescript
// 在 prompt-template-modal.tsx 中添加
{
  key: 'customerService',
  icon: RiCustomerServiceLine,
  name: '客户服务助手',
  description: '专业的客户服务对话助手，提供友好和高效的支持',
  prompt: isChatModel ? [
    {
      role: 'system',
      text: `You are a professional customer service representative. 
Your goal is to:
1. Understand customer issues quickly and accurately
2. Provide clear and helpful solutions
3. Maintain a friendly and professional tone
4. Escalate complex issues when necessary

Always be patient, empathetic, and solution-oriented.`,
    },
  ] : [
    {
      role: 'user',
      text: `You are a professional customer service representative. 
Your goal is to:
1. Understand customer issues quickly and accurately
2. Provide clear and helpful solutions
3. Maintain a friendly and professional tone
4. Escalate complex issues when necessary

Always be patient, empathetic, and solution-oriented.`,
    },
  ],
}
```

## 最佳实践

### 1. 选择合适的模板
- 根据您的具体需求选择最接近的模板
- 应用后可以进一步编辑和优化

### 2. 模板作为起点
- 模板提供了良好的基础结构
- 建议根据实际场景进行调整
- 添加特定的变量和上下文

### 3. 测试和迭代
- 应用模板后进行测试
- 根据输出结果调整提示词
- 使用提示词生成器进一步优化

### 4. 保存自定义版本
- 如果经常使用某个修改后的模板
- 考虑将其保存为工作流模板
- 方便团队成员复用

## 常见问题

### Q: 应用模板会覆盖我的现有配置吗？
A: 是的，应用模板会完全替换当前的提示词配置。系统会在应用前弹出确认对话框提醒您。

### Q: 可以同时使用多个模板吗？
A: 不可以直接使用多个模板，但您可以：
1. 先应用一个模板
2. 手动复制其他模板的内容
3. 合并到当前配置中

### Q: 模板支持变量吗？
A: 模板本身是静态文本，但应用后您可以：
1. 手动添加变量（如 {{input}}）
2. 使用提示词生成器自动提取变量

### Q: 如何添加新的模板？
A: 请参考 PROMPT_TEMPLATE_README.md 中的"扩展模板"部分。

### Q: 模板在不同语言下会变化吗？
A: 是的，模板内容会根据系统语言自动切换，但建议使用英文提示词以获得更好的模型性能。
