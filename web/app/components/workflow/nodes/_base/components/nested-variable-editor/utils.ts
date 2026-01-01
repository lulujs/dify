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
 * Validation error for nested variables
 */
export type NestedVariableValidationError = {
  path: string
  errorKey: string
  field?: string
}

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
    name: name || '',
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
    name: '',
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
 * Recursively validates all nested variable definitions
 * Returns an array of validation errors, empty array if all valid
 *
 * Validates:
 * - Variable names are not empty
 * - Variable names follow the correct format (letter start, alphanumeric + underscore)
 * - No duplicate names at the same level (sibling names)
 *
 * @param variables - Array of variable definitions to validate
 * @param parentPath - Path prefix for error reporting (e.g., "user.profile")
 * @returns Array of validation errors
 */
export function validateNestedVariables(
  variables: NestedVariableDefinition[] | undefined,
  parentPath: string = '',
): NestedVariableValidationError[] {
  if (!variables || variables.length === 0)
    return []

  const errors: NestedVariableValidationError[] = []
  const siblingNames: string[] = []

  for (const variable of variables) {
    const currentPath = parentPath ? `${parentPath}.${variable.name || '(empty)'}` : (variable.name || '(empty)')

    // Check if name is empty
    if (!variable.name.trim()) {
      errors.push({
        path: currentPath,
        errorKey: 'workflow.nestedVariable.validation.emptyName',
      })
      continue // Skip further validation for this variable
    }

    // Check if name format is valid
    if (!isValidVariableName(variable.name)) {
      errors.push({
        path: currentPath,
        errorKey: 'workflow.nestedVariable.validation.invalidFormat',
        field: variable.name,
      })
    }

    // Check for duplicate names at the same level
    if (siblingNames.includes(variable.name)) {
      errors.push({
        path: currentPath,
        errorKey: 'workflow.nestedVariable.validation.duplicateName',
        field: variable.name,
      })
    }
    else {
      siblingNames.push(variable.name)
    }

    // Recursively validate children
    if (variable.children && variable.children.length > 0) {
      const childErrors = validateNestedVariables(variable.children, currentPath)
      errors.push(...childErrors)
    }
  }

  return errors
}

/**
 * Formats validation errors into a user-friendly message
 * @param errors - Array of validation errors
 * @param t - Translation function
 * @returns Formatted error message string
 */
export function formatValidationErrors(
  errors: NestedVariableValidationError[],
  t: (key: string, options?: Record<string, string>) => string,
): string {
  if (errors.length === 0)
    return ''

  // Return the first error message for simplicity
  const firstError = errors[0]
  const message = t(firstError.errorKey, { field: firstError.field || '', path: firstError.path })
  return message || firstError.errorKey
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
