'use client'
import type { FC } from 'react'
import React, { useCallback } from 'react'
import { useBoolean } from 'ahooks'
import cn from 'classnames'
import { RiLayoutGridLine } from '@remixicon/react'
import { ActionButton } from '@/app/components/base/action-button'
import PromptTemplateModal from './prompt-template-modal'
import type { PromptItem } from '@/app/components/workflow/types'

type Props = {
  className?: string
  onApplyTemplate?: (template: PromptItem[]) => void
  isChatModel?: boolean
}

const PromptTemplateSelector: FC<Props> = ({
  className,
  onApplyTemplate,
  isChatModel,
}) => {
  const [showModal, { setTrue: showModalTrue, setFalse: showModalFalse }] = useBoolean(false)

  const handleApplyTemplate = useCallback((template: PromptItem[]) => {
    onApplyTemplate?.(template)
    showModalFalse()
  }, [onApplyTemplate, showModalFalse])

  return (
    <div className={cn(className)}>
      <ActionButton
        className='hover:bg-[#155EFF]/8'
        onClick={showModalTrue}
      >
        <RiLayoutGridLine className='h-4 w-4 text-primary-600' />
      </ActionButton>
      {showModal && (
        <PromptTemplateModal
          isShow={showModal}
          onClose={showModalFalse}
          onApply={handleApplyTemplate}
          isChatModel={isChatModel}
        />
      )}
    </div>
  )
}

export default React.memo(PromptTemplateSelector)
