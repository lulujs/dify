import type { CommonNodeType, VarType, Variable } from '@/app/components/workflow/types'

export enum CodeLanguage {
  python3 = 'python3',
  javascript = 'javascript',
  json = 'json',
}

/**
 * Output variable child definition for Code node.
 * Uses dict format keyed by variable name to match backend structure.
 */
export type OutputVarChild = {
  type: VarType
  children?: Record<string, OutputVarChild> | null // dict of children keyed by name
}

export type OutputVar = Record<string, {
  type: VarType
  children: Record<string, OutputVarChild> | null // dict of children keyed by name
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
