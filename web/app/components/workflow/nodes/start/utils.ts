import type { InputVarChild } from '@/app/components/workflow/types'
import { InputVarType } from '@/app/components/workflow/types'
import type { NestedVariableDefinition } from '@/types/workflow/nested-variable'
import { NestedVariableType } from '@/types/workflow/nested-variable'
import type { StartNodeType } from './types'

export const checkNodeValid = (_payload: StartNodeType) => {
  return true
}

/**
 * Maps InputVarType to NestedVariableType for nested variable support.
 * Only a subset of InputVarType values are supported for nested children.
 */
const inputVarTypeToNestedType: Partial<Record<InputVarType, NestedVariableType>> = {
  [InputVarType.textInput]: NestedVariableType.STRING,
  [InputVarType.paragraph]: NestedVariableType.STRING,
  [InputVarType.number]: NestedVariableType.NUMBER,
  [InputVarType.checkbox]: NestedVariableType.BOOLEAN,
  [InputVarType.singleFile]: NestedVariableType.FILE,
  [InputVarType.multiFiles]: NestedVariableType.ARRAY_FILE,
  [InputVarType.jsonObject]: NestedVariableType.OBJECT,
}

/**
 * Maps NestedVariableType to InputVarType for nested variable support.
 */
const nestedTypeToInputVarType: Partial<Record<NestedVariableType, InputVarType>> = {
  [NestedVariableType.STRING]: InputVarType.textInput,
  [NestedVariableType.INTEGER]: InputVarType.number,
  [NestedVariableType.NUMBER]: InputVarType.number,
  [NestedVariableType.BOOLEAN]: InputVarType.checkbox,
  [NestedVariableType.FILE]: InputVarType.singleFile,
  [NestedVariableType.OBJECT]: InputVarType.jsonObject,
  [NestedVariableType.ARRAY_STRING]: InputVarType.textInput,
  [NestedVariableType.ARRAY_INTEGER]: InputVarType.number,
  [NestedVariableType.ARRAY_NUMBER]: InputVarType.number,
  [NestedVariableType.ARRAY_BOOLEAN]: InputVarType.checkbox,
  [NestedVariableType.ARRAY_FILE]: InputVarType.multiFiles,
  [NestedVariableType.ARRAY_OBJECT]: InputVarType.jsonObject,
}

/**
 * Converts InputVarChild array to NestedVariableDefinition array.
 * Used when displaying nested variables in the NestedVariableEditor.
 */
export function inputVarChildrenToNestedDefinitions(
  children: InputVarChild[] | undefined,
): NestedVariableDefinition[] {
  if (!children || children.length === 0)
    return []

  return children.map((child): NestedVariableDefinition => {
    const nestedType = inputVarTypeToNestedType[child.type] || NestedVariableType.STRING
    return {
      name: child.variable,
      type: nestedType,
      required: child.required,
      description: child.description,
      defaultValue: child.default,
      children: inputVarChildrenToNestedDefinitions(child.children),
    }
  })
}

/**
 * Converts NestedVariableDefinition array to InputVarChild array.
 * Used when saving nested variables from the NestedVariableEditor.
 */
export function nestedDefinitionsToInputVarChildren(
  definitions: NestedVariableDefinition[] | undefined,
): InputVarChild[] {
  if (!definitions || definitions.length === 0)
    return []

  return definitions.map((def): InputVarChild => {
    const inputVarType = nestedTypeToInputVarType[def.type] || InputVarType.textInput
    return {
      variable: def.name,
      type: inputVarType,
      required: def.required,
      description: def.description,
      default: def.defaultValue,
      children: nestedDefinitionsToInputVarChildren(def.children),
    }
  })
}
