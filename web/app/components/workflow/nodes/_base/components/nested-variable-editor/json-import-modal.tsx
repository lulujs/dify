'use client'
import type { FC } from 'react'
import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Modal from '@/app/components/base/modal'
import Button from '@/app/components/base/button'
import { type NestedVariableDefinition, NestedVariableType } from '@/types/workflow/nested-variable'
import CodeEditor from '@/app/components/workflow/nodes/_base/components/editor/code-editor'
import { CodeLanguage } from '@/app/components/workflow/nodes/code/types'

type Props = {
  isShow: boolean
  initialValue?: NestedVariableDefinition[]
  onClose: () => void
  onConfirm: (definitions: NestedVariableDefinition[]) => void
}

/**
 * Infer the NestedVariableType from a JSON value
 */
function inferType(value: unknown): NestedVariableType {
  if (value === null || value === undefined)
    return NestedVariableType.STRING

  if (typeof value === 'string')
    return NestedVariableType.STRING

  if (typeof value === 'number')
    return NestedVariableType.NUMBER

  if (typeof value === 'boolean')
    return NestedVariableType.BOOLEAN

  if (Array.isArray(value)) {
    if (value.length === 0)
      return NestedVariableType.ARRAY_STRING

    const firstItem = value[0]
    if (typeof firstItem === 'string')
      return NestedVariableType.ARRAY_STRING
    if (typeof firstItem === 'number')
      return NestedVariableType.ARRAY_NUMBER
    if (typeof firstItem === 'boolean')
      return NestedVariableType.ARRAY_BOOLEAN
    if (typeof firstItem === 'object' && firstItem !== null)
      return NestedVariableType.ARRAY_OBJECT

    return NestedVariableType.ARRAY_STRING
  }

  if (typeof value === 'object')
    return NestedVariableType.OBJECT

  return NestedVariableType.STRING
}

/**
 * Convert a JSON object to NestedVariableDefinition array
 */
function jsonToDefinitions(json: Record<string, unknown>, depth = 0, maxDepth = 3): NestedVariableDefinition[] {
  if (depth >= maxDepth)
    return []

  const definitions: NestedVariableDefinition[] = []

  for (const [key, value] of Object.entries(json)) {
    const type = inferType(value)
    const definition: NestedVariableDefinition = {
      name: key,
      type,
      required: true,
    }

    // Handle nested objects
    if (type === NestedVariableType.OBJECT && typeof value === 'object' && value !== null && !Array.isArray(value))
      definition.children = jsonToDefinitions(value as Record<string, unknown>, depth + 1, maxDepth)

    // Handle array of objects - infer structure from first item
    if (type === NestedVariableType.ARRAY_OBJECT && Array.isArray(value) && value.length > 0) {
      const firstItem = value[0]
      if (typeof firstItem === 'object' && firstItem !== null)
        definition.children = jsonToDefinitions(firstItem as Record<string, unknown>, depth + 1, maxDepth)
    }

    definitions.push(definition)
  }

  return definitions
}

/**
 * Get default value for a type
 */
function getDefaultValue(type: NestedVariableType): unknown {
  switch (type) {
    case NestedVariableType.STRING:
      return ''
    case NestedVariableType.NUMBER:
      return 0
    case NestedVariableType.BOOLEAN:
      return false
    case NestedVariableType.OBJECT:
      return {}
    case NestedVariableType.ARRAY_STRING:
      return ['']
    case NestedVariableType.ARRAY_NUMBER:
      return [0]
    case NestedVariableType.ARRAY_BOOLEAN:
      return [false]
    case NestedVariableType.ARRAY_OBJECT:
      return [{}]
    default:
      return ''
  }
}

/**
 * Convert NestedVariableDefinition array to JSON object
 */
function definitionsToJson(definitions: NestedVariableDefinition[]): Record<string, unknown> {
  const result: Record<string, unknown> = {}

  for (const def of definitions) {
    if (def.type === NestedVariableType.OBJECT && def.children && def.children.length > 0)
      result[def.name] = definitionsToJson(def.children)
    else if (def.type === NestedVariableType.ARRAY_OBJECT && def.children && def.children.length > 0)
      result[def.name] = [definitionsToJson(def.children)]
    else
      result[def.name] = getDefaultValue(def.type)
  }

  return result
}

const JsonEditModal: FC<Props> = ({
  isShow,
  initialValue,
  onClose,
  onConfirm,
}) => {
  const { t } = useTranslation()
  const [jsonValue, setJsonValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Initialize JSON value from definitions when modal opens
  useEffect(() => {
    if (isShow) {
      if (initialValue && initialValue.length > 0) {
        const json = definitionsToJson(initialValue)
        setJsonValue(JSON.stringify(json, null, 2))
      }
      else {
        setJsonValue('')
      }
      setError(null)
    }
  }, [isShow, initialValue])

  const handleJsonChange = useCallback((value: string) => {
    setJsonValue(value)
    setError(null)
  }, [])

  const handleConfirm = useCallback(() => {
    if (!jsonValue.trim()) {
      // Empty JSON means clear all definitions
      onConfirm([])
      onClose()
      return
    }

    try {
      const parsed = JSON.parse(jsonValue)

      if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
        setError(t('workflow.nestedVariable.jsonImport.objectError') || 'JSON must be an object')
        return
      }

      const definitions = jsonToDefinitions(parsed)
      onConfirm(definitions)
      onClose()
    }
    catch {
      setError(t('workflow.nestedVariable.jsonImport.parseError') || 'Invalid JSON format')
    }
  }, [jsonValue, onConfirm, onClose, t])

  const handleClose = useCallback(() => {
    setError(null)
    onClose()
  }, [onClose])

  const placeholder = `{
  "name": "John",
  "age": 30,
  "active": true,
  "tags": ["a", "b"],
  "address": {
    "city": "NYC",
    "zip": "10001"
  }
}`

  return (
    <Modal
      title={t('workflow.nestedVariable.jsonImport.title') || 'Edit JSON'}
      isShow={isShow}
      onClose={handleClose}
      className="!w-[480px]"
    >
      <div className="mb-4">
        <p className="mb-2 text-xs text-text-tertiary">
          {t('workflow.nestedVariable.jsonImport.description') || 'Edit JSON to define variable structure'}
        </p>
        <CodeEditor
          language={CodeLanguage.json}
          value={jsonValue}
          onChange={handleJsonChange}
          noWrapper
          className="h-[200px] overflow-y-auto rounded-lg border border-components-panel-border bg-components-input-bg-normal p-2"
          placeholder={<div className="whitespace-pre text-text-quaternary">{placeholder}</div>}
        />
        {error && (
          <p className="mt-2 text-xs text-text-destructive">{error}</p>
        )}
      </div>
      <div className="flex justify-end gap-2">
        <Button onClick={handleClose}>
          {t('common.operation.cancel')}
        </Button>
        <Button variant="primary" onClick={handleConfirm}>
          {t('common.operation.confirm')}
        </Button>
      </div>
    </Modal>
  )
}

export default React.memo(JsonEditModal)
