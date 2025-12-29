'use client'
import type { FC } from 'react'
import React, { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  RiAddLine,
  RiArrowDownSLine,
  RiArrowRightSLine,
  RiDeleteBinLine,
} from '@remixicon/react'
import { isNestableType } from '@/types/workflow/nested-variable'
import type { NestedVariableType } from '@/types/workflow/nested-variable'
import { SimpleSelect } from '@/app/components/base/select'
import Switch from '@/app/components/base/switch'
import Input from '@/app/components/base/input'
import cn from '@/utils/classnames'
import VariableTypeIcon from './variable-type-icon'
import { INDENT_WIDTH, TYPE_OPTIONS } from './constants'
import { canHaveChildren, removeChildren, validateVariableName } from './utils'
import type { VariableRowProps } from './types'

const VariableRow: FC<VariableRowProps> = ({
  variable,
  depth,
  canAddChildren,
  isExpanded,
  onUpdate,
  onDelete,
  onAddChild,
  onToggleExpand,
  disabled = false,
  siblingNames,
  children,
}) => {
  const { t } = useTranslation()
  const [nameError, setNameError] = useState<string | null>(null)

  const showExpandButton = isNestableType(variable.type)
  const indentStyle = useMemo(() => ({ paddingLeft: `${depth * INDENT_WIDTH}px` }), [depth])

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.target.value
    const errorKey = validateVariableName(newName, siblingNames, variable.name)
    setNameError(errorKey ? (t(errorKey, { field: t('workflow.nestedVariable.variableName') }) || errorKey) : null)
    onUpdate({ ...variable, name: newName })
  }, [variable, siblingNames, onUpdate, t])

  const handleNameBlur = useCallback(() => {
    const errorKey = validateVariableName(variable.name, siblingNames, variable.name)
    setNameError(errorKey ? (t(errorKey, { field: t('workflow.nestedVariable.variableName') }) || errorKey) : null)
  }, [variable.name, siblingNames, t])

  const handleTypeChange = useCallback((item: { value: string | number }) => {
    const newType = item.value as NestedVariableType
    let updatedVariable = { ...variable, type: newType }

    // If changing from nestable to non-nestable, remove children
    if (!canHaveChildren(newType) && variable.children)
      updatedVariable = removeChildren(updatedVariable)

    onUpdate(updatedVariable)
  }, [variable, onUpdate])

  const handleRequiredChange = useCallback((checked: boolean) => {
    onUpdate({ ...variable, required: checked })
  }, [variable, onUpdate])

  const typeOptions = useMemo(() =>
    TYPE_OPTIONS.map(opt => ({
      value: opt.value,
      name: opt.name,
    })),
  [])

  return (
    <div className="variable-row">
      {/* Main row */}
      <div
        className={cn(
          'group flex items-center gap-2 rounded-lg border border-components-panel-border-subtle bg-components-panel-on-panel-item-bg px-2 py-1.5 hover:shadow-xs',
          disabled && 'cursor-not-allowed opacity-50',
        )}
        style={indentStyle}
      >
        {/* Expand/Collapse button */}
        <div className="flex h-5 w-5 shrink-0 items-center justify-center">
          {showExpandButton
            ? (
              <button
                type="button"
                onClick={onToggleExpand}
                disabled={disabled}
                className="flex h-5 w-5 items-center justify-center rounded hover:bg-state-base-hover"
              >
                {isExpanded
                  ? <RiArrowDownSLine className="h-4 w-4 text-text-tertiary" />
                  : <RiArrowRightSLine className="h-4 w-4 text-text-tertiary" />}
              </button>
            )
            : (
              <div className="h-4 w-4" />
            )}
        </div>

        {/* Type icon */}
        <VariableTypeIcon type={variable.type} className="h-3.5 w-3.5 shrink-0 text-text-tertiary" />

        {/* Name input */}
        <div className="w-[120px] shrink-0">
          <Input
            value={variable.name}
            onChange={handleNameChange}
            onBlur={handleNameBlur}
            disabled={disabled}
            destructive={!!nameError}
            placeholder={t('workflow.common.variableNamePlaceholder') || 'Variable name'}
            className="!h-7 !py-1 !text-xs"
          />
        </div>

        {/* Type selector */}
        <div className="w-[130px] shrink-0">
          <SimpleSelect
            items={typeOptions}
            defaultValue={variable.type}
            onSelect={handleTypeChange}
            disabled={disabled}
            wrapperClassName="!h-7"
            className="!h-7 !text-xs"
          />
        </div>

        {/* Required toggle */}
        <div className="flex shrink-0 items-center gap-1">
          <span className="text-xs text-text-tertiary">
            {t('workflow.nodes.start.required')}
          </span>
          <Switch
            size="sm"
            defaultValue={variable.required}
            onChange={handleRequiredChange}
            disabled={disabled}
          />
        </div>

        {/* Spacer to push action buttons to the right */}
        <div className="min-w-0 flex-1" />

        {/* Action buttons */}
        <div className="flex shrink-0 items-center gap-1">
          {/* Add child button - only for nestable types */}
          {canAddChildren && (
            <button
              type="button"
              onClick={onAddChild}
              disabled={disabled}
              className="group/add flex h-6 w-6 items-center justify-center rounded-md border border-components-button-secondary-border bg-components-button-secondary-bg shadow-xs hover:border-components-button-secondary-border-hover hover:bg-components-button-secondary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
              title={t('workflow.nestedVariable.addChild') || 'Add child'}
            >
              <RiAddLine className="group-hover/add:text-components-button-secondary-text-hover h-4 w-4 text-components-button-secondary-text" />
            </button>
          )}

          {/* Delete button */}
          <button
            type="button"
            onClick={onDelete}
            disabled={disabled}
            className="group/delete flex h-6 w-6 items-center justify-center rounded-md border border-transparent hover:border-state-destructive-border hover:bg-state-destructive-hover disabled:cursor-not-allowed disabled:opacity-50"
            title={t('common.operation.delete') || 'Delete'}
          >
            <RiDeleteBinLine className="h-4 w-4 text-text-tertiary group-hover/delete:text-text-destructive" />
          </button>
        </div>
      </div>

      {/* Validation error */}
      {nameError && (
        <div className="mt-1 text-xs text-text-destructive" style={{ paddingLeft: `${depth * INDENT_WIDTH + 8}px` }}>
          {nameError}
        </div>
      )}

      {/* Children (nested variables) */}
      {isExpanded && children && (
        <div className="mt-1">
          {children}
        </div>
      )}
    </div>
  )
}

export default React.memo(VariableRow)
