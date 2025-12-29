'use client'
import type { FC } from 'react'
import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useContext } from 'use-context-selector'
import { produce } from 'immer'
import {
  RiArrowDownSLine,
  RiArrowRightSLine,
  RiDeleteBinLine,
  RiPlayLargeFill,
} from '@remixicon/react'
import ConfigContext from '@/context/debug-configuration'
import type { Inputs, PromptVariableChild } from '@/models/debug'
import { AppModeEnum, ModelModeType } from '@/types/app'
import Select from '@/app/components/base/select'
import Button from '@/app/components/base/button'
import Input from '@/app/components/base/input'
import Textarea from '@/app/components/base/textarea'
import Tooltip from '@/app/components/base/tooltip'
import TextGenerationImageUploader from '@/app/components/base/image-uploader/text-generation-image-uploader'
import FeatureBar from '@/app/components/base/features/new-feature-panel/feature-bar'
import type { VisionFile, VisionSettings } from '@/types/app'
import { DEFAULT_VALUE_MAX_LEN } from '@/config'
import { useStore as useAppStore } from '@/app/components/app/store'
import cn from '@/utils/classnames'
import BoolInput from '@/app/components/workflow/nodes/_base/components/before-run-form/bool-input'
import NestedObjectInput from '@/app/components/workflow/nodes/_base/components/before-run-form/nested-object-input'
import CodeEditor from '@/app/components/workflow/nodes/_base/components/editor/code-editor'
import { CodeLanguage } from '@/app/components/workflow/nodes/code/types'
import type { InputVarChild } from '@/app/components/workflow/types'
import { InputVarType } from '@/app/components/workflow/types'

export type IPromptValuePanelProps = {
  appType: AppModeEnum
  onSend?: () => void
  inputs: Inputs
  visionConfig: VisionSettings
  onVisionFilesChange: (files: VisionFile[]) => void
}

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

