'use client'
import type { FC } from 'react'
import React, { useCallback, useState } from 'react'
import { produce } from 'immer'
import { useTranslation } from 'react-i18next'
import {
  RiAddLine,
  RiArrowDownSLine,
  RiArrowRightSLine,
  RiDeleteBinLine,
} from '@remixicon/react'
import type { OutputVar, OutputVarChild } from '../../../code/types'
import RemoveButton from '../remove-button'
import VarTypePicker from './var-type-picker'
import Input from '@/app/components/base/input'
import type { VarType } from '@/app/components/workflow/types'
import { VarType as VarTypeEnum } from '@/app/components/workflow/types'
import { checkKeys, replaceSpaceWithUnderscoreInVarNameInput } from '@/utils/var'
import type { ToastHandle } from '@/app/components/base/toast'
import Toast from '@/app/components/base/toast'
import { useDebounceFn } from 'ahooks'
import cn from '@/utils/classnames'

type Props = {
  readonly: boolean
  outputs: OutputVar
  outputKeyOrders: string[]
  onChange: (payload: OutputVar, changedIndex?: number, newKey?: string) => void
  onRemove: (index: number) => void
}

// Check if a type supports children
const isNestableType = (type: VarType): boolean => {
  return type === VarTypeEnum.object || type === VarTypeEnum.arrayObject
}

// Generate unique child name
const generateChildName = (existingNames: string[]): string => {
  let index = 1
  let name = `child_${index}`
  while (existingNames.includes(name)) {
    index++
    name = `child_${index}`
  }
  return name
}

// Child variable row component (dict format)
type ChildVarRowProps = {
  readonly: boolean
  childName: string
  child: OutputVarChild
  depth: number
  siblingNames: string[]
  onUpdate: (oldName: string, newName: string, child: OutputVarChild) => void
  onRemove: () => void
  onAddChild: () => void
}

const ChildVarRow: FC<ChildVarRowProps> = ({
  readonly,
  childName,
  child,
  depth,
  siblingNames: _siblingNames,
  onUpdate,
  onRemove,
  onAddChild: _onAddChild,
}) => {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(true)

  const childKeys = child?.children ? Object.keys(child.children).filter(k => child.children![k] !== null) : []
  const showExpandButton = child ? isNestableType(child.type) && childKeys.length > 0 : false
  const canAddChildren = child ? isNestableType(child.type) && depth < 4 : false

  const handleNameChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!child) return
    replaceSpaceWithUnderscoreInVarNameInput(e.target)
    onUpdate(childName, e.target.value, child)
  }, [childName, child, onUpdate])

  const handleTypeChange = useCallback((value: string) => {
    if (!child) return
    const newType = value as VarType
    const updatedChild: OutputVarChild = { ...child, type: newType }
    // Remove children if changing to non-nestable type
    if (!isNestableType(newType))
      updatedChild.children = null

    onUpdate(childName, childName, updatedChild)
  }, [childName, child, onUpdate])

  const handleAddNestedChild = useCallback(() => {
    if (!child) return
    const existingNames = child.children ? Object.keys(child.children) : []
    const newChildName = generateChildName(existingNames)
    const newChild: OutputVarChild = {
      type: VarTypeEnum.string,
      children: null,
    }
    const updatedChild: OutputVarChild = {
      ...child,
      children: {
        ...(child.children || {}),
        [newChildName]: newChild,
      },
    }
    onUpdate(childName, childName, updatedChild)
    setIsExpanded(true)
  }, [childName, child, onUpdate])

  const handleUpdateNestedChild = useCallback((oldNestedName: string, newNestedName: string, updatedNestedChild: OutputVarChild) => {
    if (!child) return
    const updatedChild: OutputVarChild = produce(child, (draft) => {
      if (draft.children) {
        if (oldNestedName !== newNestedName)
          delete draft.children[oldNestedName]

        draft.children[newNestedName] = updatedNestedChild
      }
    })
    onUpdate(childName, childName, updatedChild)
  }, [childName, child, onUpdate])

  const handleRemoveNestedChild = useCallback((nestedName: string) => {
    if (!child) return
    const updatedChild: OutputVarChild = produce(child, (draft) => {
      if (draft.children) {
        delete draft.children[nestedName]
        if (Object.keys(draft.children).length === 0)
          draft.children = null
      }
    })
    onUpdate(childName, childName, updatedChild)
  }, [childName, child, onUpdate])

  // Return null if child is null/undefined (after all hooks)
  if (!child)
    return null

  return (
    <div className="child-var-row">
      <div
        className={cn(
          'flex items-center gap-2 rounded-lg border border-components-panel-border-subtle bg-components-panel-on-panel-item-bg px-2 py-1.5',
          readonly && 'opacity-50',
        )}
        style={{ marginLeft: `${depth * 16}px` }}
      >
        {/* Expand/Collapse button */}
        <div className="flex h-5 w-5 shrink-0 items-center justify-center">
          {showExpandButton
            ? (
              <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                disabled={readonly}
                className="flex h-5 w-5 items-center justify-center rounded hover:bg-state-base-hover"
              >
                {isExpanded
                  ? <RiArrowDownSLine className="h-4 w-4 text-text-tertiary" />
                  : <RiArrowRightSLine className="h-4 w-4 text-text-tertiary" />}
              </button>
            )
            : <div className="h-4 w-4" />}
        </div>

        {/* Name input - editable */}
        <div className="w-[120px] shrink-0">
          <Input
            value={childName}
            onChange={handleNameChange}
            disabled={readonly}
            className="!h-7 !py-1 !text-xs"
            placeholder="name"
          />
        </div>

        {/* Type selector */}
        <div className="w-[120px] shrink-0">
          <VarTypePicker
            readonly={readonly}
            value={child.type}
            onChange={handleTypeChange}
          />
        </div>

        {/* Spacer */}
        <div className="min-w-0 flex-1" />

        {/* Action buttons */}
        <div className="flex shrink-0 items-center gap-1">
          {/* Add nested child button */}
          {canAddChildren && (
            <button
              type="button"
              onClick={handleAddNestedChild}
              disabled={readonly}
              className="group/add flex h-6 w-6 items-center justify-center rounded-md border border-components-button-secondary-border bg-components-button-secondary-bg shadow-xs hover:border-components-button-secondary-border-hover hover:bg-components-button-secondary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
              title={t('workflow.nestedVariable.addChild') || 'Add child'}
            >
              <RiAddLine className="group-hover/add:text-components-button-secondary-text-hover h-4 w-4 text-components-button-secondary-text" />
            </button>
          )}
          {/* Delete button */}
          <button
            type="button"
            onClick={onRemove}
            disabled={readonly}
            className="group/delete flex h-6 w-6 items-center justify-center rounded-md border border-transparent hover:border-state-destructive-border hover:bg-state-destructive-hover disabled:cursor-not-allowed disabled:opacity-50"
            title={t('common.operation.delete') || 'Delete'}
          >
            <RiDeleteBinLine className="h-4 w-4 text-text-tertiary group-hover/delete:text-text-destructive" />
          </button>
        </div>
      </div>

      {/* Nested children */}
      {isExpanded && child.children && childKeys.length > 0 && (
        <div className="mt-1 space-y-1">
          {childKeys.map(nestedName => (
            <ChildVarRow
              key={nestedName}
              readonly={readonly}
              childName={nestedName}
              child={child.children![nestedName]}
              depth={depth + 1}
              siblingNames={childKeys.filter(n => n !== nestedName)}
              onUpdate={handleUpdateNestedChild}
              onRemove={() => handleRemoveNestedChild(nestedName)}
              onAddChild={handleAddNestedChild}
            />
          ))}
        </div>
      )}
    </div>
  )
}

