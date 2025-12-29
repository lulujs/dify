'use client'
import React, { useMemo, useRef, useState } from 'react'
import { useHover } from 'ahooks'
import { ChevronRight } from '@/app/components/base/icons/src/vender/line/arrows'
import {
  PortalToFollowElem,
  PortalToFollowElemContent,
  PortalToFollowElemTrigger,
} from '@/app/components/base/portal-to-follow-elem'
import TreeIndentLine from '../object-child-tree-panel/tree-indent-line'
import cn from '@/utils/classnames'
import type { ValueSelector, Var } from '@/app/components/workflow/types'
import { VarType } from '@/app/components/workflow/types'
import { noop } from 'lodash-es'

const MAX_DEPTH = 10

type Props = {
  valueSelector: ValueSelector
  name: string
  varInfo: Var
  depth?: number
  readonly?: boolean
  onSelect?: (valueSelector: ValueSelector, varInfo: Var) => void
}

type ChildrenPanelProps = {
  parentName: string
  children: Var[]
  valueSelector: ValueSelector
  onHovering: (value: boolean) => void
  onSelect?: (valueSelector: ValueSelector, varInfo: Var) => void
  readonly?: boolean
}

/**
 * NestedVarField - A single field in the nested variable picker tree
 *
 * Renders a variable with its type and allows selection. For object types
 * with children, shows a nested submenu on hover.
 *
 * @see Requirements 4.1, 4.2 - Variable selector nested path support
 */
function NestedVarField({
  valueSelector,
  name,
  varInfo,
  depth = 1,
  readonly,
  onSelect,
}: Props) {
  // Check if this variable has nested children
  const hasChildren = useMemo(() => {
    if (varInfo.type !== VarType.object && varInfo.type !== VarType.file)
      return false
    if (!varInfo.children)
      return false
    // Check if children is Var[] (not StructuredOutput)
    return Array.isArray(varInfo.children) && varInfo.children.length > 0
  }, [varInfo])

  // Get children as Var[]
  const childrenVars = useMemo(() => {
    if (!hasChildren)
      return []
    return varInfo.children as Var[]
  }, [hasChildren, varInfo.children])

  // Hover state management
  const itemRef = useRef<HTMLDivElement>(null)
  const [isItemHovering, setIsItemHovering] = useState(false)
  useHover(itemRef, {
    onChange: (hovering) => {
      if (hovering) {
        setIsItemHovering(true)
      }
      else {
        if (hasChildren)
          setTimeout(() => setIsItemHovering(false), 100)

        else
          setIsItemHovering(false)
      }
    },
  })
  const [isChildrenHovering, setIsChildrenHovering] = useState(false)
  const isHovering = isItemHovering || isChildrenHovering
  const open = hasChildren && isHovering

  // Handle selection
  const handleSelect = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (readonly)
      return
    onSelect?.([...valueSelector, name], varInfo)
  }

  // Don't render if depth exceeds max
  if (depth > MAX_DEPTH + 1)
    return null

  return (
    <PortalToFollowElem open={open} onOpenChange={noop} placement="left-start">
      <PortalToFollowElemTrigger className="w-full">
        <div
          ref={itemRef}
          className={cn(
            hasChildren ? 'pr-1' : 'pr-[18px]',
            isHovering && (hasChildren ? 'bg-components-panel-on-panel-item-bg-hover' : 'bg-state-base-hover'),
            'relative flex h-6 w-full cursor-pointer items-center rounded-md pl-3',
          )}
          onClick={handleSelect}
          onMouseDown={e => e.preventDefault()}
        >
          <div className="flex w-0 grow items-stretch">
            <TreeIndentLine depth={depth} />
            <div
              title={name}
              className="system-sm-medium h-6 w-0 grow truncate leading-6 text-text-secondary"
            >
              {name}
            </div>
          </div>
          <div className="system-xs-regular ml-2 shrink-0 capitalize text-text-tertiary">
            {varInfo.schemaType || varInfo.type}
          </div>
          {hasChildren && (
            <ChevronRight
              className={cn(
                'ml-0.5 h-3 w-3 text-text-quaternary',
                isHovering && 'text-text-tertiary',
              )}
            />
          )}
        </div>
      </PortalToFollowElemTrigger>

      <PortalToFollowElemContent style={{ zIndex: 100 }}>
        {hasChildren && (
          <NestedVarChildrenPanel
            parentName={name}
            children={childrenVars}
            valueSelector={[...valueSelector, name]}
            onHovering={setIsChildrenHovering}
            onSelect={onSelect}
            readonly={readonly}
          />
        )}
      </PortalToFollowElemContent>
    </PortalToFollowElem>
  )
}

/**
 * NestedVarChildrenPanel - Panel showing children of a nested variable
 */
function NestedVarChildrenPanel({
  parentName,
  children,
  valueSelector,
  onHovering,
  onSelect,
  readonly,
}: ChildrenPanelProps) {
  const ref = useRef<HTMLDivElement>(null)
  useHover(ref, {
    onChange: (hovering) => {
      if (hovering)
        onHovering(true)
      else
        setTimeout(() => onHovering(false), 100)
    },
  })

  return (
    <div
      ref={ref}
      className="w-[296px] rounded-xl border-[0.5px] border-components-panel-border bg-components-panel-bg-blur p-1 shadow-lg backdrop-blur-[5px]"
    >
      {/* Header showing parent path */}
      <div className="flex items-center justify-between px-2 py-1">
        <div className="system-sm-medium text-text-secondary">{parentName}</div>
        <div className="system-xs-regular ml-2 text-text-tertiary">object</div>
      </div>

      {/* Child fields */}
      {children.map(child => (
        <NestedVarField
          key={child.variable}
          name={child.variable}
          varInfo={child}
          valueSelector={valueSelector}
          onSelect={onSelect}
          readonly={readonly}
        />
      ))}
    </div>
  )
}

export default React.memo(NestedVarField)
