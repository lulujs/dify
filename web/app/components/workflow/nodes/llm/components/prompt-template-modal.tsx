'use client'
import type { FC } from 'react'
import React, { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useBoolean } from 'ahooks'
import Modal from '@/app/components/base/modal'
import Button from '@/app/components/base/button'
import type { PromptItem } from '@/app/components/workflow/types'
import { PromptRole } from '@/app/components/workflow/types'
import cn from '@/utils/classnames'
import PromptEditor from '@/app/components/base/prompt-editor'
import Confirm from '@/app/components/base/confirm'
import Input from '@/app/components/base/input'

type TemplateItem = {
  key: string
  name: string
  model: string
  template: string
  prompt: PromptItem[]
}

type Props = {
  isShow: boolean
  onClose: () => void
  onApply: (template: PromptItem[]) => void
  isChatModel?: boolean
}

const PromptTemplateModal: FC<Props> = ({
  isShow,
  onClose,
  onApply,
  isChatModel,
}) => {
  const { t } = useTranslation()
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateItem | null>(null)
  const [previewTemplate, setPreviewTemplate] = useState<TemplateItem | null>(null)
  const [editedTemplate, setEditedTemplate] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(1)
  const [isShowConfirm, { setTrue: showConfirm, setFalse: hideConfirm }] = useBoolean(false)
  const [activeTab, setActiveTab] = useState<'mine' | 'workspace'>('mine')
  const [searchQuery, setSearchQuery] = useState('')
  const pageSize = 10

  // 我创建的模板列表
  const myTemplates: TemplateItem[] = [
    {
      key: 'myTemplate1',
      name: '产品需求文档生成器',
      model: 'GPT-4',
      template: '请根据以下信息生成产品需求文档（PRD）：\n\n产品名称：{{product_name}}\n目标用户：{{target_users}}\n核心功能：{{core_features}}\n业务目标：{{business_goals}}\n\n请包含以下章节：\n1. 产品概述\n2. 用户画像\n3. 功能需求\n4. 非功能需求\n5. 技术方案建议',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请根据以下信息生成产品需求文档（PRD）：\n\n产品名称：{{product_name}}\n目标用户：{{target_users}}\n核心功能：{{core_features}}\n业务目标：{{business_goals}}\n\n请包含以下章节：\n1. 产品概述\n2. 用户画像\n3. 功能需求\n4. 非功能需求\n5. 技术方案建议',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请根据以下信息生成产品需求文档（PRD）：\n\n产品名称：{{product_name}}\n目标用户：{{target_users}}\n核心功能：{{core_features}}\n业务目标：{{business_goals}}\n\n请包含以下章节：\n1. 产品概述\n2. 用户画像\n3. 功能需求\n4. 非功能需求\n5. 技术方案建议',
        },
      ],
    },
    {
      key: 'myTemplate2',
      name: '会议纪要整理',
      model: 'GPT-3.5',
      template: '请整理以下会议内容：\n\n会议主题：{{meeting_topic}}\n参会人员：{{attendees}}\n会议内容：{{meeting_content}}\n\n请按以下格式输出：\n1. 会议概要\n2. 讨论要点\n3. 决策事项\n4. 待办任务（负责人+截止时间）\n5. 下次会议安排',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请整理以下会议内容：\n\n会议主题：{{meeting_topic}}\n参会人员：{{attendees}}\n会议内容：{{meeting_content}}\n\n请按以下格式输出：\n1. 会议概要\n2. 讨论要点\n3. 决策事项\n4. 待办任务（负责人+截止时间）\n5. 下次会议安排',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请整理以下会议内容：\n\n会议主题：{{meeting_topic}}\n参会人员：{{attendees}}\n会议内容：{{meeting_content}}\n\n请按以下格式输出：\n1. 会议概要\n2. 讨论要点\n3. 决策事项\n4. 待办任务（负责人+截止时间）\n5. 下次会议安排',
        },
      ],
    },
    {
      key: 'myTemplate3',
      name: '技术方案评审',
      model: 'GPT-4',
      template: '请对以下技术方案进行评审：\n\n方案名称：{{solution_name}}\n技术栈：{{tech_stack}}\n方案描述：{{description}}\n\n请从以下维度进行评审：\n1. 技术可行性\n2. 性能和扩展性\n3. 安全性考虑\n4. 开发成本和周期\n5. 维护难度\n6. 改进建议',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请对以下技术方案进行评审：\n\n方案名称：{{solution_name}}\n技术栈：{{tech_stack}}\n方案描述：{{description}}\n\n请从以下维度进行评审：\n1. 技术可行性\n2. 性能和扩展性\n3. 安全性考虑\n4. 开发成本和周期\n5. 维护难度\n6. 改进建议',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请对以下技术方案进行评审：\n\n方案名称：{{solution_name}}\n技术栈：{{tech_stack}}\n方案描述：{{description}}\n\n请从以下维度进行评审：\n1. 技术可行性\n2. 性能和扩展性\n3. 安全性考虑\n4. 开发成本和周期\n5. 维护难度\n6. 改进建议',
        },
      ],
    },
  ]

  // 资源空间模板列表
  const workspaceTemplates: TemplateItem[] = [
    {
      key: 'customerService',
      name: '客户服务助手',
      model: 'GPT-4',
      template: '你是一位专业的客户服务代表。请根据客户的问题 {{question}} 提供帮助。\n\n要求：\n1. 保持友好和专业的态度\n2. 快速准确地理解客户需求\n3. 提供清晰的解决方案\n4. 如遇复杂问题，及时升级处理',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '你是一位专业的客户服务代表。请根据客户的问题 {{question}} 提供帮助。\n\n要求：\n1. 保持友好和专业的态度\n2. 快速准确地理解客户需求\n3. 提供清晰的解决方案\n4. 如遇复杂问题，及时升级处理',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '你是一位专业的客户服务代表。请根据客户的问题 {{question}} 提供帮助。\n\n要求：\n1. 保持友好和专业的态度\n2. 快速准确地理解客户需求\n3. 提供清晰的解决方案\n4. 如遇复杂问题，及时升级处理',
        },
      ],
    },
    {
      key: 'contentSummarizer',
      name: '内容摘要生成器',
      model: 'GPT-3.5',
      template: '请对以下内容进行摘要：\n\n{{content}}\n\n要求：\n1. 提取核心观点和关键信息\n2. 保持客观中立\n3. 字数控制在 {{max_words}} 字以内\n4. 使用简洁清晰的语言',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请对以下内容进行摘要：\n\n{{content}}\n\n要求：\n1. 提取核心观点和关键信息\n2. 保持客观中立\n3. 字数控制在 {{max_words}} 字以内\n4. 使用简洁清晰的语言',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请对以下内容进行摘要：\n\n{{content}}\n\n要求：\n1. 提取核心观点和关键信息\n2. 保持客观中立\n3. 字数控制在 {{max_words}} 字以内\n4. 使用简洁清晰的语言',
        },
      ],
    },
    {
      key: 'codeReviewer',
      name: '代码审查助手',
      model: 'GPT-4',
      template: '请审查以下 {{language}} 代码：\n\n```{{language}}\n{{code}}\n```\n\n请从以下方面进行审查：\n1. 代码质量和可读性\n2. 潜在的 bug 和安全问题\n3. 性能优化建议\n4. 最佳实践建议',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请审查以下 {{language}} 代码：\n\n```{{language}}\n{{code}}\n```\n\n请从以下方面进行审查：\n1. 代码质量和可读性\n2. 潜在的 bug 和安全问题\n3. 性能优化建议\n4. 最佳实践建议',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请审查以下 {{language}} 代码：\n\n```{{language}}\n{{code}}\n```\n\n请从以下方面进行审查：\n1. 代码质量和可读性\n2. 潜在的 bug 和安全问题\n3. 性能优化建议\n4. 最佳实践建议',
        },
      ],
    },
    {
      key: 'emailWriter',
      name: '邮件撰写助手',
      model: 'GPT-3.5',
      template: '请帮我撰写一封邮件：\n\n收件人：{{recipient}}\n主题：{{subject}}\n目的：{{purpose}}\n\n要求：\n1. 语气：{{tone}}\n2. 保持专业和礼貌\n3. 结构清晰，重点突出\n4. 包含适当的开头和结尾',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请帮我撰写一封邮件：\n\n收件人：{{recipient}}\n主题：{{subject}}\n目的：{{purpose}}\n\n要求：\n1. 语气：{{tone}}\n2. 保持专业和礼貌\n3. 结构清晰，重点突出\n4. 包含适当的开头和结尾',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请帮我撰写一封邮件：\n\n收件人：{{recipient}}\n主题：{{subject}}\n目的：{{purpose}}\n\n要求：\n1. 语气：{{tone}}\n2. 保持专业和礼貌\n3. 结构清晰，重点突出\n4. 包含适当的开头和结尾',
        },
      ],
    },
    {
      key: 'dataAnalyst',
      name: '数据分析助手',
      model: 'GPT-4',
      template: '请分析以下数据：\n\n{{data}}\n\n分析维度：\n1. 数据趋势和模式\n2. 异常值识别\n3. 关键指标：{{metrics}}\n4. 提供 {{insights_count}} 条洞察和建议',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请分析以下数据：\n\n{{data}}\n\n分析维度：\n1. 数据趋势和模式\n2. 异常值识别\n3. 关键指标：{{metrics}}\n4. 提供 {{insights_count}} 条洞察和建议',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请分析以下数据：\n\n{{data}}\n\n分析维度：\n1. 数据趋势和模式\n2. 异常值识别\n3. 关键指标：{{metrics}}\n4. 提供 {{insights_count}} 条洞察和建议',
        },
      ],
    },
    {
      key: 'productDescriptor',
      name: '产品描述生成器',
      model: 'GPT-3.5',
      template: '请为以下产品撰写描述：\n\n产品名称：{{product_name}}\n产品类别：{{category}}\n核心特点：{{features}}\n目标用户：{{target_audience}}\n\n要求：\n1. 突出产品优势\n2. 语言生动有吸引力\n3. 字数：{{word_count}} 字左右',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请为以下产品撰写描述：\n\n产品名称：{{product_name}}\n产品类别：{{category}}\n核心特点：{{features}}\n目标用户：{{target_audience}}\n\n要求：\n1. 突出产品优势\n2. 语言生动有吸引力\n3. 字数：{{word_count}} 字左右',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请为以下产品撰写描述：\n\n产品名称：{{product_name}}\n产品类别：{{category}}\n核心特点：{{features}}\n目标用户：{{target_audience}}\n\n要求：\n1. 突出产品优势\n2. 语言生动有吸引力\n3. 字数：{{word_count}} 字左右',
        },
      ],
    },
    {
      key: 'interviewPrep',
      name: '面试准备助手',
      model: 'GPT-4',
      template: '请帮我准备面试：\n\n职位：{{position}}\n公司：{{company}}\n面试类型：{{interview_type}}\n\n请提供：\n1. 可能的面试问题（{{question_count}} 个）\n2. 针对我的背景 {{background}} 的回答建议\n3. 需要准备的技术点\n4. 面试注意事项',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请帮我准备面试：\n\n职位：{{position}}\n公司：{{company}}\n面试类型：{{interview_type}}\n\n请提供：\n1. 可能的面试问题（{{question_count}} 个）\n2. 针对我的背景 {{background}} 的回答建议\n3. 需要准备的技术点\n4. 面试注意事项',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请帮我准备面试：\n\n职位：{{position}}\n公司：{{company}}\n面试类型：{{interview_type}}\n\n请提供：\n1. 可能的面试问题（{{question_count}} 个）\n2. 针对我的背景 {{background}} 的回答建议\n3. 需要准备的技术点\n4. 面试注意事项',
        },
      ],
    },
    {
      key: 'socialMediaPost',
      name: '社交媒体文案',
      model: 'GPT-3.5',
      template: '请为 {{platform}} 平台创作一条社交媒体文案：\n\n主题：{{topic}}\n目标：{{goal}}\n风格：{{style}}\n\n要求：\n1. 符合平台特点\n2. 包含 {{hashtag_count}} 个相关话题标签\n3. 吸引用户互动\n4. 字数限制：{{char_limit}} 字符',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请为 {{platform}} 平台创作一条社交媒体文案：\n\n主题：{{topic}}\n目标：{{goal}}\n风格：{{style}}\n\n要求：\n1. 符合平台特点\n2. 包含 {{hashtag_count}} 个相关话题标签\n3. 吸引用户互动\n4. 字数限制：{{char_limit}} 字符',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请为 {{platform}} 平台创作一条社交媒体文案：\n\n主题：{{topic}}\n目标：{{goal}}\n风格：{{style}}\n\n要求：\n1. 符合平台特点\n2. 包含 {{hashtag_count}} 个相关话题标签\n3. 吸引用户互动\n4. 字数限制：{{char_limit}} 字符',
        },
      ],
    },
    {
      key: 'bugReporter',
      name: 'Bug 报告生成器',
      model: 'GPT-4',
      template: '请根据以下信息生成 Bug 报告：\n\n问题描述：{{issue_description}}\n复现步骤：{{steps}}\n预期结果：{{expected}}\n实际结果：{{actual}}\n环境信息：{{environment}}\n\n请生成规范的 Bug 报告，包括：\n1. 标题\n2. 严重程度评估\n3. 详细描述\n4. 可能的原因分析',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请根据以下信息生成 Bug 报告：\n\n问题描述：{{issue_description}}\n复现步骤：{{steps}}\n预期结果：{{expected}}\n实际结果：{{actual}}\n环境信息：{{environment}}\n\n请生成规范的 Bug 报告，包括：\n1. 标题\n2. 严重程度评估\n3. 详细描述\n4. 可能的原因分析',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请根据以下信息生成 Bug 报告：\n\n问题描述：{{issue_description}}\n复现步骤：{{steps}}\n预期结果：{{expected}}\n实际结果：{{actual}}\n环境信息：{{environment}}\n\n请生成规范的 Bug 报告，包括：\n1. 标题\n2. 严重程度评估\n3. 详细描述\n4. 可能的原因分析',
        },
      ],
    },
    {
      key: 'learningPlan',
      name: '学习计划制定',
      model: 'GPT-4',
      template: '请帮我制定学习计划：\n\n学习目标：{{goal}}\n当前水平：{{current_level}}\n可用时间：{{available_time}}\n学习期限：{{deadline}}\n\n请提供：\n1. 分阶段学习路线\n2. 每个阶段的学习资源推荐\n3. 时间分配建议\n4. 学习效果评估方法',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请帮我制定学习计划：\n\n学习目标：{{goal}}\n当前水平：{{current_level}}\n可用时间：{{available_time}}\n学习期限：{{deadline}}\n\n请提供：\n1. 分阶段学习路线\n2. 每个阶段的学习资源推荐\n3. 时间分配建议\n4. 学习效果评估方法',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请帮我制定学习计划：\n\n学习目标：{{goal}}\n当前水平：{{current_level}}\n可用时间：{{available_time}}\n学习期限：{{deadline}}\n\n请提供：\n1. 分阶段学习路线\n2. 每个阶段的学习资源推荐\n3. 时间分配建议\n4. 学习效果评估方法',
        },
      ],
    },
    {
      key: 'apiDocGenerator',
      name: 'API 文档生成器',
      model: 'GPT-3.5',
      template: '请为以下 API 生成文档：\n\n接口名称：{{api_name}}\n请求方法：{{method}}\n请求路径：{{path}}\n请求参数：{{params}}\n响应格式：{{response}}\n\n请生成包含以下内容的文档：\n1. 接口描述\n2. 请求示例\n3. 响应示例\n4. 错误码说明\n5. 注意事项',
      prompt: isChatModel ? [
        {
          role: PromptRole.system,
          text: '请为以下 API 生成文档：\n\n接口名称：{{api_name}}\n请求方法：{{method}}\n请求路径：{{path}}\n请求参数：{{params}}\n响应格式：{{response}}\n\n请生成包含以下内容的文档：\n1. 接口描述\n2. 请求示例\n3. 响应示例\n4. 错误码说明\n5. 注意事项',
        },
      ] : [
        {
          role: PromptRole.user,
          text: '请为以下 API 生成文档：\n\n接口名称：{{api_name}}\n请求方法：{{method}}\n请求路径：{{path}}\n请求参数：{{params}}\n响应格式：{{response}}\n\n请生成包含以下内容的文档：\n1. 接口描述\n2. 请求示例\n3. 响应示例\n4. 错误码说明\n5. 注意事项',
        },
      ],
    },
  ]

  // 过滤和搜索逻辑
  const filteredTemplates = useMemo(() => {
    // 根据标签页选择模板列表
    let result = activeTab === 'mine' ? myTemplates : workspaceTemplates

    // 根据搜索关键词过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase()
      result = result.filter(template =>
        template.name.toLowerCase().includes(query)
        || template.template.toLowerCase().includes(query),
      )
    }

    return result
  }, [myTemplates, workspaceTemplates, activeTab, searchQuery])

  const totalPages = Math.ceil(filteredTemplates.length / pageSize)
  const paginatedTemplates = filteredTemplates.slice((currentPage - 1) * pageSize, currentPage * pageSize)

  const handleSelectTemplate = useCallback((template: TemplateItem) => {
    setSelectedTemplate(template)
    setPreviewTemplate(template)
    setEditedTemplate(template.template)
  }, [])

  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value)
    setCurrentPage(1)
  }, [])

  const handleTemplateChange = useCallback((value: string) => {
    setEditedTemplate(value)
  }, [])

  const handleConfirmApply = useCallback(() => {
    if (selectedTemplate)
      showConfirm()
  }, [selectedTemplate, showConfirm])

  const handleApply = useCallback(() => {
    if (selectedTemplate) {
      // 使用编辑后的模板内容
      const updatedPrompt = selectedTemplate.prompt.map(item => ({
        ...item,
        text: editedTemplate,
      }))
      onApply(updatedPrompt)
      hideConfirm()
    }
  }, [selectedTemplate, editedTemplate, onApply, hideConfirm])

  return (
    <>
      <Modal
        isShow={isShow}
        onClose={onClose}
        className='!max-w-[1200px] !p-0'
      >
        <div className='flex h-[700px] flex-col'>
          {/* Header */}
          <div className='border-b border-divider-regular px-6 py-4'>
            <div className='text-lg font-semibold text-text-primary'>
              {t('workflow.nodes.llm.promptTemplate.title')}
            </div>
            <div className='mt-1 text-sm text-text-tertiary'>
              {t('workflow.nodes.llm.promptTemplate.description')}
            </div>
          </div>

          {/* Main Content */}
          <div className='flex flex-1 overflow-hidden'>
            {/* Left: Template List */}
            <div className='w-[600px] border-r border-divider-regular'>
              <div className='flex h-full flex-col'>
                {/* Tabs and Search */}
                <div className='border-b border-divider-regular px-4 py-3'>
                  <div className='flex items-center justify-between'>
                    {/* Tabs */}
                    <div className='flex items-center space-x-1 rounded-lg bg-background-section p-0.5'>
                      <button
                        className={cn(
                          'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                          activeTab === 'mine'
                            ? 'bg-primary-600 text-white shadow-xs'
                            : 'text-text-tertiary hover:text-text-secondary',
                        )}
                        onClick={() => {
                          setActiveTab('mine')
                          setCurrentPage(1)
                        }}
                      >
                        {t('workflow.nodes.llm.promptTemplate.mine')}
                      </button>
                      <button
                        className={cn(
                          'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
                          activeTab === 'workspace'
                            ? 'bg-primary-600 text-white shadow-xs'
                            : 'text-text-tertiary hover:text-text-secondary',
                        )}
                        onClick={() => {
                          setActiveTab('workspace')
                          setCurrentPage(1)
                        }}
                      >
                        {t('workflow.nodes.llm.promptTemplate.workspace')}
                      </button>
                    </div>

                    {/* Search */}
                    <div className='w-64'>
                      <Input
                        value={searchQuery}
                        onChange={e => handleSearchChange(e.target.value)}
                        placeholder={t('workflow.nodes.llm.promptTemplate.searchPlaceholder')}
                        showLeftIcon
                      />
                    </div>
                  </div>
                </div>

                {/* Table Header */}
                <div className='grid grid-cols-12 gap-2 border-b border-divider-regular bg-background-section px-4 py-3 text-xs font-semibold text-text-tertiary'>
                  <div className='col-span-5'>{t('workflow.nodes.llm.promptTemplate.promptName')}</div>
                  <div className='col-span-7'>{t('workflow.nodes.llm.promptTemplate.template')}</div>
                </div>

                {/* Table Body */}
                <div className='flex-1 overflow-y-auto'>
                  {paginatedTemplates.length > 0 ? (
                    paginatedTemplates.map((template) => {
                      const isSelected = selectedTemplate?.key === template.key
                      return (
                        <div
                          key={template.key}
                          className={cn(
                            'grid cursor-pointer grid-cols-12 gap-2 border-b border-divider-subtle px-4 py-3 text-sm transition-colors hover:bg-background-default-hover',
                            isSelected && 'bg-components-button-primary-bg/5',
                          )}
                          onClick={() => handleSelectTemplate(template)}
                        >
                          <div className='col-span-5 truncate font-medium text-text-primary'>
                            {template.name}
                          </div>
                          <div className='col-span-7 truncate text-text-secondary'>
                            {template.template}
                          </div>
                        </div>
                      )
                    })
                  ) : (
                    <div className='flex h-full items-center justify-center'>
                      <div className='text-center'>
                        <div className='text-sm text-text-tertiary'>
                          {activeTab === 'mine'
                            ? t('workflow.nodes.llm.promptTemplate.noMyTemplates')
                            : t('workflow.nodes.llm.promptTemplate.noResults')}
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Pagination */}
                <div className='flex items-center justify-between border-t border-divider-regular px-4 py-3 text-sm text-text-tertiary'>
                  <div>
                    {t('workflow.nodes.llm.promptTemplate.pagination', {
                      current: currentPage,
                      total: filteredTemplates.length,
                      pageSize,
                    })}
                  </div>
                  <div className='flex items-center space-x-2'>
                    <Button
                      size='small'
                      variant='ghost'
                      disabled={currentPage === 1}
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    >
                      {t('workflow.nodes.llm.promptTemplate.previousPage')}
                    </Button>
                    <Button
                      size='small'
                      variant='ghost'
                      disabled={currentPage === totalPages}
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    >
                      {t('workflow.nodes.llm.promptTemplate.nextPage')}
                    </Button>
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Edit Area */}
            <div className='flex flex-1 flex-col p-6'>
              <div className='mb-4'>
                <div className='text-sm font-semibold text-text-secondary'>
                  {t('workflow.nodes.llm.promptTemplate.editArea')}
                </div>
              </div>
              <div className='flex-1 overflow-hidden'>
                <div className='relative h-full'>
                  <PromptEditor
                    key={previewTemplate?.key || 'empty'}
                    wrapperClassName='h-full border !border-components-input-bg-normal bg-components-input-bg-normal hover:!border-components-input-bg-hover rounded-[10px]'
                    className='h-full min-h-[400px] px-4 py-3'
                    instanceId='prompt-template-editor'
                    value={editedTemplate}
                    placeholder={
                      <div className='system-sm-regular text-text-placeholder'>
                        {t('workflow.nodes.llm.promptTemplate.editPlaceholder')}
                      </div>
                    }
                    onChange={handleTemplateChange}
                    editable={true}
                    contextBlock={{
                      show: false,
                      selectable: false,
                    }}
                    variableBlock={{
                      show: false,
                    }}
                    externalToolBlock={{
                      show: false,
                    }}
                    historyBlock={{
                      show: false,
                      selectable: false,
                    }}
                    queryBlock={{
                      show: false,
                      selectable: false,
                    }}
                    workflowVariableBlock={{
                      show: false,
                    }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className='flex items-center justify-end space-x-2 border-t border-divider-regular px-6 py-4'>
            <Button onClick={onClose}>
              {t('common.operation.cancel')}
            </Button>
            <Button
              variant='primary'
              onClick={handleConfirmApply}
              disabled={!selectedTemplate}
            >
              {t('common.operation.confirm')}
            </Button>
          </div>
        </div>
      </Modal>

      {isShowConfirm && (
        <Confirm
          title={t('workflow.nodes.llm.promptTemplate.confirmTitle')}
          content={t('workflow.nodes.llm.promptTemplate.confirmMessage')}
          isShow
          onConfirm={handleApply}
          onCancel={hideConfirm}
        />
      )}
    </>
  )
}

export default React.memo(PromptTemplateModal)
