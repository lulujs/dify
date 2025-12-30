import type { ChangeEvent, FC, FormEvent } from 'react'
import { useEffect, useState } from 'react'
import React, { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import {
  RiDeleteBinLine,
  RiLoader2Line,
  RiPlayLargeLine,
} from '@remixicon/react'
import { produce } from 'immer'
import Select from '@/app/components/base/select'
import type { SiteInfo } from '@/models/share'
import type { PromptConfig, PromptVariableChild } from '@/models/debug'
import Button from '@/app/components/base/button'
import Textarea from '@/app/components/base/textarea'
import Input from '@/app/components/base/input'
import { DEFAULT_VALUE_MAX_LEN } from '@/config'
import TextGenerationImageUploader from '@/app/components/base/image-uploader/text-generation-image-uploader'
import type { VisionFile, VisionSettings } from '@/types/app'
import { FileUploaderInAttachmentWrapper } from '@/app/components/base/file-uploader'
import useBreakpoints, { MediaType } from '@/hooks/use-breakpoints'
import cn from '@/utils/classnames'
import BoolInput from '@/app/components/workflow/nodes/_base/components/before-run-form/bool-input'
import NestedObjectInput from '@/app/components/workflow/nodes/_base/components/before-run-form/nested-object-input'
import CodeEditor from '@/app/components/workflow/nodes/_base/components/editor/code-editor'
import { CodeLanguage } from '@/app/components/workflow/nodes/code/types'
import { StopCircle } from '@/app/components/base/icons/src/vender/solid/mediaAndDevices'
import type { InputVarChild } from '@/app/components/workflow/types'
import { InputVarType } from '@/app/components/workflow/types'

/**
 * Converts PromptVariableChild to InputVarChild for NestedObjectInput compatibility
 */
const convertToInputVarChild = (children: PromptVariableChild[] | undefined): InputVarChild[] => {
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

export type IRunOnceProps = {
  siteInfo: SiteInfo
  promptConfig: PromptConfig
  inputs: Record<string, any>
  inputsRef: React.RefObject<Record<string, any>>
  onInputsChange: (inputs: Record<string, any>) => void
  onSend: () => void
  visionConfig: VisionSettings
  onVisionFilesChange: (files: VisionFile[]) => void
  runControl?: {
    onStop: () => Promise<void> | void
    isStopping: boolean
  } | null
}
const RunOnce: FC<IRunOnceProps> = ({
  promptConfig,
  inputs,
  inputsRef,
  onInputsChange,
  onSend,
  visionConfig,
  onVisionFilesChange,
  runControl,
}) => {
  const { t } = useTranslation()
  const media = useBreakpoints()
  const isPC = media === MediaType.pc
  const [isInitialized, setIsInitialized] = useState(false)

  const onClear = () => {
    const newInputs: Record<string, any> = {}
    promptConfig.prompt_variables.forEach((item) => {
      if (item.type === 'string' || item.type === 'paragraph')
        newInputs[item.key] = ''
      else if (item.type === 'checkbox')
        newInputs[item.key] = false
      else if (item.type === InputVarType.arrayString)
        newInputs[item.key] = ['']
      else if (item.type === InputVarType.arrayNumber)
        newInputs[item.key] = [0]
      else if (item.type === InputVarType.arrayBoolean)
        newInputs[item.key] = [false]
      else if (item.type === InputVarType.arrayObject)
        newInputs[item.key] = [{}]
      else if (item.type === InputVarType.object)
        newInputs[item.key] = {}
      else
        newInputs[item.key] = undefined
    })
    onInputsChange(newInputs)
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    onSend()
  }
  const isRunning = !!runControl
  const stopLabel = t('share.generation.stopRun', { defaultValue: 'Stop Run' })
  const handlePrimaryClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (!isRunning)
      return
    e.preventDefault()
    runControl?.onStop?.()
  }, [isRunning, runControl])

  const handleInputsChange = useCallback((newInputs: Record<string, any>) => {
    onInputsChange(newInputs)
    inputsRef.current = newInputs
  }, [onInputsChange, inputsRef])

  // Array item change handler for array types
  const handleArrayItemChange = useCallback((key: string, index: number, newValue: any) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    const newValues = produce(currentValue as any[], (draft) => {
      while (draft.length <= index)
        draft.push(undefined)
      draft[index] = newValue
    })
    handleInputsChange({ ...inputsRef.current, [key]: newValues })
  }, [inputs, handleInputsChange, inputsRef])

  // Array item remove handler for array types
  const handleArrayItemRemove = useCallback((key: string, index: number) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    const newValues = produce(currentValue as any[], (draft) => {
      if (index < draft.length)
        draft.splice(index, 1)
    })
    handleInputsChange({ ...inputsRef.current, [key]: newValues })
  }, [inputs, handleInputsChange, inputsRef])

  // Add new item to array
  const handleArrayItemAdd = useCallback((key: string, defaultValue: any) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    handleInputsChange({ ...inputsRef.current, [key]: [...currentValue, defaultValue] })
  }, [inputs, handleInputsChange, inputsRef])

  useEffect(() => {
    if (isInitialized) return
    const newInputs: Record<string, any> = {}
    promptConfig.prompt_variables.forEach((item) => {
      if (item.type === 'select')
        newInputs[item.key] = item.default
      else if (item.type === 'string' || item.type === 'paragraph')
        newInputs[item.key] = item.default || ''
      else if (item.type === 'number')
        newInputs[item.key] = item.default
      else if (item.type === 'checkbox')
        newInputs[item.key] = item.default || false
      else if (item.type === 'file')
        newInputs[item.key] = undefined
      else if (item.type === 'file-list')
        newInputs[item.key] = []
      else if (item.type === InputVarType.arrayString)
        newInputs[item.key] = ['']
      else if (item.type === InputVarType.arrayNumber)
        newInputs[item.key] = [0]
      else if (item.type === InputVarType.arrayBoolean)
        newInputs[item.key] = [false]
      else if (item.type === InputVarType.arrayObject)
        newInputs[item.key] = [{}]
      else if (item.type === InputVarType.object)
        newInputs[item.key] = {}
      else
        newInputs[item.key] = undefined
    })
    onInputsChange(newInputs)
    setIsInitialized(true)
  }, [promptConfig.prompt_variables, onInputsChange])

  return (
    <div className="">
      <section>
        {/* input form */}
        <form onSubmit={onSubmit}>
          {(inputs === null || inputs === undefined || Object.keys(inputs).length === 0) || !isInitialized ? null
            : promptConfig.prompt_variables.filter(item => item.hide !== true).map(item => (
              <div className='mt-4 w-full' key={item.key}>
                {item.type !== 'checkbox' && (
                  <div className='system-md-semibold flex h-6 items-center gap-1 text-text-secondary'>
                    <div className='truncate'>{item.name}</div>
                    {!item.required && <span className='system-xs-regular text-text-tertiary'>{t('workflow.panel.optional')}</span>}
                  </div>
                )}
                <div className='mt-1'>
                  {item.type === 'select' && (
                    <Select
                      className='w-full'
                      defaultValue={inputs[item.key]}
                      onSelect={(i) => { handleInputsChange({ ...inputsRef.current, [item.key]: i.value }) }}
                      items={(item.options || []).map(i => ({ name: i, value: i }))}
                      allowSearch={false}
                    />
                  )}
                  {item.type === 'string' && (
                    <Input
                      type="text"
                      placeholder={item.name}
                      value={inputs[item.key]}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => { handleInputsChange({ ...inputsRef.current, [item.key]: e.target.value }) }}
                      maxLength={item.max_length || DEFAULT_VALUE_MAX_LEN}
                    />
                  )}
                  {item.type === 'paragraph' && (
                    <Textarea
                      className='h-[104px] sm:text-xs'
                      placeholder={item.name}
                      value={inputs[item.key]}
                      onChange={(e: ChangeEvent<HTMLTextAreaElement>) => { handleInputsChange({ ...inputsRef.current, [item.key]: e.target.value }) }}
                    />
                  )}
                  {item.type === 'number' && (
                    <Input
                      type="number"
                      placeholder={item.name}
                      value={inputs[item.key]}
                      onChange={(e: ChangeEvent<HTMLInputElement>) => { handleInputsChange({ ...inputsRef.current, [item.key]: e.target.value }) }}
                    />
                  )}
                  {item.type === 'checkbox' && (
                    <BoolInput
                      name={item.name || item.key}
                      value={!!inputs[item.key]}
                      required={item.required}
                      onChange={(value) => { handleInputsChange({ ...inputsRef.current, [item.key]: value }) }}
                    />
                  )}
                  {item.type === 'file' && (
                    <FileUploaderInAttachmentWrapper
                      value={(inputs[item.key] && typeof inputs[item.key] === 'object') ? [inputs[item.key]] : []}
                      onChange={(files) => { handleInputsChange({ ...inputsRef.current, [item.key]: files[0] }) }}
                      fileConfig={{
                        ...item.config,
                        fileUploadConfig: (visionConfig as any).fileUploadConfig,
                      }}
                    />
                  )}
                  {item.type === 'file-list' && (
                    <FileUploaderInAttachmentWrapper
                      value={Array.isArray(inputs[item.key]) ? inputs[item.key] : []}
                      onChange={(files) => { handleInputsChange({ ...inputsRef.current, [item.key]: files }) }}
                      fileConfig={{
                        ...item.config,
                        fileUploadConfig: (visionConfig as any).fileUploadConfig,
                      }}
                    />
                  )}
                  {/* JSON Object type with children - nested object input */}
                  {item.type === InputVarType.object && item.children && item.children.length > 0 && (
                    <div className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                      <NestedObjectInput
                        definition={convertToInputVarChild(item.children)}
                        value={typeof inputs[item.key] === 'object' && inputs[item.key] !== null ? inputs[item.key] as Record<string, unknown> : {}}
                        onChange={(value) => { handleInputsChange({ ...inputsRef.current, [item.key]: value }) }}
                      />
                    </div>
                  )}
                  {/* JSON Object type without children - JSON editor */}
                  {item.type === InputVarType.object && (!item.children || item.children.length === 0) && (
                    <CodeEditor
                      language={CodeLanguage.json}
                      value={inputs[item.key]}
                      onChange={(value) => { handleInputsChange({ ...inputsRef.current, [item.key]: value }) }}
                      noWrapper
                      className='h-[80px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
                      placeholder={
                        <div className='whitespace-pre'>{item.json_schema}</div>
                      }
                    />
                  )}
                  {/* Array[String] type - list of text inputs */}
                  {item.type === InputVarType.arrayString && (
                    <div className='space-y-2'>
                      {((inputs[item.key] as string[]) || ['']).map((arrayItem: string, idx: number) => (
                        <div key={idx} className='flex items-center gap-2'>
                          <Input
                            value={arrayItem || ''}
                            onChange={e => handleArrayItemChange(item.key, idx, e.target.value)}
                            placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                            className='flex-1'
                          />
                          {((inputs[item.key] as string[]) || []).length > 1 && (
                            <RiDeleteBinLine
                              onClick={() => handleArrayItemRemove(item.key, idx)}
                              className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                            />
                          )}
                        </div>
                      ))}
                      <button
                        type='button'
                        onClick={() => handleArrayItemAdd(item.key, '')}
                        className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                      >
                        + {t('appDebug.variableConfig.addOption')}
                      </button>
                    </div>
                  )}
                  {/* Array[Number] type - list of number inputs */}
                  {item.type === InputVarType.arrayNumber && (
                    <div className='space-y-2'>
                      {((inputs[item.key] as number[]) || [0]).map((arrayItem: number, idx: number) => (
                        <div key={idx} className='flex items-center gap-2'>
                          <Input
                            type='number'
                            value={arrayItem ?? ''}
                            onChange={e => handleArrayItemChange(item.key, idx, e.target.value ? Number(e.target.value) : 0)}
                            placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                            className='flex-1'
                          />
                          {((inputs[item.key] as number[]) || []).length > 1 && (
                            <RiDeleteBinLine
                              onClick={() => handleArrayItemRemove(item.key, idx)}
                              className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                            />
                          )}
                        </div>
                      ))}
                      <button
                        type='button'
                        onClick={() => handleArrayItemAdd(item.key, 0)}
                        className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                      >
                        + {t('appDebug.variableConfig.addOption')}
                      </button>
                    </div>
                  )}
                  {/* Array[Boolean] type - list of boolean toggles */}
                  {item.type === InputVarType.arrayBoolean && (
                    <div className='space-y-2'>
                      {((inputs[item.key] as boolean[]) || [false]).map((arrayItem: boolean, idx: number) => (
                        <div key={idx} className='flex items-center gap-2'>
                          <BoolInput
                            name={`${item.name || item.key} [${idx + 1}]`}
                            value={!!arrayItem}
                            required={false}
                            onChange={v => handleArrayItemChange(item.key, idx, v)}
                          />
                          {((inputs[item.key] as boolean[]) || []).length > 1 && (
                            <RiDeleteBinLine
                              onClick={() => handleArrayItemRemove(item.key, idx)}
                              className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                            />
                          )}
                        </div>
                      ))}
                      <button
                        type='button'
                        onClick={() => handleArrayItemAdd(item.key, false)}
                        className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                      >
                        + {t('appDebug.variableConfig.addOption')}
                      </button>
                    </div>
                  )}
                  {/* Array[Object] type with children - list of nested object inputs */}
                  {item.type === InputVarType.arrayObject && item.children && item.children.length > 0 && (
                    <div className='space-y-2'>
                      {((inputs[item.key] as Record<string, unknown>[]) || [{}]).map((arrayItem: Record<string, unknown>, idx: number) => (
                        <div key={idx} className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                          <div className='mb-2 flex items-center justify-between'>
                            <span className='system-xs-semibold text-text-secondary'>
                              {t('appDebug.variableConfig.content')} {idx + 1}
                            </span>
                            {((inputs[item.key] as Record<string, unknown>[]) || []).length > 1 && (
                              <RiDeleteBinLine
                                onClick={() => handleArrayItemRemove(item.key, idx)}
                                className='h-4 w-4 cursor-pointer text-text-tertiary hover:text-text-secondary'
                              />
                            )}
                          </div>
                          <NestedObjectInput
                            definition={convertToInputVarChild(item.children)}
                            value={typeof arrayItem === 'object' && arrayItem !== null ? arrayItem : {}}
                            onChange={v => handleArrayItemChange(item.key, idx, v)}
                          />
                        </div>
                      ))}
                      <button
                        type='button'
                        onClick={() => handleArrayItemAdd(item.key, {})}
                        className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                      >
                        + {t('appDebug.variableConfig.addOption')}
                      </button>
                    </div>
                  )}
                  {/* Array[Object] type without children - JSON array editor */}
                  {item.type === InputVarType.arrayObject && (!item.children || item.children.length === 0) && (
                    <CodeEditor
                      value={typeof inputs[item.key] === 'string' ? inputs[item.key] : (typeof inputs[item.key] === 'object' ? inputs[item.key] : '')}
                      language={CodeLanguage.json}
                      onChange={(value) => { handleInputsChange({ ...inputsRef.current, [item.key]: value }) }}
                      noWrapper
                      className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
                      placeholder={
                        <div className='whitespace-pre'>{'[\n  { }\n]'}</div>
                      }
                    />
                  )}
                </div>
              </div>
            ))}
          {
            visionConfig?.enabled && (
              <div className="mt-4 w-full">
                <div className="system-md-semibold flex h-6 items-center text-text-secondary">{t('common.imageUploader.imageUpload')}</div>
                <div className='mt-1'>
                  <TextGenerationImageUploader
                    settings={visionConfig}
                    onFilesChange={files => onVisionFilesChange(files.filter(file => file.progress !== -1).map(fileItem => ({
                      type: 'image',
                      transfer_method: fileItem.type,
                      url: fileItem.url,
                      upload_file_id: fileItem.fileId,
                    })))}
                  />
                </div>
              </div>
            )
          }
          <div className='mb-3 mt-6 w-full'>
            <div className="flex items-center justify-between gap-2">
              <Button
                onClick={onClear}
                disabled={false}
              >
                <span className='text-[13px]'>{t('common.operation.clear')}</span>
              </Button>
              <Button
                className={cn(!isPC && 'grow')}
                type={isRunning ? 'button' : 'submit'}
                variant={isRunning ? 'secondary' : 'primary'}
                disabled={isRunning && runControl?.isStopping}
                onClick={handlePrimaryClick}
              >
                {isRunning ? (
                  <>
                    {runControl?.isStopping
                      ? <RiLoader2Line className='mr-1 h-4 w-4 shrink-0 animate-spin' aria-hidden="true" />
                      : <StopCircle className='mr-1 h-4 w-4 shrink-0' aria-hidden="true" />
                    }
                    <span className='text-[13px]'>{stopLabel}</span>
                  </>
                ) : (
                  <>
                    <RiPlayLargeLine className="mr-1 h-4 w-4 shrink-0" aria-hidden="true" />
                    <span className='text-[13px]'>{t('share.generation.run')}</span>
                  </>
                )}
              </Button>
            </div>
          </div>
        </form>
      </section>
    </div>
  )
}
export default React.memo(RunOnce)
