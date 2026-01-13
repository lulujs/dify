'use client'
import type { FC } from 'react'
import React, { useCallback, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { produce } from 'immer'
import { RiArrowDownSLine, RiArrowRightSLine, RiDeleteBinLine } from '@remixicon/react'
import type { InputVarChild } from '../../../../types'
import { InputVarType } from '../../../../types'
import Input from '@/app/components/base/input'
import Textarea from '@/app/components/base/textarea'
import cn from '@/utils/classnames'
import BoolInput from './bool-input'
import CodeEditor from '../editor/code-editor'
import { CodeLanguage } from '../../../code/types'

type InputMode = 'form' | 'json'

type Props = {
  /** Variable definition with children */
  definition: InputVarChild[]
  /** Current value (object) */
  value: Record<string, unknown>
  /** Callback when value changes */
  onChange: (value: Record<string, unknown>) => void
  /** Current nesting depth */
  depth?: number
  /** Whether the input is disabled */
  disabled?: boolean
  /** Class name for the container */
  className?: string
}

/**
 * NestedObjectInput - A component for inputting nested object values
 *
 * This component renders a form based on InputVarChild[] definition,
 * allowing users to input values for nested object structures.
 *
 * @see Requirements 4.1, 4.2 - Variable selector nested path support
 */
const NestedObjectInput: FC<Props> = ({
  definition,
  value,
  onChange,
  depth = 0,
  disabled = false,
  className,
}) => {
  const { t } = useTranslation()
  const [expandedFields, setExpandedFields] = React.useState<Set<string>>(new Set())
  const [inputModes, setInputModes] = useState<Record<string, InputMode>>({})

  const toggleExpand = useCallback((fieldName: string) => {
    setExpandedFields((prev) => {
      const next = new Set(prev)
      if (next.has(fieldName))
        next.delete(fieldName)
      else
        next.add(fieldName)
      return next
    })
  }, [])

  const setInputMode = useCallback((fieldName: string, mode: InputMode) => {
    setInputModes(prev => ({ ...prev, [fieldName]: mode }))
  }, [])

  const getInputMode = useCallback((fieldName: string): InputMode => {
    return inputModes[fieldName] || 'form'
  }, [inputModes])

  const handleFieldChange = useCallback((fieldName: string, fieldValue: unknown) => {
    const newValue = produce(value || {}, (draft) => {
      draft[fieldName] = fieldValue
    })
    onChange(newValue)
  }, [value, onChange])

  // Handle JSON input change with validation
  const handleJsonChange = useCallback((fieldName: string, jsonValue: string) => {
    try {
      const parsed = JSON.parse(jsonValue)
      handleFieldChange(fieldName, parsed)
    }
    catch {
      // Keep the raw string if not valid JSON - will be validated on submit
      handleFieldChange(fieldName, jsonValue)
    }
  }, [handleFieldChange])

  // Get JSON string representation of value
  const getJsonValue = useCallback((fieldValue: unknown): string => {
    if (typeof fieldValue === 'string')
      return fieldValue
    if (fieldValue === undefined || fieldValue === null)
      return ''
    return JSON.stringify(fieldValue, null, 2)
  }, [])

  // Handle array item changes
  const handleArrayItemChange = useCallback((fieldName: string, index: number) => {
    return (newValue: any) => {
      const currentValue = value?.[fieldName]
      const currentArray = Array.isArray(currentValue) ? currentValue : []
      const newArray = produce(currentArray, (draft: any) => {
        draft[index] = newValue
      })
      handleFieldChange(fieldName, newArray)
    }
  }, [value, handleFieldChange])

  const handleArrayItemRemove = useCallback((fieldName: string, index: number) => {
    return () => {
      const currentValue = value?.[fieldName]
      const currentArray = Array.isArray(currentValue) ? currentValue : []
      const newArray = currentArray.filter((_, i) => i !== index)
      handleFieldChange(fieldName, newArray)
    }
  }, [value, handleFieldChange])

  const renderField = useCallback((child: InputVarChild) => {
    const fieldValue = value?.[child.variable]
    const isExpanded = expandedFields.has(child.variable)
    const hasChildren = child.children && child.children.length > 0
    const isObjectType = child.type === InputVarType.object
    const isArrayString = child.type === InputVarType.arrayString
    const isArrayNumber = child.type === InputVarType.arrayNumber
    const isArrayBoolean = child.type === InputVarType.arrayBoolean
    const isArrayObject = child.type === InputVarType.arrayObject
    const isArrayType = isArrayString || isArrayNumber || isArrayBoolean || isArrayObject
    const isComplexType = isObjectType || isArrayType
    const inputMode = getInputMode(child.variable)
    const jsonValue = getJsonValue(fieldValue)

    return (
      <div key={child.variable} className={cn('mb-2 last:mb-0', depth > 0 && 'ml-4')}>
        {/* Field label */}
        <div className='mb-1 flex items-center justify-between'>
          <div className='flex items-center gap-1'>
            {(hasChildren || isArrayType) && (
              <button
                type='button'
                onClick={() => toggleExpand(child.variable)}
                className='flex h-4 w-4 items-center justify-center rounded hover:bg-state-base-hover'
              >
                {isExpanded
                  ? <RiArrowDownSLine className='h-3 w-3 text-text-tertiary' />
                  : <RiArrowRightSLine className='h-3 w-3 text-text-tertiary' />
                }
              </button>
            )}
            <span className='system-sm-semibold text-text-secondary'>
              {child.variable}
            </span>
            {!child.required && (
              <span className='system-xs-regular text-text-tertiary'>
                {t('workflow.panel.optional')}
              </span>
            )}
            <span className='system-xs-regular text-text-tertiary'>
              ({getTypeLabel(child.type)})
            </span>
          </div>

          {/* Mode switcher for complex types */}
          {isComplexType && (
            <div className='flex shrink-0 items-center gap-1'>
              <button
                type='button'
                onClick={() => setInputMode(child.variable, 'form')}
                className={cn(
                  'system-xs-medium rounded-md px-2 py-1 transition-colors',
                  inputMode === 'form'
                    ? 'bg-components-button-primary-bg text-components-button-primary-text'
                    : 'text-text-tertiary hover:text-text-secondary',
                )}
              >
                {t('workflow.panel.form')}
              </button>
              <button
                type='button'
                onClick={() => setInputMode(child.variable, 'json')}
                className={cn(
                  'system-xs-medium rounded-md px-2 py-1 transition-colors',
                  inputMode === 'json'
                    ? 'bg-components-button-primary-bg text-components-button-primary-text'
                    : 'text-text-tertiary hover:text-text-secondary',
                )}
              >
                JSON
              </button>
            </div>
          )}
        </div>

        {/* Field description */}
        {child.description && (
          <div className='mb-1 text-xs text-text-tertiary'>
            {child.description}
          </div>
        )}

        {/* Field input */}
        <div className='grow'>
          {child.type === InputVarType.textInput && (
            <Input
              value={(fieldValue as string) || ''}
              onChange={e => handleFieldChange(child.variable, e.target.value)}
              placeholder={child.variable}
              disabled={disabled}
            />
          )}

          {child.type === InputVarType.paragraph && (
            <Textarea
              value={(fieldValue as string) || ''}
              onChange={e => handleFieldChange(child.variable, e.target.value)}
              placeholder={child.variable}
              disabled={disabled}
            />
          )}

          {child.type === InputVarType.number && (
            <Input
              type='number'
              value={(fieldValue as number) ?? ''}
              onChange={e => handleFieldChange(child.variable, e.target.value ? Number(e.target.value) : undefined)}
              placeholder={child.variable}
              disabled={disabled}
            />
          )}

          {child.type === InputVarType.checkbox && (
            <BoolInput
              name={child.variable}
              value={!!fieldValue}
              required={child.required}
              onChange={v => handleFieldChange(child.variable, v)}
            />
          )}

          {/* Array[String] type */}
          {isArrayString && inputMode === 'form' && (
            <div className='space-y-2'>
              {(fieldValue as string[] || ['']).map((item: string, index: number) => (
                <div key={index} className='flex items-center gap-2'>
                  <Input
                    value={item || ''}
                    onChange={e => handleArrayItemChange(child.variable, index)(e.target.value)}
                    placeholder={`${t('appDebug.variableConfig.content')} ${index + 1}`}
                    className='flex-1'
                    disabled={disabled}
                  />
                  {(fieldValue as any)?.length > 1 && (
                    <RiDeleteBinLine
                      onClick={handleArrayItemRemove(child.variable, index)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleFieldChange(child.variable, [...(fieldValue as string[] || []), ''])}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                disabled={disabled}
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {isArrayString && inputMode === 'json' && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'["item1", "item2"]'}</div>}
            />
          )}

          {/* Array[Number] type */}
          {isArrayNumber && inputMode === 'form' && (
            <div className='space-y-2'>
              {(fieldValue as number[] || [0]).map((item: number, index: number) => (
                <div key={index} className='flex items-center gap-2'>
                  <Input
                    type='number'
                    value={item ?? ''}
                    onChange={e => handleArrayItemChange(child.variable, index)(e.target.value ? Number(e.target.value) : 0)}
                    placeholder={`${t('appDebug.variableConfig.content')} ${index + 1}`}
                    className='flex-1'
                    disabled={disabled}
                  />
                  {(fieldValue as any)?.length > 1 && (
                    <RiDeleteBinLine
                      onClick={handleArrayItemRemove(child.variable, index)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleFieldChange(child.variable, [...(fieldValue as number[] || []), 0])}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                disabled={disabled}
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {isArrayNumber && inputMode === 'json' && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'[1, 2, 3]'}</div>}
            />
          )}

          {/* Array[Boolean] type */}
          {isArrayBoolean && inputMode === 'form' && (
            <div className='space-y-2'>
              {(fieldValue as boolean[] || [false]).map((item: boolean, index: number) => (
                <div key={index} className='flex items-center gap-2'>
                  <BoolInput
                    name={`${child.variable} [${index + 1}]`}
                    value={!!item}
                    required={false}
                    onChange={v => handleArrayItemChange(child.variable, index)(v)}
                  />
                  {(fieldValue as any)?.length > 1 && (
                    <RiDeleteBinLine
                      onClick={handleArrayItemRemove(child.variable, index)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleFieldChange(child.variable, [...(fieldValue as boolean[] || []), false])}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                disabled={disabled}
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {isArrayBoolean && inputMode === 'json' && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'[true, false]'}</div>}
            />
          )}

          {/* Array[Object] type with children */}
          {isArrayObject && hasChildren && inputMode === 'form' && (
            <div className='space-y-2'>
              {(fieldValue as Record<string, unknown>[] || [{}]).map((item: Record<string, unknown>, index: number) => (
                <div key={index} className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                  <div className='mb-2 flex items-center justify-between'>
                    <span className='system-xs-semibold text-text-secondary'>
                      {t('appDebug.variableConfig.content')} {index + 1}
                    </span>
                    {(fieldValue as any)?.length > 1 && (
                      <RiDeleteBinLine
                        onClick={handleArrayItemRemove(child.variable, index)}
                        className='h-4 w-4 cursor-pointer text-text-tertiary hover:text-text-secondary'
                      />
                    )}
                  </div>
                  <NestedObjectInput
                    definition={child.children!}
                    value={typeof item === 'object' && item !== null ? item : {}}
                    onChange={v => handleArrayItemChange(child.variable, index)(v)}
                    depth={depth + 1}
                    disabled={disabled}
                  />
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleFieldChange(child.variable, [...(fieldValue as Record<string, unknown>[] || []), {}])}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                disabled={disabled}
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {isArrayObject && hasChildren && inputMode === 'json' && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'[{}, {}]'}</div>}
            />
          )}

          {/* Array[Object] type without children - JSON array editor */}
          {isArrayObject && !hasChildren && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'[{}, {}]'}</div>}
            />
          )}

          {/* Nested object type with children */}
          {isObjectType && hasChildren && isExpanded && inputMode === 'form' && (
            <div className='mt-2 rounded-lg border border-components-panel-border bg-components-panel-bg p-2'>
              <NestedObjectInput
                definition={child.children!}
                value={(fieldValue as Record<string, unknown>) || {}}
                onChange={v => handleFieldChange(child.variable, v)}
                depth={depth + 1}
                disabled={disabled}
              />
            </div>
          )}

          {/* Object type with children - JSON mode */}
          {isObjectType && hasChildren && inputMode === 'json' && (
            <CodeEditor
              value={jsonValue}
              language={CodeLanguage.json}
              onChange={v => handleJsonChange(child.variable, v)}
              noWrapper
              className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={<div className='whitespace-pre'>{'{}'}</div>}
            />
          )}

          {/* Object type without children - show JSON input */}
          {isObjectType && !hasChildren && (
            <Textarea
              value={typeof fieldValue === 'object' ? JSON.stringify(fieldValue, null, 2) : ''}
              onChange={(e) => {
                try {
                  const parsed = JSON.parse(e.target.value)
                  handleFieldChange(child.variable, parsed)
                }
                catch {
                  // Keep the raw string if not valid JSON
                }
              }}
              placeholder='{ }'
              disabled={disabled}
              className='font-mono text-xs'
            />
          )}
        </div>
      </div>
    )
  }, [value, expandedFields, depth, disabled, handleFieldChange, toggleExpand, t, inputModes, getInputMode, setInputMode, getJsonValue, handleJsonChange, handleArrayItemChange, handleArrayItemRemove])

  return (
    <div className={cn('space-y-2', className)}>
      {definition.map(renderField)}
    </div>
  )
}

/**
 * Get display label for input type
 */
function getTypeLabel(type: InputVarType): string {
  const labels: Partial<Record<InputVarType, string>> = {
    [InputVarType.textInput]: 'string',
    [InputVarType.paragraph]: 'string',
    [InputVarType.number]: 'number',
    [InputVarType.checkbox]: 'boolean',
    [InputVarType.object]: 'object',
    [InputVarType.singleFile]: 'file',
    [InputVarType.multiFiles]: 'files',
    [InputVarType.arrayString]: 'array[string]',
    [InputVarType.arrayNumber]: 'array[number]',
    [InputVarType.arrayBoolean]: 'array[boolean]',
    [InputVarType.arrayObject]: 'array[object]',
  }
  return labels[type] || type
}

export default React.memo(NestedObjectInput)
