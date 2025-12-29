/**
 * Constants for the NestedVariableEditor component
 */

import { NestedVariableType } from '@/types/workflow/nested-variable'
import type { TypeOption } from './types'

/**
 * Available variable type options for child variables
 * Types are displayed in English without translation
 * Supported types: string, number, boolean, object, array[string], array[number], array[boolean], array[object]
 */
export const TYPE_OPTIONS: TypeOption[] = [
  { value: NestedVariableType.STRING, name: 'string' },
  { value: NestedVariableType.NUMBER, name: 'number' },
  { value: NestedVariableType.BOOLEAN, name: 'boolean' },
  { value: NestedVariableType.OBJECT, name: 'object' },
  { value: NestedVariableType.ARRAY_STRING, name: 'array[string]' },
  { value: NestedVariableType.ARRAY_NUMBER, name: 'array[number]' },
  { value: NestedVariableType.ARRAY_BOOLEAN, name: 'array[boolean]' },
  { value: NestedVariableType.ARRAY_OBJECT, name: 'array[object]' },
]

/**
 * Indentation width per nesting level in pixels
 */
export const INDENT_WIDTH = 24

/**
 * Default variable name prefix
 */
export const DEFAULT_VAR_PREFIX = 'var_'

/**
 * Default child variable name prefix
 */
export const DEFAULT_CHILD_PREFIX = 'child_'
