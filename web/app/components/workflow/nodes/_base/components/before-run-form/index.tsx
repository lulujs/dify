'use client'
import type { FC } from 'react'
import React, { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import type { Props as FormProps } from './form'
import Form from './form'
import cn from '@/utils/classnames'
import Button from '@/app/components/base/button'
import Split from '@/app/components/workflow/nodes/_base/components/split'
import type { InputVarChild } from '@/app/components/workflow/types'
import { InputVarType } from '@/app/components/workflow/types'
import Toast from '@/app/components/base/toast'
import { TransferMethod } from '@/types/app'
import { getProcessedFiles } from '@/app/components/base/file-uploader/utils'
import type { BlockEnum, NodeRunningStatus } from '@/app/components/workflow/types'
import type { Emoji } from '@/app/components/tools/types'
import type { SpecialResultPanelProps } from '@/app/components/workflow/run/special-result-panel'
import PanelWrap from './panel-wrap'
const i18nPrefix = 'workflow.singleRun'

/**
 * Validates nested object values against their child definitions
 * Returns the path of the first missing required field, or null if all valid
 */
function validateNestedRequired(
  definition: InputVarChild[],
  value: Record<string, unknown> | undefined | null,
  parentPath: string,
): string | null {
  if (!definition || definition.length === 0)
    return null

  for (const child of definition) {
    const fieldValue = value?.[child.variable]
    const fieldPath = parentPath ? `${parentPath}.${child.variable}` : child.variable

    // Check if required field is missing or empty
    if (child.required) {
      const isEmpty = fieldValue === undefined
        || fieldValue === null
        || fieldValue === ''
        || (Array.isArray(fieldValue) && fieldValue.length === 0)

      if (isEmpty)
        return fieldPath
    }

    // Recursively validate nested children for object types
    if (child.children && child.children.length > 0 && child.type === InputVarType.object) {
      const nestedError = validateNestedRequired(
        child.children,
        fieldValue as Record<string, unknown> | undefined,
        fieldPath,
      )
      if (nestedError)
        return nestedError
    }

    // Recursively validate nested children for array[object] types
    if (child.children && child.children.length > 0 && child.type === InputVarType.arrayObject) {
      const arrayError = validateArrayObjectRequired(
        child.children,
        fieldValue as Array<Record<string, unknown>> | undefined,
        fieldPath,
      )
      if (arrayError)
        return arrayError
    }
  }

  return null
}

/**
 * Validates array of objects against their child definitions
 * Returns the path of the first missing required field, or null if all valid
 */
function validateArrayObjectRequired(
  definition: InputVarChild[],
  value: Array<Record<string, unknown>> | undefined | null,
  variableName: string,
): string | null {
  if (!definition || definition.length === 0 || !Array.isArray(value))
    return null

  for (let i = 0; i < value.length; i++) {
    const itemPath = `${variableName}[${i}]`
    const error = validateNestedRequired(definition, value[i], itemPath)
    if (error)
      return error
  }

  return null
}

export type BeforeRunFormProps = {
  nodeName: string
  nodeType?: BlockEnum
  toolIcon?: string | Emoji
  onHide: () => void
  onRun: (submitData: Record<string, any>) => void
  onStop: () => void
  runningStatus: NodeRunningStatus
  forms: FormProps[]
  showSpecialResultPanel?: boolean
  existVarValuesInForms: Record<string, any>[]
  filteredExistVarForms: FormProps[]
} & Partial<SpecialResultPanelProps>

function formatValue(value: string | any, type: InputVarType) {
  if(type === InputVarType.checkbox)
    return !!value
  if(value === undefined || value === null)
    return value
  if (type === InputVarType.number)
    return Number.parseFloat(value)
  if (type === InputVarType.json)
    return JSON.parse(value)
  if (type === InputVarType.contexts) {
    return value.map((item: any) => {
      return JSON.parse(item)
    })
  }
  if (type === InputVarType.multiFiles)
    return getProcessedFiles(value)

  if (type === InputVarType.singleFile) {
    if (Array.isArray(value))
      return getProcessedFiles(value)
    if (!value)
      return undefined
    return getProcessedFiles([value])[0]
  }

  return value
}
const BeforeRunForm: FC<BeforeRunFormProps> = ({
  nodeName,
  onHide,
  onRun,
  forms,
  filteredExistVarForms,
  existVarValuesInForms,
}) => {
  const { t } = useTranslation()

  const isFileLoaded = (() => {
    if (!forms || forms.length === 0)
      return true
    // system files
    const filesForm = forms.find(item => !!item.values['#files#'])
    if (!filesForm)
      return true

    const files = filesForm.values['#files#'] as any
    if (files?.some((item: any) => item.transfer_method === TransferMethod.local_file && !item.upload_file_id))
      return false

    return true
  })()
  const handleRun = () => {
    let errMsg = ''
    forms.forEach((form, i) => {
      const existVarValuesInForm = existVarValuesInForms[i]

      form.inputs.forEach((input) => {
        const value = form.values[input.variable] as any
        if (!errMsg && input.required && (input.type !== InputVarType.checkbox) && !(input.variable in existVarValuesInForm) && (value === '' || value === undefined || value === null || (input.type === InputVarType.files && value.length === 0)))
          errMsg = t('workflow.errorMsg.fieldRequired', { field: typeof input.label === 'object' ? input.label.variable : input.label })

        if (!errMsg && (input.type === InputVarType.singleFile || input.type === InputVarType.multiFiles) && value) {
          let fileIsUploading = false
          if (Array.isArray(value))
            fileIsUploading = value.find(item => item.transferMethod === TransferMethod.local_file && !item.uploadedId)
          else
            fileIsUploading = value.transferMethod === TransferMethod.local_file && !value.uploadedId

          if (fileIsUploading)
            errMsg = t('appDebug.errorMessage.waitForFileUpload')
        }

        // Validate nested required fields for object type
        if (!errMsg && input.type === InputVarType.object && input.children && input.children.length > 0) {
          const nestedError = validateNestedRequired(
            input.children,
            value as Record<string, unknown>,
            input.variable,
          )
          if (nestedError)
            errMsg = t('workflow.errorMsg.fieldRequired', { field: nestedError })
        }

        // Validate nested required fields for array[object] type
        if (!errMsg && input.type === InputVarType.arrayObject && input.children && input.children.length > 0) {
          const arrayError = validateArrayObjectRequired(
            input.children,
            value as Array<Record<string, unknown>>,
            input.variable,
          )
          if (arrayError)
            errMsg = t('workflow.errorMsg.fieldRequired', { field: arrayError })
        }

        // Validate required array primitive types (array[string], array[number], array[boolean])
        if (!errMsg && input.required && !(input.variable in existVarValuesInForm)) {
          const isArrayPrimitiveType = input.type === InputVarType.arrayString
            || input.type === InputVarType.arrayNumber
            || input.type === InputVarType.arrayBoolean

          if (isArrayPrimitiveType) {
            const isEmpty = !Array.isArray(value) || value.length === 0
            if (isEmpty)
              errMsg = t('workflow.errorMsg.fieldRequired', { field: typeof input.label === 'object' ? input.label.variable : input.label })
          }
        }
      })
    })
    if (errMsg) {
      Toast.notify({
        message: errMsg,
        type: 'error',
      })
      return
    }

    const submitData: Record<string, any> = {}
    let parseErrorJsonField = ''
    forms.forEach((form) => {
      form.inputs.forEach((input) => {
        try {
          const value = formatValue(form.values[input.variable], input.type)
          submitData[input.variable] = value
        }
        catch {
          parseErrorJsonField = input.variable
        }
      })
    })
    if (parseErrorJsonField) {
      Toast.notify({
        message: t('workflow.errorMsg.invalidJson', { field: parseErrorJsonField }),
        type: 'error',
      })
      return
    }

    onRun(submitData)
  }
  const hasRun = useRef(false)
  useEffect(() => {
    // React 18 run twice in dev mode
    if(hasRun.current)
      return
    hasRun.current = true
    if(filteredExistVarForms.length === 0)
      onRun({})
  }, [filteredExistVarForms, onRun])

  if(filteredExistVarForms.length === 0)
    return null

  return (
    <PanelWrap
      nodeName={nodeName}
      onHide={onHide}
    >
      <div className='h-0 grow overflow-y-auto pb-4'>
        <div className='mt-3 space-y-4 px-4'>
          {filteredExistVarForms.map((form, index) => (
            <div key={index}>
              <Form
                key={index}
                className={cn(index < forms.length - 1 && 'mb-4')}
                {...form}
              />
              {index < forms.length - 1 && <Split />}
            </div>
          ))}
        </div>
        <div className='mt-4 flex justify-between space-x-2 px-4' >
          <Button disabled={!isFileLoaded} variant='primary' className='w-0 grow space-x-2' onClick={handleRun}>
            <div>{t(`${i18nPrefix}.startRun`)}</div>
          </Button>
        </div>
      </div>
    </PanelWrap>
  )
}
export default React.memo(BeforeRunForm)
