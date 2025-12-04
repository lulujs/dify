'use client'
import type { FC } from 'react'
import React from 'react'
import { useTranslation } from 'react-i18next'
import {
  RiLayoutGridLine,
} from '@remixicon/react'
import Button from '@/app/components/base/button'

export type IPromptTemplateBtnProps = {
  onClick: () => void
}

const PromptTemplateBtn: FC<IPromptTemplateBtnProps> = ({
  onClick,
}) => {
  const { t } = useTranslation()

  return (
    <Button variant='secondary' size='small' onClick={onClick}>
      <RiLayoutGridLine className='mr-1 h-3.5 w-3.5' />
      <span className=''>{t('appDebug.operation.promptTemplate')}</span>
    </Button>
  )
}

export default React.memo(PromptTemplateBtn)
