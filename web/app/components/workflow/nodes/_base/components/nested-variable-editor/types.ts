/**
 * Types for the NestedVariableEditor component
 */

import type { NestedVariableDefinition, NestedVariableType } from '@/types/workflow/nested-variable'

export type VariableRowProps = {
  /** The variable definition */
  variable: NestedVariableDefinition
  /** Current nesting depth */
  depth: number
  /** Whether children can be added */
  canAddChildren: boolean
  /** Whether the row is expanded */
  isExpanded: boolean
  /** Callback when variable is updated */
  onUpdate: (updated: NestedVariableDefinition) => void
  /** Callback when variable is deleted */
  onDelete: () => void
  /** Callback when a child is added */
  onAddChild: () => void
  /** Callback when expand/collapse is toggled */
  onToggleExpand: () => void
  /** Whether the editor is disabled */
  disabled?: boolean
  /** Existing variable names at the same level (for validation) */
  siblingNames: string[]
  /** Children content (nested editor) */
  children?: React.ReactNode
}

export type NestedVariableEditorInternalProps = {
  /** Current variable definitions */
  value: NestedVariableDefinition[]
  /** Callback when definitions change */
  onChange: (value: NestedVariableDefinition[]) => void
  /** Maximum nesting depth allowed */
  maxDepth: number
  /** Current nesting depth */
  currentDepth: number
  /** Parent path for generating unique keys */
  parentPath: string
  /** Whether the editor is disabled */
  disabled?: boolean
}

export type TypeOption = {
  value: NestedVariableType
  name: string
  i18nKey?: string
}
