'use client'
import type { FC } from 'react'
import React, { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { produce } from 'immer'
import {
  MAX_NESTING_DEPTH,
  type NestedVariableDefinition,
  type NestedVariableEditorProps,
  isNestableType,
} from '@/types/workflow/nested-variable'
import VariableRow from './variable-row'
import { createDefaultChildVariable, createDefaultVariable } from './utils'
import AddButton from '../add-button'

/**
 * NestedVariableEditor - A component for editing nested variable definitions
 *
 * This component allows users to define complex nested variable structures
 * with support for Object and Array<Object> types that can contain child variables.
 *
 * Features:
 * - Add/remove variables at any level
 * - Configure variable name, type, required flag, and description
 * - Support for nested children (Object and Array<Object> types)
 * - Expand/collapse nested structures
 * - Maximum nesting depth enforcement
 * - Visual indentation for hierarchy
 *
 * @see Requirements 7.1, 7.4, 7.5
 */
const NestedVariableEditor: FC<NestedVariableEditorProps> = ({
  value,
  onChange,
  maxDepth = MAX_NESTING_DEPTH,
  disabled = false,
  currentDepth = 0,
  parentPath = '',
}) => {
  const { t } = useTranslation()

  // Track expanded state for each variable by path
  const [expandedPaths, setExpandedPaths] = useState<Set<string>>(new Set())

  // Get sibling names for validation
  const siblingNames = useMemo(() => value.map(v => v.name), [value])

  // Check if we can add more nesting
  const canAddMoreNesting = currentDepth < maxDepth - 1

  // Toggle expand/collapse for a variable
  const toggleExpand = useCallback((path: string) => {
    setExpandedPaths((prev) => {
      const next = new Set(prev)
      if (next.has(path))
        next.delete(path)
      else
        next.add(path)

      return next
    })
  }, [])

  // Add a new variable at the current level
  const handleAddVariable = useCallback(() => {
    const newVariable = createDefaultVariable()
    onChange([...value, newVariable])
  }, [value, onChange])

  // Update a variable at a specific index
  const handleUpdateVariable = useCallback((index: number, updated: NestedVariableDefinition) => {
    const newValue = produce(value, (draft) => {
      draft[index] = updated
    })
    onChange(newValue)
  }, [value, onChange])

  // Delete a variable at a specific index (cascade deletes children)
  const handleDeleteVariable = useCallback((index: number) => {
    const newValue = produce(value, (draft) => {
      draft.splice(index, 1)
    })
    onChange(newValue)
  }, [value, onChange])

  // Add a child to a variable at a specific index
  const handleAddChild = useCallback((index: number) => {
    const variable = value[index]
    const newChild = createDefaultChildVariable()
    const updatedVariable: NestedVariableDefinition = {
      ...variable,
      children: [...(variable.children || []), newChild],
    }
    handleUpdateVariable(index, updatedVariable)

    // Auto-expand when adding a child (use name-based path for expand state)
    const namePath = parentPath ? `${parentPath}.${variable.name || index}` : (variable.name || String(index))
    setExpandedPaths(prev => new Set(prev).add(namePath))
  }, [value, handleUpdateVariable, parentPath])

  // Handle children change for a variable
  const handleChildrenChange = useCallback((index: number, children: NestedVariableDefinition[]) => {
    const variable = value[index]
    const updatedVariable: NestedVariableDefinition = {
      ...variable,
      children,
    }
    handleUpdateVariable(index, updatedVariable)
  }, [value, handleUpdateVariable])

  // Render empty state
  if (value.length === 0 && currentDepth === 0) {
    return (
      <div className="space-y-2">
        <div className="flex h-[42px] items-center justify-center rounded-md bg-components-panel-bg text-xs font-normal leading-[18px] text-text-tertiary">
          {t('workflow.nodes.start.noVarTip')}
        </div>
        {!disabled && (
          <AddButton
            text={t('workflow.nestedVariable.addVariable') || 'Add Variable'}
            onClick={handleAddVariable}
          />
        )}
      </div>
    )
  }

  return (
    <div className="space-y-1">
      {value.map((variable, index) => {
        // Use index-based path for key to avoid duplicate key issues when names are the same
        const indexPath = parentPath ? `${parentPath}[${index}]` : `[${index}]`
        // Use name-based path for expand state (so renaming doesn't collapse)
        const namePath = parentPath ? `${parentPath}.${variable.name || index}` : (variable.name || String(index))
        const isExpanded = expandedPaths.has(namePath)
        const canAddChildren = isNestableType(variable.type) && canAddMoreNesting

        return (
          <VariableRow
            key={indexPath}
            variable={variable}
            depth={currentDepth}
            canAddChildren={canAddChildren}
            isExpanded={isExpanded}
            onUpdate={updated => handleUpdateVariable(index, updated)}
            onDelete={() => handleDeleteVariable(index)}
            onAddChild={() => handleAddChild(index)}
            onToggleExpand={() => toggleExpand(namePath)}
            disabled={disabled}
            siblingNames={siblingNames}
          >
            {/* Render nested editor for children */}
            {variable.children && variable.children.length > 0 && isExpanded && (
              <NestedVariableEditor
                value={variable.children}
                onChange={children => handleChildrenChange(index, children)}
                maxDepth={maxDepth}
                disabled={disabled}
                currentDepth={currentDepth + 1}
                parentPath={namePath}
              />
            )}
          </VariableRow>
        )
      })}

      {/* Add variable button */}
      {!disabled && currentDepth === 0 && (
        <AddButton
          text={t('workflow.nestedVariable.addVariable') || 'Add Variable'}
          onClick={handleAddVariable}
        />
      )}
    </div>
  )
}

export default React.memo(NestedVariableEditor)
