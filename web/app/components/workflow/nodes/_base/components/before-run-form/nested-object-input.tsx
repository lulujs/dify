'use client'
import type { FC } from 'react'
import React, { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { produce } from 'immer'
import { RiArrowDownSLine, RiArrowRightSLine } from '@remixicon/react'
import type { InputVarChild } from '../../../../types'
import { InputVarType } from '../../../../types'
import Input from '@/app/components/base/input'
import Textarea from '@/app/components/base/textarea'
import cn from '@/utils/classnames'
import BoolInput from './bool-input'

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

  const handleFieldChange = useCallback((fieldName: string, fieldValue: unknown) => {
    const newValue = produce(value || {}, (draft) => {
      draft[fieldName] = fieldValue
    })
    onChange(newValue)
  }, [value, onChange])

  const renderField = useCallback((child: InputVarChild) => {
    const fieldValue = value?.[child.variable]
    const isExpanded = expandedFields.has(child.variable)
    const hasChildren = child.children && child.children.length > 0
    const isObjectType = child.type === InputVarType.object

    return (
      <div key={child.variable} className={cn('mb-2 last:mb-0', depth > 0 && 'ml-4')}>
        {/* Field label */}
        <div className='mb-1 flex items-center gap-1'>
          {hasChildren && (
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

          {/* Nested object type with children */}
          {isObjectType && hasChildren && isExpanded && (
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
  }, [value, expandedFields, depth, disabled, handleFieldChange, toggleExpand, t])

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
  }
  return labels[type] || type
}

export default React.memo(NestedObjectInput)