const PromptValuePanel: FC<IPromptValuePanelProps> = ({
  appType,
  onSend,
  inputs,
  visionConfig,
  onVisionFilesChange,
}) => {
  const { t } = useTranslation()
  const { modelModeType, modelConfig, setInputs, mode, isAdvancedMode, completionPromptConfig, chatPromptConfig } = useContext(ConfigContext)
  const [userInputFieldCollapse, setUserInputFieldCollapse] = useState(false)
  const promptVariables = modelConfig.configs.prompt_variables.filter(({ key, name }) => {
    return key && key?.trim() && name && name?.trim()
  })

  const promptVariableObj = useMemo(() => {
    const obj: Record<string, boolean> = {}
    promptVariables.forEach((input) => {
      obj[input.key] = true
    })
    return obj
  }, [promptVariables])

  // Initialize inputs with default values from promptVariables
  useEffect(() => {
    const newInputs = { ...inputs }
    let hasChanges = false

    promptVariables.forEach((variable) => {
      const { key, default: defaultValue } = variable
      // Only set default value if the field is empty and a default exists
      if (defaultValue !== undefined && defaultValue !== null && defaultValue !== '' && (inputs[key] === undefined || inputs[key] === null || inputs[key] === '')) {
        newInputs[key] = defaultValue
        hasChanges = true
      }
    })

    if (hasChanges)
      setInputs(newInputs)
  }, [promptVariables, inputs, setInputs])

  const canNotRun = useMemo(() => {
    if (mode !== AppModeEnum.COMPLETION)
      return true

    if (isAdvancedMode) {
      if (modelModeType === ModelModeType.chat)
        return chatPromptConfig.prompt.every(({ text }) => !text)
      return !completionPromptConfig.prompt?.text
    }

    else { return !modelConfig.configs.prompt_template }
  }, [chatPromptConfig.prompt, completionPromptConfig.prompt?.text, isAdvancedMode, mode, modelConfig.configs.prompt_template, modelModeType])

  const handleInputValueChange = (key: string, value: any) => {
    if (!(key in promptVariableObj))
      return

    const newInputs = { ...inputs }
    promptVariables.forEach((input) => {
      if (input.key === key)
        newInputs[key] = value
    })
    setInputs(newInputs)
  }

  // Array item change handler for array types
  const handleArrayItemChange = useCallback((key: string, index: number, newValue: any) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    const newValues = produce(currentValue as any[], (draft) => {
      while (draft.length <= index)
        draft.push(undefined)
      draft[index] = newValue
    })
    handleInputValueChange(key, newValues)
  }, [inputs, handleInputValueChange])

  // Array item remove handler for array types
  const handleArrayItemRemove = useCallback((key: string, index: number) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    const newValues = produce(currentValue as any[], (draft) => {
      if (index < draft.length)
        draft.splice(index, 1)
    })
    handleInputValueChange(key, newValues)
  }, [inputs, handleInputValueChange])

  // Add new item to array
  const handleArrayItemAdd = useCallback((key: string, defaultValue: any) => {
    const currentValue = Array.isArray(inputs[key]) ? inputs[key] : []
    handleInputValueChange(key, [...currentValue, defaultValue])
  }, [inputs, handleInputValueChange])

  const onClear = () => {
    const newInputs: Inputs = {}
    promptVariables.forEach((item) => {
      newInputs[item.key] = ''
    })
    setInputs(newInputs)
  }

  const setShowAppConfigureFeaturesModal = useAppStore(s => s.setShowAppConfigureFeaturesModal)

  return (
    <>
      <div className='relative z-[1] mx-3 rounded-xl border-[0.5px] border-components-panel-border-subtle bg-components-panel-on-panel-item-bg shadow-md'>
        <div className={cn('px-4 pt-3', userInputFieldCollapse ? 'pb-3' : 'pb-1')}>
          <div className='flex cursor-pointer items-center gap-0.5 py-0.5' onClick={() => setUserInputFieldCollapse(!userInputFieldCollapse)}>
            <div className='system-md-semibold-uppercase text-text-secondary'>{t('appDebug.inputs.userInputField')}</div>
            {userInputFieldCollapse && <RiArrowRightSLine className='h-4 w-4 text-text-secondary'/>}
            {!userInputFieldCollapse && <RiArrowDownSLine className='h-4 w-4 text-text-secondary'/>}
          </div>
          {!userInputFieldCollapse && (
            <div className='system-xs-regular mt-1 text-text-tertiary'>{t('appDebug.inputs.completionVarTip')}</div>
          )}
        </div>
        {!userInputFieldCollapse && promptVariables.length > 0 && (
          <div className='px-4 pb-4 pt-3'>
            {promptVariables.map(({ key, name, type, options, max_length, required, children }, index) => (
              <div
                key={key}
                className='mb-4 last-of-type:mb-0'
              >
                <div>
                  {type !== 'checkbox' && (
                    <div className='system-sm-semibold mb-1 flex h-6 items-center gap-1 text-text-secondary'>
                      <div className='truncate'>{name || key}</div>
                      {!required && <span className='system-xs-regular text-text-tertiary'>{t('workflow.panel.optional')}</span>}
                    </div>
                  )}
                  <div className='grow'>
                    {type === 'string' && (
                      <Input
                        value={inputs[key] ? `${inputs[key]}` : ''}
                        onChange={(e) => { handleInputValueChange(key, e.target.value) }}
                        placeholder={name}
                        autoFocus={index === 0}
                        maxLength={max_length || DEFAULT_VALUE_MAX_LEN}
                      />
                    )}
                    {type === 'paragraph' && (
                      <Textarea
                        className='h-[120px] grow'
                        placeholder={name}
                        value={inputs[key] ? `${inputs[key]}` : ''}
                        onChange={(e) => { handleInputValueChange(key, e.target.value) }}
                      />
                    )}
                    {type === 'select' && (
                      <Select
                        className='w-full'
                        defaultValue={inputs[key] as string}
                        onSelect={(i) => { handleInputValueChange(key, i.value as string) }}
                        items={(options || []).map(i => ({ name: i, value: i }))}
                        allowSearch={false}
                        bgClassName='bg-gray-50'
                      />
                    )}
                    {type === 'number' && (
                      <Input
                        type='number'
                        value={inputs[key] ? `${inputs[key]}` : ''}
                        onChange={(e) => { handleInputValueChange(key, e.target.value) }}
                        placeholder={name}
                        autoFocus={index === 0}
                        maxLength={max_length || DEFAULT_VALUE_MAX_LEN}
                      />
                    )}
                    {type === 'checkbox' && (
                      <BoolInput
                        name={name || key}
                        value={!!inputs[key]}
                        required={required}
                        onChange={(value) => { handleInputValueChange(key, value) }}
                      />
                    )}
                    {/* JSON Object type with children - nested object input */}
                    {type === InputVarType.jsonObject && children && children.length > 0 && (
                      <div className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                        <NestedObjectInput
                          definition={convertToInputVarChild(children)}
                          value={typeof inputs[key] === 'object' && inputs[key] !== null ? inputs[key] as Record<string, unknown> : {}}
                          onChange={(value) => { handleInputValueChange(key, value) }}
                        />
                      </div>
                    )}
                    {/* JSON Object type without children - JSON editor */}
                    {type === InputVarType.jsonObject && (!children || children.length === 0) && (
                      <CodeEditor
                        value={typeof inputs[key] === 'string' ? inputs[key] : (typeof inputs[key] === 'object' ? inputs[key] : '')}
                        language={CodeLanguage.json}
                        onChange={(value) => { handleInputValueChange(key, value) }}
                        noWrapper
                        className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
                      />
                    )}
                    {/* Array[String] type - list of text inputs */}
                    {type === InputVarType.arrayString && (
                      <div className='space-y-2'>
                        {((inputs[key] as string[]) || ['']).map((item: string, idx: number) => (
                          <div key={idx} className='flex items-center gap-2'>
                            <Input
                              value={item || ''}
                              onChange={e => handleArrayItemChange(key, idx, e.target.value)}
                              placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                              className='flex-1'
                            />
                            {((inputs[key] as string[]) || []).length > 1 && (
                              <RiDeleteBinLine
                                onClick={() => handleArrayItemRemove(key, idx)}
                                className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                              />
                            )}
                          </div>
                        ))}
                        <button
                          type='button'
                          onClick={() => handleArrayItemAdd(key, '')}
                          className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                        >
                          + {t('appDebug.variableConfig.addOption')}
                        </button>
                      </div>
                    )}
                    {/* Array[Number] type - list of number inputs */}
                    {type === InputVarType.arrayNumber && (
                      <div className='space-y-2'>
                        {((inputs[key] as number[]) || [0]).map((item: number, idx: number) => (
                          <div key={idx} className='flex items-center gap-2'>
                            <Input
                              type='number'
                              value={item ?? ''}
                              onChange={e => handleArrayItemChange(key, idx, e.target.value ? Number(e.target.value) : 0)}
                              placeholder={`${t('appDebug.variableConfig.content')} ${idx + 1}`}
                              className='flex-1'
                            />
                            {((inputs[key] as number[]) || []).length > 1 && (
                              <RiDeleteBinLine
                                onClick={() => handleArrayItemRemove(key, idx)}
                                className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                              />
                            )}
                          </div>
                        ))}
                        <button
                          type='button'
                          onClick={() => handleArrayItemAdd(key, 0)}
                          className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                        >
                          + {t('appDebug.variableConfig.addOption')}
                        </button>
                      </div>
                    )}
                    {/* Array[Boolean] type - list of boolean toggles */}
                    {type === InputVarType.arrayBoolean && (
                      <div className='space-y-2'>
                        {((inputs[key] as boolean[]) || [false]).map((item: boolean, idx: number) => (
                          <div key={idx} className='flex items-center gap-2'>
                            <BoolInput
                              name={`${name || key} [${idx + 1}]`}
                              value={!!item}
                              required={false}
                              onChange={v => handleArrayItemChange(key, idx, v)}
                            />
                            {((inputs[key] as boolean[]) || []).length > 1 && (
                              <RiDeleteBinLine
                                onClick={() => handleArrayItemRemove(key, idx)}
                                className='h-4 w-4 shrink-0 cursor-pointer text-text-tertiary hover:text-text-secondary'
                              />
                            )}
                          </div>
                        ))}
                        <button
                          type='button'
                          onClick={() => handleArrayItemAdd(key, false)}
                          className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                        >
                          + {t('appDebug.variableConfig.addOption')}
                        </button>
                      </div>
                    )}
                    {/* Array[Object] type with children - list of nested object inputs */}
                    {type === InputVarType.arrayObject && children && children.length > 0 && (
                      <div className='space-y-2'>
                        {((inputs[key] as Record<string, unknown>[]) || [{}]).map((item: Record<string, unknown>, idx: number) => (
                          <div key={idx} className='rounded-lg border border-components-panel-border bg-components-panel-bg p-3'>
                            <div className='mb-2 flex items-center justify-between'>
                              <span className='system-xs-semibold text-text-secondary'>
                                {t('appDebug.variableConfig.content')} {idx + 1}
                              </span>
                              {((inputs[key] as Record<string, unknown>[]) || []).length > 1 && (
                                <RiDeleteBinLine
                                  onClick={() => handleArrayItemRemove(key, idx)}
                                  className='h-4 w-4 cursor-pointer text-text-tertiary hover:text-text-secondary'
                                />
                              )}
                            </div>
                            <NestedObjectInput
                              definition={convertToInputVarChild(children)}
                              value={typeof item === 'object' && item !== null ? item : {}}
                              onChange={v => handleArrayItemChange(key, idx, v)}
                            />
                          </div>
                        ))}
                        <button
                          type='button'
                          onClick={() => handleArrayItemAdd(key, {})}
                          className='system-xs-medium text-text-accent hover:text-text-accent-secondary'
                        >
                          + {t('appDebug.variableConfig.addOption')}
                        </button>
                      </div>
                    )}
                    {/* Array[Object] type without children - JSON array editor */}
                    {type === InputVarType.arrayObject && (!children || children.length === 0) && (
                      <CodeEditor
                        value={typeof inputs[key] === 'string' ? inputs[key] : (typeof inputs[key] === 'object' ? inputs[key] : '')}
                        language={CodeLanguage.json}
                        onChange={(value) => { handleInputValueChange(key, value) }}
                        noWrapper
                        className='h-[120px] overflow-y-auto rounded-[10px] bg-components-input-bg-normal p-1'
                        placeholder={
                          <div className='whitespace-pre'>{'[\n  { }\n]'}</div>
                        }
                      />
                    )}
                  </div>
                </div>
              </div>
            ))}
            {visionConfig?.enabled && (
              <div className="mt-3 justify-between xl:flex">
                <div className="mr-1 w-[120px] shrink-0 py-2 text-sm text-text-primary">{t('common.imageUploader.imageUpload')}</div>
                <div className='grow'>
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
            )}
          </div>
        )}
        {!userInputFieldCollapse && (
          <div className='flex justify-between border-t border-divider-subtle p-4 pt-3'>
            <Button className='w-[72px]' onClick={onClear}>{t('common.operation.clear')}</Button>
            {canNotRun && (
              <Tooltip popupContent={t('appDebug.otherError.promptNoBeEmpty')}>
                <Button
                  variant="primary"
                  disabled={canNotRun}
                  onClick={() => onSend?.()}
                  className="w-[96px]">
                  <RiPlayLargeFill className="mr-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  {t('appDebug.inputs.run')}
                </Button>
              </Tooltip>
            )}
            {!canNotRun && (
              <Button
                variant="primary"
                disabled={canNotRun}
                onClick={() => onSend?.()}
                className="w-[96px]">
                <RiPlayLargeFill className="mr-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                {t('appDebug.inputs.run')}
              </Button>
            )}
          </div>
        )}
      </div>
      <div className='mx-3'>
        <FeatureBar
          showFileUpload={false}
          isChatMode={appType !== AppModeEnum.COMPLETION}
          onFeatureBarClick={setShowAppConfigureFeaturesModal} />
      </div>
    </>
  )
}

export default React.memo(PromptValuePanel)
