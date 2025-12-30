import React, { memo, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { RiDeleteBinLine } from '@remixicon/react'
import { produce } from 'immer'
import { useEmbeddedChatbotContext } from '../context'
import Input from '@/app/components/base/input'
import Textarea from '@/app/components/base/textarea'
import { PortalSelect } from '@/app/components/base/select'
import { FileUploaderInAttachmentWrapper } from '@/app/components/base/file-uploader'
import type { InputVarChild } from '@/app/components/workflow/types'
import { InputVarType } from '@/app/components/workflow/types'
import BoolInput from '@/app/components/workflow/nodes/_base/components/before-run-form/bool-input'
import NestedObjectInput from '@/app/components/workflow/nodes/_base/components/before-run-form/nested-object-input'
import { CodeLanguage } from '@/app/components/workflow/nodes/code/types'
import CodeEditor from '@/app/components/workflow/nodes/_base/components/editor/code-editor'

/**
 * Converts form children to InputVarChild for NestedObjectInput compatibility
 */
const convertToInputVarChild = (children: any[] | undefined): InputVarChild[] => {
  if (!children || children.length === 0)
    return []

  return children.map((child): InputVarChild => ({
    variable: child.variable,
    type: child.type as InputVarType,
    required: child.required,
    description: child.description,
    default: child.default,
    children: convertToInputVarChild(child.children),
  }))
}

type Props = {
  showTip?: boolean
}

const InputsFormContent = ({ showTip }: Props) => {
  const { t } = useTranslation()
  const {
    appParams,
    inputsForms,
    currentConversationId,
    currentConversationInputs,
    setCurrentConversationInputs,
    newConversationInputs,
    newConversationInputsRef,
    handleNewConversationInputsChange,
  } = useEmbeddedChatbotContext()
  const inputsFormValue = currentConversationId ? currentConversationInputs : newConversationInputs

  const handleFormChange = useCallback((variable: string, value: any) => {
    setCurrentConversationInputs({
      ...currentConversationInputs,
      [variable]: value,
    })
    handleNewConversationInputsChange({
      ...newConversationInputsRef.current,
      [variable]: value,
    })
  }, [newConversationInputsRef, handleNewConversationInputsChange, currentConversationInputs, setCurrentConversationInputs])

  // Array item change handler for array types
  const handleArrayItemChange = useCallback((variable: string, index: number, newValue: any) => {
    const currentValue = Array.isArray(inputsFormValue?.[variable]) ? inputsFormValue[variable] : []
    const newValues = produce(currentValue as any[], (draft) => {
      while (draft.length <= index)
        draft.push(undefined)
      draft[index] = newValue
    })
    handleFormChange(variable, newValues)
  }, [inputsFormValue, handleFormChange])

  // Array item remove handler for array types
  const handleArrayItemRemove = useCallback((variable: string, index: number) => {
    const currentValue = Array.isArray(inputsFormValue?.[variable]) ? inputsFormValue[variable] : []
    const newValues = produce(currentValue as any[], (draft) => {
      if (index < draft.length)
        draft.splice(index, 1)
    })
    handleFormChange(variable, newValues)
  }, [inputsFormValue, handleFormChange])

  // Add new item to array
  const handleArrayItemAdd = useCallback((variable: string, defaultValue: any) => {
    const currentValue = Array.isArray(inputsFormValue?.[variable]) ? inputsFormValue[variable] : []
    handleFormChange(variable, [...currentValue, defaultValue])
  }, [inputsFormValue, handleFormChange])

  const visibleInputsForms = inputsForms.filter(form => form.hide !== true)

  return (
    <div className='space-y-4'>
      {visibleInputsForms.map(form => (
        <div key={form.variable} className='space-y-1'>
          {form.type !== InputVarType.checkbox && (
            <div className='flex h-6 items-center gap-1'>
              <div className='system-md-semibold text-text-secondary'>{form.label}</div>
              {!form.required && (
                <div className='system-xs-regular text-text-tertiary'>{t('workflow.panel.optional')}</div>
              )}
            </div>
          )}
          {form.type === InputVarType.textInput && (
            <Input
              value={inputsFormValue?.[form.variable] || ''}
              onChange={e => handleFormChange(form.variable, e.target.value)}
              placeholder={form.label}
            />
          )}
          {form.type === InputVarType.number && (
            <Input
              type='number'
              value={inputsFormValue?.[form.variable] || ''}
              onChange={e => handleFormChange(form.variable, e.target.value)}
              placeholder={form.label}
            />
          )}
          {form.type === InputVarType.paragraph && (
            <Textarea
              value={inputsFormValue?.[form.variable] || ''}
              onChange={e => handleFormChange(form.variable, e.target.value)}
              placeholder={form.label}
            />
          )}
          {form.type === InputVarType.checkbox && (
            <BoolInput
              name={form.label}
              value={inputsFormValue?.[form.variable]}
              required={form.required}
              onChange={value => handleFormChange(form.variable, value)}
            />
          )}
          {form.type === InputVarType.select && (
            <PortalSelect
              popupClassName='w-[200px]'
              value={inputsFormValue?.[form.variable] ?? form.default ?? ''}
              items={form.options.map((option: string) => ({ value: option, name: option }))}
              onSelect={item => handleFormChange(form.variable, item.value as string)}
              placeholder={form.label}
            />
          )}
          {form.type === InputVarType.singleFile && (
            <FileUploaderInAttachmentWrapper
              value={inputsFormValue?.[form.variable] ? [inputsFormValue?.[form.variable]] : []}
              onChange={files => handleFormChange(form.variable, files[0])}
              fileConfig={{
                allowed_file_types: form.allowed_file_types,
                allowed_file_extensions: form.allowed_file_extensions,
                allowed_file_upload_methods: form.allowed_file_upload_methods,
                number_limits: 1,
                fileUploadConfig: (appParams as any).system_parameters,
              }}
            />
          )}
          {form.type === InputVarType.multiFiles && (
            <FileUploaderInAttachmentWrapper
              value={inputsFormValue?.[form.variable] || []}
              onChange={files => handleFormChange(form.variable, files)}
              fileConfig={{
                allowed_file_types: form.allowed_file_types,
                allowed_file_extensions: form.allowed_file_extensions,
                allowed_file_upload_methods: form.allowed_file_upload_methods,
                number_limits: form.max_length,
                fileUploadConfig: (appParams as any).system_parameters,
              }}
            />
          )}
          {/* JSON Object type with children - nested object input */}
          {form.type === InputVarType.object && form.children && form.children.length > 0 && (
            <div className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
              <NestedObjectInput
                definition={convertToInputVarChild(form.children)}
                value={typeof inputsFormValue?.[form.variable] === 'object' && inputsFormValue?.[form.variable] !== null ? inputsFormValue[form.variable] as Record<string, unknown> : {}}
                onChange={value => handleFormChange(form.variable, value)}
              />
            </div>
          )}
          {/* JSON Object type without children - JSON editor */}
          {form.type === InputVarType.object && (!form.children || form.children.length === 0) && (
            <CodeEditor
              language={CodeLanguage.json}
              value={inputsFormValue?.[form.variable] || ''}
              onChange={v => handleFormChange(form.variable, v)}
              noWrapper
              className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={
                <div className='whitespace-pre'>{form.json_schema}</div>
              }
            />
          )}
          {/* Array[String] type - list of text inputs */}
          {form.type === InputVarType.arrayString && (
            <div className='space-y-2'>
              {((inputsFormValue?.[form.variable] as string[]) || ['']).map((item: string, idx: number) => (
                <div key={idx} className='flex items-center gap-2'>
                  <Input
                    value={item || ''}
                    onChange={e => handleArrayItemChange(form.variable, idx, e.target.value)}
                    placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                    className='flex-1'
                  />
                  {((inputsFormValue?.[form.variable] as string[]) || []).length > 1 && (
                    <RiDeleteBinLine
                      onClick={() => handleArrayItemRemove(form.variable, idx)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleArrayItemAdd(form.variable, '')}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {/* Array[Number] type - list of number inputs */}
          {form.type === InputVarType.arrayNumber && (
            <div className='space-y-2'>
              {((inputsFormValue?.[form.variable] as number[]) || [0]).map((item: number, idx: number) => (
                <div key={idx} className='flex items-center gap-2'>
                  <Input
                    type='number'
                    value={item ?? ''}
                    onChange={e => handleArrayItemChange(form.variable, idx, e.target.value ? Number(e.target.value) : 0)}
                    placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                    className='flex-1'
                  />
                  {((inputsFormValue?.[form.variable] as number[]) || []).length > 1 && (
                    <RiDeleteBinLine
                      onClick={() => handleArrayItemRemove(form.variable, idx)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleArrayItemAdd(form.variable, 0)}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {/* Array[Boolean] type - list of boolean toggles */}
          {form.type === InputVarType.arrayBoolean && (
            <div className='space-y-2'>
              {((inputsFormValue?.[form.variable] as boolean[]) || [false]).map((item: boolean, idx: number) => (
                <div key={idx} className='flex items-center gap-2'>
                  <BoolInput
                    name={`${form.label} [${idx + 1}]`}
                    value={!!item}
                    required={false}
                    onChange={v => handleArrayItemChange(form.variable, idx, v)}
                  />
                  {((inputsFormValue?.[form.variable] as boolean[]) || []).length > 1 && (
                    <RiDeleteBinLine
                      onClick={() => handleArrayItemRemove(form.variable, idx)}
                      className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                    />
                  )}
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleArrayItemAdd(form.variable, false)}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {/* Array[Object] type with children - list of nested object inputs */}
          {form.type === InputVarType.arrayObject && form.children && form.children.length > 0 && (
            <div className='space-y-2'>
              {((inputsFormValue?.[form.variable] as Record<string, unknown>[]) || [{}]).map((item: Record<string, unknown>, idx: number) => (
                <div key={idx} className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                  <div className='mb-2 flex items-center justify-between'>
                    <span className='system-xs-semibold text-text-secondary'>
                      {t('appDebug.variableConfig.content')} {idx + 1}
                    </span>
                    {((inputsFormValue?.[form.variable] as Record<string, unknown>[]) || []).length > 1 && (
                      <RiDeleteBinLine
                        onClick={() => handleArrayItemRemove(form.variable, idx)}
                        className='h-4 w-4 cursor-pointer text-text-tertiary hover:text-text-secondary'
                      />
                    )}
                  </div>
                  <NestedObjectInput
                    definition={convertToInputVarChild(form.children)}
                    value={typeof item === 'object' && item !== null ? item : {}}
                    onChange={v => handleArrayItemChange(form.variable, idx, v)}
                  />
                </div>
              ))}
              <button
                type='button'
                onClick={() => handleArrayItemAdd(form.variable, {})}
                className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
              >
                + {t('appDebug.variableConfig.addOption')}
              </button>
            </div>
          )}
          {/* Array[Object] type without children - JSON array editor */}
          {form.type === InputVarType.arrayObject && (!form.children || form.children.length === 0) && (
            <CodeEditor
              value={typeof inputsFormValue?.[form.variable] === 'string' ? inputsFormValue[form.variable] : (typeof inputsFormValue?.[form.variable] === 'object' ? inputsFormValue[form.variable] : '')}
              language={CodeLanguage.json}
              onChange={v => handleFormChange(form.variable, v)}
              noWrapper
              className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
              placeholder={
                <div className='whitespace-pre'>{'[\n  { }\n]'}</div>
              }
            />
          )}
        </div>
      ))}
      {showTip && (
        <div className='system-xs-regular text-text-tertiary'>{t('share.chat.chatFormTip')}</div>
      )}
    </div>
  )
}

export default memo(InputsFormContent)
