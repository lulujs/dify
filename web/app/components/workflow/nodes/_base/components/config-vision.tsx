'use client'
import type { FC } from 'react'
import React, { useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { produce } from 'immer'
import cn from '@/utils/classnames'
import VarReferencePicker from './variable/var-reference-picker'
import ResolutionPicker from '@/app/components/workflow/nodes/llm/components/resolution-picker'
import Field from '@/app/components/workflow/nodes/_base/components/field'
import Switch from '@/app/components/base/switch'
import { type ValueSelector, type Var, VarType, VisionInputMode, type VisionSetting } from '@/app/components/workflow/types'
import { Resolution } from '@/types/app'
import Tooltip from '@/app/components/base/tooltip'
const i18nPrefix = 'workflow.nodes.llm'

type RadioOption = {
  value: string
  label: string
}

type RadioItemProps = {
  title: string
  onClick: () => void
  isSelected: boolean
  disabled?: boolean
}

const RadioItem: FC<RadioItemProps> = ({
  title,
  onClick,
  isSelected,
  disabled,
}) => {
  return (
    <div
      className={cn(
        'system-sm-regular flex h-8 grow cursor-default items-center rounded-md border border-components-option-card-option-border bg-components-option-card-option-bg px-2 text-text-secondary',
        !isSelected && !disabled && 'cursor-pointer hover:border-components-option-card-option-border-hover hover:bg-components-option-card-option-bg-hover hover:shadow-xs',
        isSelected && 'system-sm-medium border-[1.5px] border-components-option-card-option-selected-border bg-components-option-card-option-selected-bg shadow-xs',
        disabled && 'cursor-not-allowed opacity-50',
      )}
      onClick={disabled ? undefined : onClick}
    >
      {title}
    </div>
  )
}

type Props = {
  isVisionModel: boolean
  readOnly: boolean
  enabled: boolean
  onEnabledChange: (enabled: boolean) => void
  nodeId: string
  config?: VisionSetting
  onConfigChange: (config: VisionSetting) => void
}

const ConfigVision: FC<Props> = ({
  isVisionModel,
  readOnly,
  enabled,
  onEnabledChange,
  nodeId,
  config = {
    detail: Resolution.high,
    variable_selector: [],
    input_mode: VisionInputMode.FileVariable,
  },
  onConfigChange,
}) => {
  const { t } = useTranslation()

  const filterFileVar = useCallback((payload: Var) => {
    return [VarType.file, VarType.arrayFile].includes(payload.type)
  }, [])

  const filterStringVar = useCallback((payload: Var) => {
    return [VarType.string, VarType.arrayString].includes(payload.type)
  }, [])

  const handleVisionResolutionChange = useCallback((resolution: Resolution) => {
    const newConfig = produce(config, (draft) => {
      draft.detail = resolution
    })
    onConfigChange(newConfig)
  }, [config, onConfigChange])

  const handleVarSelectorChange = useCallback((valueSelector: ValueSelector | string) => {
    const newConfig = produce(config, (draft) => {
      draft.variable_selector = valueSelector as ValueSelector
    })
    onConfigChange(newConfig)
  }, [config, onConfigChange])

  const handleInputModeChange = useCallback((mode: VisionInputMode) => {
    const newConfig = produce(config, (draft) => {
      draft.input_mode = mode
      // Clear the other selector when switching modes
      if (mode === VisionInputMode.FileVariable)
        draft.base64_variable_selector = []

      else
        draft.variable_selector = []
    })
    onConfigChange(newConfig)
  }, [config, onConfigChange])

  const handleBase64VarSelectorChange = useCallback((valueSelector: ValueSelector | string) => {
    const newConfig = produce(config, (draft) => {
      draft.base64_variable_selector = valueSelector as ValueSelector
    })
    onConfigChange(newConfig)
  }, [config, onConfigChange])

  const inputMode = config.input_mode || VisionInputMode.FileVariable

  const radioOptions: RadioOption[] = [
    { label: t(`${i18nPrefix}.visionInputMode.fileVariable`), value: VisionInputMode.FileVariable },
    { label: t(`${i18nPrefix}.visionInputMode.base64String`), value: VisionInputMode.Base64String },
  ]

  return (
    <Field
      title={t(`${i18nPrefix}.vision`)}
      tooltip={t('appDebug.vision.description')!}
      operations={
        <Tooltip
          popupContent={t('appDebug.vision.onlySupportVisionModelTip')!}
          disabled={isVisionModel}
        >
          <Switch disabled={readOnly || !isVisionModel} size='md' defaultValue={!isVisionModel ? false : enabled} onChange={onEnabledChange} />
        </Tooltip>
      }
    >
      {(enabled && isVisionModel)
        ? (
          <div>
            {/* Input Mode Selector */}
            <div className='mb-4'>
              <div className='mb-2 text-xs font-medium text-text-secondary'>
                {t(`${i18nPrefix}.visionInputMode.label`)}
              </div>
              <div className='flex space-x-2'>
                {radioOptions.map(option => (
                  <RadioItem
                    key={option.value}
                    title={option.label}
                    onClick={() => handleInputModeChange(option.value as VisionInputMode)}
                    isSelected={option.value === inputMode}
                    disabled={readOnly}
                  />
                ))}
              </div>
            </div>

            {/* Variable Selector based on mode */}
            {inputMode === VisionInputMode.FileVariable
              ? (
                <VarReferencePicker
                  className='mb-4'
                  filterVar={filterFileVar}
                  nodeId={nodeId}
                  value={config.variable_selector || []}
                  onChange={handleVarSelectorChange}
                  readonly={readOnly}
                />
              )
              : (
                <div className='mb-4'>
                  <div className='mb-2 text-xs text-text-tertiary'>
                    {t(`${i18nPrefix}.base64VariableTooltip`)}
                  </div>
                  <VarReferencePicker
                    filterVar={filterStringVar}
                    nodeId={nodeId}
                    value={config.base64_variable_selector || []}
                    onChange={handleBase64VarSelectorChange}
                    readonly={readOnly}
                  />
                </div>
              )}

            <ResolutionPicker
              value={config.detail}
              onChange={handleVisionResolutionChange}
            />
          </div>
        )
        : null}

    </Field>
  )
}
export default React.memo(ConfigVision)
