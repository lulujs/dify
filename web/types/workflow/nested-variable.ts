/**
 * Nested Variable Type Definitions
 *
 * This module defines TypeScript types for nested variable support in Dify workflows.
 * Nested variables allow users to define complex data structures with hierarchical
 * relationships, supporting Object and Array<Object> types with child variables.
 *
 * @see Requirements 1.3, 1.4 - Type support for child variables
 */

/**
 * Supported types for nested variables.
 * Includes primitive types, array types, and nestable types (object, array[object]).
 */
export enum NestedVariableType {
  // Primitive types
  STRING = 'string',
  INTEGER = 'integer',
  NUMBER = 'number',
  BOOLEAN = 'boolean',
  FILE = 'file',

  // Nestable types - can have children
  OBJECT = 'object',

  // Array types
  ARRAY_STRING = 'array[string]',
  ARRAY_INTEGER = 'array[integer]',
  ARRAY_NUMBER = 'array[number]',
  ARRAY_BOOLEAN = 'array[boolean]',
  ARRAY_FILE = 'array[file]',
  ARRAY_OBJECT = 'array[object]',
}

/**
 * Maximum allowed nesting depth for nested variables.
 * Prevents overly complex structures that could impact performance.
 */
export const MAX_NESTING_DEPTH = 5

/**
 * Regular expression pattern for validating variable names.
 * Names must start with a letter and contain only alphanumeric characters and underscores.
 */
export const VARIABLE_NAME_PATTERN = /^[a-zA-Z]\w*$/

/**
 * Checks if a variable type supports nested children.
 * Only 'object' and 'array[object]' types can have child variables.
 */
export function isNestableType(type: NestedVariableType): boolean {
  return type === NestedVariableType.OBJECT || type === NestedVariableType.ARRAY_OBJECT
}

/**
 * Checks if a variable type is an array type.
 */
export function isArrayType(type: NestedVariableType): boolean {
  return type.startsWith('array[')
}

/**
 * Validates a variable name against the naming pattern.
 * @param name - The variable name to validate
 * @returns true if the name is valid, false otherwise
 */
export function isValidVariableName(name: string): boolean {
  return VARIABLE_NAME_PATTERN.test(name)
}

/**
 * Definition of a nested variable.
 * Supports recursive structure for Object and Array<Object> types.
 */
export type NestedVariableDefinition = {
  /** Variable name - must match VARIABLE_NAME_PATTERN */
  name: string
  /** Variable type */
  type: NestedVariableType
  /** Whether the variable is required */
  required: boolean
  /** Optional description of the variable */
  description?: string
  /** Optional default value */
  defaultValue?: unknown
  /**
   * Child variable definitions.
   * Only valid for 'object' and 'array[object]' types.
   */
  children?: NestedVariableDefinition[]
}

/**
 * Enhanced variable selector that supports nested paths.
 * Used to reference variables from upstream nodes with nested access.
 */
export type EnhancedVariableSelector = {
  /** Variable reference string */
  variable: string
  /** Variable selector path - array of path segments */
  valueSelector: string[]
}

/**
 * Node input definition with nested variable support.
 */
export type NodeInputDefinition = {
  /** Input name */
  name: string
  /** Input type */
  type: NestedVariableType
  /** Whether the input is required */
  required: boolean
  /** Optional description */
  description?: string
  /** Variable selector for referencing upstream variables */
  variableSelector?: EnhancedVariableSelector
  /** Child variable definitions for nested types */
  children?: NestedVariableDefinition[]
  /** Default value */
  defaultValue?: unknown
}

/**
 * Node output definition with nested variable support.
 */
export type NodeOutputDefinition = {
  /** Output name */
  name: string
  /** Output type */
  type: NestedVariableType
  /** Optional description */
  description?: string
  /** Child variable definitions for nested types */
  children?: NestedVariableDefinition[]
}

/**
 * Props for the NestedVariableEditor component.
 */
export type NestedVariableEditorProps = {
  /** Current variable definitions */
  value: NestedVariableDefinition[]
  /** Callback when definitions change */
  onChange: (value: NestedVariableDefinition[]) => void
  /** Maximum nesting depth allowed (default: MAX_NESTING_DEPTH) */
  maxDepth?: number
  /** Whether the editor is disabled */
  disabled?: boolean
  /** Current nesting depth (used internally for recursion) */
  currentDepth?: number
  /** Parent path for generating unique keys (used internally) */
  parentPath?: string
}

/**
 * Validation error for nested variables.
 */
export type NestedVariableValidationError = {
  /** Error code */
  code: NestedVariableErrorCode
  /** Human-readable error message */
  message: string
  /** Path to the problematic variable (e.g., 'user.profile.age') */
  path?: string
  /** Expected type (for type mismatch errors) */
  expected?: string
  /** Actual type (for type mismatch errors) */
  actual?: string
}

/**
 * Error codes for nested variable validation.
 */
export enum NestedVariableErrorCode {
  INVALID_VARIABLE_NAME = 'INVALID_VARIABLE_NAME',
  DUPLICATE_CHILD_NAME = 'DUPLICATE_CHILD_NAME',
  MAX_DEPTH_EXCEEDED = 'MAX_DEPTH_EXCEEDED',
  INVALID_CHILDREN_TYPE = 'INVALID_CHILDREN_TYPE',
  REQUIRED_FIELD_MISSING = 'REQUIRED_FIELD_MISSING',
  TYPE_MISMATCH = 'TYPE_MISMATCH',
}

/**
 * Type guard to check if a value is a NestedVariableDefinition.
 */
export function isNestedVariableDefinition(value: unknown): value is NestedVariableDefinition {
  if (typeof value !== 'object' || value === null)
    return false

  const obj = value as Record<string, unknown>
  return (
    typeof obj.name === 'string'
    && typeof obj.type === 'string'
    && Object.values(NestedVariableType).includes(obj.type as NestedVariableType)
    && typeof obj.required === 'boolean'
  )
}

/**
 * Calculates the maximum nesting depth of a variable definition.
 * @param definition - The variable definition to analyze
 * @returns The maximum depth (1 for leaf nodes)
 */
export function getMaxDepth(definition: NestedVariableDefinition): number {
  if (!definition.children || definition.children.length === 0)
    return 1

  return 1 + Math.max(...definition.children.map(getMaxDepth))
}

/**
 * Gets the full path string from a variable selector.
 * @param selector - The enhanced variable selector
 * @returns Dot-notation path string
 */
export function getFullPath(selector: EnhancedVariableSelector): string {
  return selector.valueSelector.join('.')
}
