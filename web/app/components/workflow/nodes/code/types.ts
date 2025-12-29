import type { CommonNodeType, VarType, Variable } from '@/app/components/workflow/types'

export enum CodeLanguage {
  python3 = 'python3',
  javascript = 'javascript',
  json = 'json',
}

/**
 * Output variable definition for Code node.
 * Supports nested children for object and array[object] types.
 */
export type OutputVarChild = {
  type: VarType
  children?: OutputVarChild | null
}

export type OutputVar = Record<string, {
  type: VarType
  children: OutputVarChild | null // supports nested structure for object types
}>

export type CodeDependency = {
  name: string
  version?: string
}

export type CodeNodeType = CommonNodeType & {
  variables: Variable[]
  code_language: CodeLanguage
  code: string
  outputs: OutputVar
}
