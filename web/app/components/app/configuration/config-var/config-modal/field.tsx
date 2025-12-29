'use client'
import type { FC } from 'react'
import React from 'react'
import cn from '@/utils/classnames'
import { useTranslation } from 'react-i18next'

type Props = {
  className?: string
  title: string
  isOptional?: boolean
  headerAction?: React.ReactNode
  children: React.JSX.Element
}

const Field: FC<Props> = ({
  className,
  title,
  isOptional,
  headerAction,
  children,
}) => {
  const { t } = useTranslation()
  return (
    <div className={cn(className)}>
      <div className='flex items-center justify-between leading-8'>
        <div className='system-sm-semibold text-text-secondary'>
          {title}
          {isOptional && <span className='system-xs-regular ml-1 text-text-tertiary'>({t('appDebug.variableConfig.optional')})</span>}
        </div>
        {headerAction}
      </div>
      <div>{children}</div>
    </div>
  )
}
export default React.memo(Field)
