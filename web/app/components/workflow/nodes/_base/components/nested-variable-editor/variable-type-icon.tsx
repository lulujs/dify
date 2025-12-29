'use client'
import type { FC } from 'react'
import React from 'react'
import {
  RiAlignLeft,
  RiBracesLine,
  RiCheckboxLine,
  RiFileList2Line,
  RiHashtag,
  RiListCheck2,
  RiTextSnippet,
} from '@remixicon/react'
import { NestedVariableType } from '@/types/workflow/nested-variable'

type Props = {
  className?: string
  type: NestedVariableType
}

const getIcon = (type: NestedVariableType) => {
  const iconMap: Record<NestedVariableType, typeof RiTextSnippet> = {
    [NestedVariableType.STRING]: RiTextSnippet,
    [NestedVariableType.INTEGER]: RiHashtag,
    [NestedVariableType.NUMBER]: RiHashtag,
    [NestedVariableType.BOOLEAN]: RiCheckboxLine,
    [NestedVariableType.OBJECT]: RiBracesLine,
    [NestedVariableType.FILE]: RiFileList2Line,
    [NestedVariableType.ARRAY_STRING]: RiListCheck2,
    [NestedVariableType.ARRAY_INTEGER]: RiListCheck2,
    [NestedVariableType.ARRAY_NUMBER]: RiListCheck2,
    [NestedVariableType.ARRAY_BOOLEAN]: RiListCheck2,
    [NestedVariableType.ARRAY_OBJECT]: RiListCheck2,
    [NestedVariableType.ARRAY_FILE]: RiListCheck2,
  }
  return iconMap[type] || RiAlignLeft
}

const VariableTypeIcon: FC<Props> = ({ className, type }) => {
  const Icon = getIcon(type)
  return <Icon className={className} />
}

export default React.memo(VariableTypeIcon)