const OutputVarList: FC<Props> = ({
  readonly,
  outputs,
  outputKeyOrders,
  onChange,
  onRemove,
}) => {
  const { t } = useTranslation()
  const [toastHandler, setToastHandler] = useState<ToastHandle>()
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set())

  const list = outputKeyOrders.map(key => ({
    variable: key,
    variable_type: outputs[key]?.type,
    children: outputs[key]?.children,
  }))

  const toggleExpand = useCallback((key: string) => {
    setExpandedKeys((prev) => {
      const newSet = new Set(prev)
      if (newSet.has(key))
        newSet.delete(key)
      else
        newSet.add(key)

      return newSet
    })
  }, [])

  const { run: validateVarInput } = useDebounceFn((existingVariables: typeof list, newKey: string) => {
    const { isValid, errorKey, errorMessageKey } = checkKeys([newKey], true)
    if (!isValid) {
      setToastHandler(Toast.notify({
        type: 'error',
        message: t(`appDebug.varKeyError.${errorMessageKey}`, { key: errorKey }),
      }))
      return
    }
    if (existingVariables.some(key => key.variable?.trim() === newKey.trim())) {
      setToastHandler(Toast.notify({
        type: 'error',
        message: t('appDebug.varKeyError.keyAlreadyExists', { key: newKey }),
      }))
    }
    else {
      toastHandler?.clear?.()
    }
  }, { wait: 500 })

  const handleVarNameChange = useCallback((index: number) => {
    return (e: React.ChangeEvent<HTMLInputElement>) => {
      const oldKey = list[index].variable

      replaceSpaceWithUnderscoreInVarNameInput(e.target)
      const newKey = e.target.value

      toastHandler?.clear?.()
      validateVarInput(list.toSpliced(index, 1), newKey)

      const newOutputs = produce(outputs, (draft) => {
        draft[newKey] = draft[oldKey]
        delete draft[oldKey]
      })
      onChange(newOutputs, index, newKey)
    }
  }, [list, onChange, outputs, validateVarInput, toastHandler])

  const handleVarTypeChange = useCallback((index: number) => {
    return (value: string) => {
      const key = list[index].variable
      const newType = value as VarType
      const newOutputs = produce(outputs, (draft) => {
        draft[key].type = newType
        // Remove children if changing to non-nestable type
        if (!isNestableType(newType))
          draft[key].children = null
      })
      onChange(newOutputs)
    }
  }, [list, onChange, outputs])

  const handleVarRemove = useCallback((index: number) => {
    return () => {
      onRemove(index)
    }
  }, [onRemove])

  const handleAddChild = useCallback((index: number) => {
    const key = list[index].variable
    const existingNames = outputs[key]?.children ? Object.keys(outputs[key].children!) : []
    const newChildName = generateChildName(existingNames)
    const newChild: OutputVarChild = {
      type: VarTypeEnum.string,
      children: null,
    }
    const newOutputs = produce(outputs, (draft) => {
      draft[key].children = {
        ...(draft[key].children || {}),
        [newChildName]: newChild,
      }
    })
    onChange(newOutputs)
    // Auto-expand when adding child
    setExpandedKeys(prev => new Set(prev).add(key))
  }, [list, outputs, onChange])

  const handleUpdateChild = useCallback((index: number, oldChildName: string, newChildName: string, updatedChild: OutputVarChild) => {
    const key = list[index].variable
    const newOutputs = produce(outputs, (draft) => {
      if (draft[key].children) {
        if (oldChildName !== newChildName)
          delete draft[key].children![oldChildName]

        draft[key].children![newChildName] = updatedChild
      }
    })
    onChange(newOutputs)
  }, [list, outputs, onChange])

  const handleRemoveChild = useCallback((index: number, childName: string) => {
    const key = list[index].variable
    const newOutputs = produce(outputs, (draft) => {
      if (draft[key].children) {
        delete draft[key].children![childName]
        if (Object.keys(draft[key].children!).length === 0)
          draft[key].children = null
      }
    })
    onChange(newOutputs)
  }, [list, outputs, onChange])

  return (
    <div className='space-y-2'>
      {list.map((item, index) => {
        const childKeys = item.children ? Object.keys(item.children).filter(k => item.children![k] !== null) : []
        const showExpandButton = isNestableType(item.variable_type) && childKeys.length > 0
        const isExpanded = expandedKeys.has(item.variable)
        const canAddChildren = isNestableType(item.variable_type)

        return (
          <div key={index} className="output-var-item">
            <div className='flex items-center space-x-1'>
              {/* Expand/Collapse button for nestable types */}
              {showExpandButton
                ? (
                  <button
                    type="button"
                    onClick={() => toggleExpand(item.variable)}
                    className="flex h-8 w-6 shrink-0 items-center justify-center rounded hover:bg-state-base-hover"
                  >
                    {isExpanded
                      ? <RiArrowDownSLine className="h-4 w-4 text-text-tertiary" />
                      : <RiArrowRightSLine className="h-4 w-4 text-text-tertiary" />}
                  </button>
                )
                : <div className="w-6 shrink-0" />}

              <Input
                readOnly={readonly}
                value={item.variable}
                onChange={handleVarNameChange(index)}
                wrapperClassName='grow'
              />
              <VarTypePicker
                readonly={readonly}
                value={item.variable_type}
                onChange={handleVarTypeChange(index)}
              />

              {/* Add child button for nestable types */}
              {canAddChildren && (
                <button
                  type="button"
                  onClick={() => handleAddChild(index)}
                  disabled={readonly}
                  className="group/add flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-components-button-secondary-border bg-components-button-secondary-bg shadow-xs hover:border-components-button-secondary-border-hover hover:bg-components-button-secondary-bg-hover disabled:cursor-not-allowed disabled:opacity-50"
                  title={t('workflow.nestedVariable.addChild') || 'Add child'}
                >
                  <RiAddLine className="group-hover/add:text-components-button-secondary-text-hover h-4 w-4 text-components-button-secondary-text" />
                </button>
              )}

              <RemoveButton
                className='!bg-gray-100 !p-2 hover:!bg-gray-200'
                onClick={handleVarRemove(index)}
              />
            </div>

            {/* Children */}
            {isExpanded && item.children && childKeys.length > 0 && (
              <div className="ml-6 mt-1 space-y-1">
                {childKeys.map(childName => (
                  <ChildVarRow
                    key={childName}
                    readonly={readonly}
                    childName={childName}
                    child={item.children![childName]}
                    depth={1}
                    siblingNames={childKeys.filter(n => n !== childName)}
                    onUpdate={(oldName, newName, updatedChild) => handleUpdateChild(index, oldName, newName, updatedChild)}
                    onRemove={() => handleRemoveChild(index, childName)}
                    onAddChild={() => handleAddChild(index)}
                  />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
export default React.memo(OutputVarList)
