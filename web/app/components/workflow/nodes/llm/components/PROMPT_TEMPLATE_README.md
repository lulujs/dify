# 提示词模板组件

## 概述

提示词模板组件允许用户从预设的模板中快速选择并应用到 LLM 节点的提示词配置中，大大提高了工作效率。

## 组件结构

### 1. PromptTemplateSelector (提示词模板选择器)
**文件**: `prompt-template-selector.tsx`

这是一个按钮组件，点击后会打开模板选择模态框。

**Props**:
- `className`: 可选的样式类名
- `onApplyTemplate`: 应用模板时的回调函数
- `nodeId`: 当前节点的 ID
- `isChatModel`: 是否为聊天模型

**使用示例**:
```tsx
<PromptTemplateSelector
  nodeId={nodeId}
  onApplyTemplate={(template) => {
    // 处理模板应用逻辑
  }}
  isChatModel={true}
/>
```

### 2. PromptTemplateModal (提示词模板模态框)
**文件**: `prompt-template-modal.tsx`

显示所有可用的提示词模板，用户可以选择并应用。

**Props**:
- `isShow`: 是否显示模态框
- `onClose`: 关闭模态框的回调
- `onApply`: 应用模板的回调
- `nodeId`: 当前节点的 ID
- `isChatModel`: 是否为聊天模型

**预设模板**:
1. Python Debugger - Python 调试助手
2. Translation - 多语言翻译
3. Meeting Takeaways - 会议总结
4. Writing Polisher - 写作润色
5. Professional Analyst - 专业分析师
6. Excel Formula Expert - Excel 公式专家
7. Travel Planning - 旅行规划
8. SQL Sorcerer - SQL 查询生成
9. Git Gud - Git 命令生成

## 集成方式

### 在 Editor 组件中集成

在 `editor.tsx` 中添加了 `isSupportPromptTemplate` 属性：

```tsx
<Editor
  isSupportPromptTemplate={true}
  onTemplateApplied={(prompt) => {
    // 处理模板应用
  }}
  // ... 其他属性
/>
```

### 在 ConfigPrompt 组件中集成

对于聊天模型，模板选择器显示在提示词列表的顶部：

```tsx
<PromptTemplateSelector
  nodeId={nodeId}
  onApplyTemplate={handleChatModeTemplateApplied}
  isChatModel={isChatModel}
/>
```

对于完成模型，通过 Editor 组件的 `isSupportPromptTemplate` 属性启用。

## 功能特性

### 1. 模板选择
- 网格布局展示所有可用模板
- 每个模板卡片显示图标、名称和描述
- 支持单选，选中的模板会高亮显示

### 2. 应用确认
- 应用模板前会弹出确认对话框
- 提醒用户当前配置将被覆盖
- 用户可以取消操作

### 3. 模型适配
- 自动根据模型类型（Chat/Completion）调整模板格式
- Chat 模型：生成带有 role 的消息数组
- Completion 模型：生成纯文本提示词

### 4. 国际化支持
- 支持中英文切换
- 模板名称和描述都已国际化
- 翻译文件位置：
  - 英文：`i18n/en-US/workflow.ts`
  - 中文：`i18n/zh-Hans/workflow.ts`

## 扩展模板

要添加新的模板，在 `prompt-template-modal.tsx` 中的 `templates` 数组添加新项：

```tsx
{
  key: 'yourTemplateKey',
  icon: YourIcon,
  name: t('appDebug.generate.template.yourTemplateKey.name'),
  description: t('appDebug.generate.template.yourTemplateKey.description'),
  prompt: isChatModel ? [
    {
      role: 'system',
      text: t('appDebug.generate.template.yourTemplateKey.prompt'),
    },
  ] : [
    {
      role: 'user',
      text: t('appDebug.generate.template.yourTemplateKey.prompt'),
    },
  ],
}
```

然后在翻译文件中添加对应的文本：

```typescript
// i18n/en-US/app-debug.ts
template: {
  yourTemplateKey: {
    name: 'Your Template Name',
    description: 'Your template description',
    prompt: 'Your prompt template content',
  },
}
```

## 样式说明

组件使用 Tailwind CSS 进行样式设计，主要特点：
- 响应式网格布局（2列）
- 悬停效果和过渡动画
- 选中状态的视觉反馈
- 与 Dify 设计系统保持一致

## 注意事项

1. **数据覆盖**: 应用模板会完全替换当前的提示词配置，请确保用户了解这一点
2. **模型兼容性**: 模板会根据模型类型自动调整格式
3. **翻译完整性**: 添加新模板时务必同步更新所有语言的翻译文件
4. **图标选择**: 为每个模板选择合适的图标以提升用户体验

## 未来改进方向

1. 支持用户自定义模板
2. 模板分类和搜索功能
3. 模板预览功能
4. 从云端同步模板
5. 模板版本管理
