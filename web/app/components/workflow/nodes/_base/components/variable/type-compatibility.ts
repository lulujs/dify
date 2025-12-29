/**
 * Type Compatibility Validation for Nested Variables
 *
 * This module provides utilities for validating type compatibility
 * when selecting nested variable paths in the workflow editor.
 *
 * @see Requirements 4.3 - Type compatibility validation for nested paths
 */

import { VarType } from '@/app/components/workflow/types'
import type { ValueSelector, Var } from '@/app/components/workflow/types'
import type { NestedVariableType } from '@/types/workflow/nested-variable'

/**
 * Type compatibility mapping for variable types.
 * Defines which types are compatible with each other.
 */
const TYPE_COMPATIBILITY_MAP: Record<string, VarType[]> = {
  // String is compatible with string
  [VarType.string]: [VarType.string, VarType.any],

  // Number is compatible with number and integer
  [VarType.number]: [VarType.number, VarType.integer, VarType.any],

  // Integer is compatible with integer and number
  [VarType.integer]: [VarType.integer, VarType.number, VarType.any],

  // Boolean is compatible with boolean
  [VarType.boolean]: [VarType.boolean, VarType.any],

  // Object is compatible with object
  [VarType.object]: [VarType.object, VarType.any],

  // File is compatible with file
  [VarType.file]: [VarType.file, VarType.any],

  // Array types
  [VarType.array]: [VarType.array, VarType.arrayAny, VarType.any],
  [VarType.arrayString]: [VarType.arrayString, VarType.array, VarType.arrayAny, VarType.any],
  [VarType.arrayNumber]: [VarType.arrayNumber, VarType.array, VarType.arrayAny, VarType.any],
  [VarType.arrayObject]: [VarType.arrayObject, VarType.array, VarType.arrayAny, VarType.any],
  [VarType.arrayBoolean]: [VarType.arrayBoolean, VarType.array, VarType.arrayAny, VarType.any],
  [VarType.arrayFile]: [VarType.arrayFile, VarType.array, VarType.arrayAny, VarType.any],

  // Any type is compatible with everything
  [VarType.any]: Object.values(VarType),
  [VarType.arrayAny]: [VarType.array, VarType.arrayAny, VarType.arrayString, VarType.arrayNumber, VarType.arrayObject, VarType.arrayBoolean, VarType.arrayFile, VarType.any],
}

/**
 * Checks if two variable types are compatible.
 *
 * @param sourceType - The type of the source variable
 * @param targetType - The expected type of the target input
 * @returns true if the types are compatible, false otherwise
 */
export function isTypeCompatible(sourceType: VarType, targetType: VarType): boolean {
  // Any type is always compatible
  if (targetType === VarType.any || sourceType === VarType.any)
    return true

  // Check if source type is in the compatible types for target
  const compatibleTypes = TYPE_COMPATIBILITY_MAP[targetType]
  if (compatibleTypes)
    return compatibleTypes.includes(sourceType)

  // Default: exact match required
  return sourceType === targetType
}

/**
 * Maps NestedVariableType to VarType for compatibility checking.
 */
export function nestedTypeToVarType(nestedType: NestedVariableType | string): VarType {
  const mapping: Record<string, VarType> = {
    'string': VarType.string,
    'integer': VarType.integer,
    'number': VarType.number,
    'boolean': VarType.boolean,
    'object': VarType.object,
    'file': VarType.file,
    'array[string]': VarType.arrayString,
    'array[integer]': VarType.arrayNumber, // Map to arrayNumber as VarType doesn't have arrayInteger
    'array[number]': VarType.arrayNumber,
    'array[boolean]': VarType.arrayBoolean,
    'array[object]': VarType.arrayObject,
    'array[file]': VarType.arrayFile,
  }
  return mapping[nestedType] || VarType.any
}

/**
 * Gets the type of a nested path within a variable.
 *
 * @param rootVar - The root variable
 * @param nestedPath - Array of path segments (e.g., ['profile', 'name'])
 * @returns The type at the nested path, or undefined if path is invalid
 */
export function getNestedPathType(rootVar: Var, nestedPath: string[]): VarType | undefined {
  if (nestedPath.length === 0)
    return rootVar.type

  let currentVar: Var | undefined = rootVar
  for (const segment of nestedPath) {
    if (!currentVar)
      return undefined

    // Check if current var has children
    if (!currentVar.children || !Array.isArray(currentVar.children))
      return undefined

    // Find the child with matching variable name
    currentVar = (currentVar.children as Var[]).find(child => child.variable === segment)
  }

  return currentVar?.type
}

/**
 * Creates a filter function that validates type compatibility for nested paths.
 *
 * @param expectedType - The expected type for the target input
 * @returns A filter function that can be used with VarReferencePicker
 */
export function createNestedTypeFilter(expectedType: VarType) {
  return (payload: Var, valueSelector: ValueSelector): boolean => {
    // If expected type is any, allow all
    if (expectedType === VarType.any)
      return true

    // Get the actual type of the selected path
    const actualType = payload.type

    // Check compatibility
    return isTypeCompatible(actualType, expectedType)
  }
}

/**
 * Validates if a value selector path is valid for a given variable structure.
 *
 * @param rootVar - The root variable
 * @param valueSelector - The full value selector path
 * @returns true if the path is valid, false otherwise
 */
export function isValidNestedPath(rootVar: Var, valueSelector: ValueSelector): boolean {
  // Value selector format: [nodeId, varName, ...nestedPath]
  if (valueSelector.length < 2)
    return false

  const nestedPath = valueSelector.slice(2) // Skip nodeId and varName
  if (nestedPath.length === 0)
    return true // Root variable is always valid

  const pathType = getNestedPathType(rootVar, nestedPath)
  return pathType !== undefined
}

/**
 * Gets a human-readable description of type compatibility.
 *
 * @param sourceType - The source variable type
 * @param targetType - The target expected type
 * @returns A description of the compatibility status
 */
export function getTypeCompatibilityMessage(sourceType: VarType, targetType: VarType): string {
  if (isTypeCompatible(sourceType, targetType))
    return `Type '${sourceType}' is compatible with '${targetType}'`

  return `Type mismatch: expected '${targetType}', got '${sourceType}'`
}
