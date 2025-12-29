'use client'
import type { FC } from 'react'
import React, { useRef } from 'react'
import { useHover } from 'ahooks'
import NestedVarField from './field'
import cn from '@/utils/classnames'
import type { ValueSelector, Var } from '@/app/components/workflow/types'

type Props = {
  className?: string
  root: {
    nodeId?: string
    nodeName?: string
    attrName: string
    attrAlias?: string
  }
  children: Var[]
  readonly?: boolean
  onSelect?: (valueSelector: ValueSelector, varInfo: Var) => void
  onHovering?: (value: boolean) => void
}

/**
 * NestedVarPickerMain - Main content component for nested variable picker
 *
 * Displays a tree structure of nested variables (Var[]) and allows
 * selecting nested paths. This is used when variables have children
 * defined as Var[] rather than StructuredOutput.
 *
 * @see Requirements 4.1, 4.2 - Variable selector nested path support
 */
export const NestedVarPickerMain: FC<Props> = ({
  className,
  root,
  children,
  readonly,
  onHovering,
  onSelect,
}) => {
  const ref = useRef<HTMLDivElement>(null)
  useHover(ref, {
    onChange: (hovering) => {
      if (hovering)
        onHovering?.(true)
      else
        setTimeout(() => onHovering?.(false), 100)
    },
  })

  return (
    <div className={cn(className)} ref={ref}>
      {/* Root info header */}
      <div className="flex items-center justify-between px-2 py-1">
        <div className="flex">
          {root.nodeName && (
            <>
              <div className="system-sm-medium max-w-[100px] truncate text-text-tertiary">
                {root.nodeName}
              </div>
              <div className="system-sm-medium text-text-tertiary">.</div>
            </>
          )}
          <div className="system-sm-medium text-text-secondary">{root.attrName}</div>
        </div>
        <div
          className="system-xs-regular ml-2 truncate text-text-tertiary"
          title={root.attrAlias || 'object'}
        >
          {root.attrAlias || 'object'}
        </div>
      </div>

      {/* Nested fields */}
      {children.map(child => (
        <NestedVarField
          key={child.variable}
          name={child.variable}
          varInfo={child}
          readonly={readonly}
          valueSelector={[root.nodeId!, root.attrName]}
          onSelect={onSelect}
        />
      ))}
    </div>
  )
}

/**
 * NestedVarPicker - Panel wrapper for nested variable picker
 *
 * Wraps NestedVarPickerMain with panel styling for use in popups.
 */
const NestedVarPicker: FC<Props> = ({ className, ...props }) => {
  return (
    <div
      className={cn(
        'w-[296px] rounded-xl border-[0.5px] border-components-panel-border bg-components-panel-bg-blur p-1 shadow-lg backdrop-blur-[5px]',
        className,
      )}
    >
      <NestedVarPickerMain {...props} />
    </div>
  )
}

export default React.memo(NestedVarPicker)
