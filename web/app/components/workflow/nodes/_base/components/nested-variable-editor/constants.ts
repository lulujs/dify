/**
 * Constants for the NestedVariableEditor component
 */

import { NestedVariableType } from '@/types/workflow/nested-variable'
import type { TypeOption } from './types'

/**
 * All available variable type options for the type selector
 * Note: The 'name' field is the i18n key suffix under 'workflow.nestedVariable.types'
 */
export const TYPE_OPTIONS: TypeOption[] = [
  { value: NestedVariableType.STRING, name: 'string', i18nKey: 'workflow.nestedVariable.types.string' },
  { value: NestedVariableType.INTEGER, name: 'integer', i18nKey: 'workflow.nestedVariable.types.integer' },
  { value: NestedVariableType.NUMBER, name: 'number', i18nKey: 'workflow.nestedVariable.types.number' },
  { value: NestedVariableType.BOOLEAN, name: 'boolean', i18nKey: 'workflow.nestedVariable.types.boolean' },
  { value: NestedVariableType.OBJECT, name: 'object', i18nKey: 'workflow.nestedVariable.types.object' },
  { value: NestedVariableType.FILE, name: 'file', i18nKey: 'workflow.nestedVariable.types.file' },
  { value: NestedVariableType.ARRAY_STRING, name: 'arrayString', i18nKey: 'workflow.nestedVariable.types.arrayString' },
  { value: NestedVariableType.ARRAY_INTEGER, name: 'arrayInteger', i18nKey: 'workflow.nestedVariable.types.arrayInteger' },
  { value: NestedVariableType.ARRAY_NUMBER, name: 'arrayNumber', i18nKey: 'workflow.nestedVariable.types.arrayNumber' },
  { value: NestedVariableType.ARRAY_BOOLEAN, name: 'arrayBoolean', i18nKey: 'workflow.nestedVariable.types.arrayBoolean' },
  { value: NestedVariableType.ARRAY_OBJECT, name: 'arrayObject', i18nKey: 'workflow.nestedVariable.types.arrayObject' },
  { value: NestedVariableType.ARRAY_FILE, name: 'arrayFile', i18nKey: 'workflow.nestedVariable.types.arrayFile' },
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
