'use client'
import type { FC } from 'react'
import React from 'react'
import { Type } from '../../../../../llm/types'
import { getFieldType } from '../../../../../llm/utils'
import type { Field as FieldType } from '../../../../../llm/types'
import cn from '@/utils/classnames'
import TreeIndentLine from '../tree-indent-line'
import { RiMoreFill } from '@remixicon/react'
import Tooltip from '@/app/components/base/tooltip'
import type { ValueSelector, Var } from '@/app/components/workflow/types'
import { VarType } from '@/app/components/workflow/types'
import { useTranslation } from 'react-i18next'
import { varTypeToStructType } from '../../utils'

const MAX_DEPTH = 10

/**
 * Converts StructuredOutput Type to VarType for compatibility checking
 * @see Requirements 4.3 - Type compatibility validation
 */
const structTypeToVarType = (type: Type): VarType => {
  const mapping: Record<Type, VarType> = {
    [Type.string]: VarType.string,
    [Type.number]: VarType.number,
    [Type.boolean]: VarType.boolean,
    [Type.object]: VarType.object,
    [Type.array]: VarType.array,
    [Type.arrayString]: VarType.arrayString,
    [Type.arrayNumber]: VarType.arrayNumber,
    [Type.arrayObject]: VarType.arrayObject,
    [Type.file]: VarType.file,
    [Type.enumType]: VarType.string, // enum maps to string
  }
  return mapping[type] || VarType.any
}

type Props = {
  valueSelector: ValueSelector
  name: string
  payload: FieldType
  depth?: number
  readonly?: boolean
  onSelect?: (valueSelector: ValueSelector) => void
  /**
   * Optional filter function to validate type compatibility for nested paths.
   * Returns true if the path should be selectable, false otherwise.
   *
   * @see Requirements 4.3 - Type compatibility validation
   */
  filterNestedPath?: (valueSelector: ValueSelector, fieldType: VarType) => boolean
}

/**
 * Converts Var[] children to StructuredOutput properties format
 * This enables proper nested path selection for variables with Var[] children
 *
 * @see Requirements 4.1, 4.2 - Variable selector nested path support
 */
const varChildrenToProperties = (children: Var[]): Record<string, FieldType> => {
  const properties: Record<string, FieldType> = {}
  children.forEach((child) => {
    const fieldType: FieldType = {
      type: varTypeToStructType(child.type),
      description: child.des,
    }
    // Recursively convert nested Var[] children
    if (
      (child.type === VarType.object || child.type === VarType.file)
      && child.children
      && Array.isArray(child.children)
      && child.children.length > 0
    )
      fieldType.properties = varChildrenToProperties(child.children as Var[])

    properties[child.variable] = fieldType
  })
  return properties
}

const Field: FC<Props> = ({
  valueSelector,
  name,
  payload,
  depth = 1,
  readonly,
  onSelect,
  filterNestedPath,
}) => {
  const { t } = useTranslation()
  const isLastFieldHighlight = readonly
  const hasChildren = payload.type === Type.object && payload.properties

  // Calculate full value selector for this field
  const fullValueSelector = [...valueSelector, name]
  const fieldVarType = structTypeToVarType(payload.type)

  // Check type compatibility if filter is provided
  const isTypeCompatible = !filterNestedPath || filterNestedPath(fullValueSelector, fieldVarType)
  const isSelectable = !readonly && isTypeCompatible

  const isHighlight = isLastFieldHighlight && !hasChildren
  if (depth > MAX_DEPTH + 1)
    return null

  // Tooltip content for incompatible types
  const tooltipContent = !isTypeCompatible
    ? t('workflow.common.typeNotCompatible')
    : (depth === MAX_DEPTH + 1 ? t('app.structOutput.moreFillTip') : undefined)

  return (
    <div>
      <Tooltip popupContent={tooltipContent} disabled={!tooltipContent}>
        <div
          className={cn(
            'flex items-center justify-between rounded-md pr-2',
            isSelectable && 'cursor-pointer hover:bg-state-base-hover',
            !isTypeCompatible && 'cursor-not-allowed opacity-50',
            depth === MAX_DEPTH + 1 && 'cursor-default',
          )}
          onMouseDown={() => isSelectable && depth !== MAX_DEPTH + 1 && onSelect?.(fullValueSelector)}
        >
          <div className='flex grow items-stretch'>
            <TreeIndentLine depth={depth} />
            {depth === MAX_DEPTH + 1 ? (
              <RiMoreFill className='h-3 w-3 text-text-tertiary' />
            ) : (<div className={cn('system-sm-medium h-6 w-0 grow truncate leading-6 text-text-secondary', isHighlight && 'text-text-accent')}>{name}</div>)}

          </div>
          {depth < MAX_DEPTH + 1 && (
            <div className='system-xs-regular ml-2 shrink-0 text-text-tertiary'>{getFieldType(payload)}</div>
          )}
        </div>
      </Tooltip>

      {depth <= MAX_DEPTH && payload.type === Type.object && payload.properties && (
        <div>
          {Object.keys(payload.properties).map(propName => (
            <Field
              key={propName}
              name={propName}
              payload={payload.properties?.[propName] as FieldType}
              depth={depth + 1}
              readonly={readonly}
              valueSelector={fullValueSelector}
              onSelect={onSelect}
              filterNestedPath={filterNestedPath}
            />
          ))}
        </div>
      )}
    </div>
  )
}

// Export the helper function for use in other components
export { varChildrenToProperties }
export default React.memo(Field)
