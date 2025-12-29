/**
 * Utility functions for the NestedVariableEditor component
 */

import {
  type NestedVariableDefinition,
  NestedVariableType,
  isNestableType,
  isValidVariableName,
} from '@/types/workflow/nested-variable'
import { DEFAULT_CHILD_PREFIX, DEFAULT_VAR_PREFIX } from './constants'

/**
 * Generates a unique variable name
 */
export function generateVariableName(prefix: string = DEFAULT_VAR_PREFIX): string {
  return `${prefix}${Date.now()}`
}

/**
 * Generates a unique child variable name
 */
export function generateChildName(): string {
  return generateVariableName(DEFAULT_CHILD_PREFIX)
}

/**
 * Creates a new default variable definition
 */
export function createDefaultVariable(name?: string): NestedVariableDefinition {
  return {
    name: name || generateVariableName(),
    type: NestedVariableType.STRING,
    required: false,
    description: '',
  }
}

/**
 * Creates a new default child variable definition
 */
export function createDefaultChildVariable(): NestedVariableDefinition {
  return {
    name: generateChildName(),
    type: NestedVariableType.STRING,
    required: false,
    description: '',
  }
}

/**
 * Checks if a variable type can have children
 */
export function canHaveChildren(type: NestedVariableType): boolean {
  return isNestableType(type)
}

/**
 * Validates a variable name and returns an error message key if invalid
 * Returns the i18n key for the error message, or null if valid
 */
export function validateVariableName(
  name: string,
  siblingNames: string[],
  currentName?: string,
): string | null {
  if (!name.trim())
    return 'workflow.errorMsg.fieldRequired'

  if (!isValidVariableName(name))
    return 'workflow.nestedVariable.invalidName'

  // Check for duplicates (excluding current name if editing)
  const otherNames = currentName
    ? siblingNames.filter(n => n !== currentName)
    : siblingNames

  if (otherNames.includes(name))
    return 'workflow.nestedVariable.duplicateName'

  return null
}

/**
 * Gets the display name for a variable type
 */
export function getTypeDisplayName(type: NestedVariableType): string {
  const displayNames: Record<NestedVariableType, string> = {
    [NestedVariableType.STRING]: 'String',
    [NestedVariableType.INTEGER]: 'Integer',
    [NestedVariableType.NUMBER]: 'Number',
    [NestedVariableType.BOOLEAN]: 'Boolean',
    [NestedVariableType.OBJECT]: 'Object',
    [NestedVariableType.FILE]: 'File',
    [NestedVariableType.ARRAY_STRING]: 'Array[String]',
    [NestedVariableType.ARRAY_INTEGER]: 'Array[Integer]',
    [NestedVariableType.ARRAY_NUMBER]: 'Array[Number]',
    [NestedVariableType.ARRAY_BOOLEAN]: 'Array[Boolean]',
    [NestedVariableType.ARRAY_OBJECT]: 'Array[Object]',
    [NestedVariableType.ARRAY_FILE]: 'Array[File]',
  }
  return displayNames[type] || type
}

/**
 * Recursively removes all children from a variable definition
 * Used when changing type from nestable to non-nestable
 */
export function removeChildren(variable: NestedVariableDefinition): NestedVariableDefinition {
  const { children, ...rest } = variable
  return rest
}
