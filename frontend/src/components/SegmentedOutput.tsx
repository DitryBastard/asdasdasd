import { useState } from 'react'
import type { Segment } from '../types'

function groupByParagraph(segments: Segment[]): Segment[][] {
  const groups: Segment[][] = []
  let current: Segment[] = []
  let currentIndex: number | null = null
  for (const seg of segments) {
    if (currentIndex !== null && seg.paragraph_index !== currentIndex) {
      groups.push(current)
      current = []
    }
    currentIndex = seg.paragraph_index
    current.push(seg)
  }
  if (current.length) groups.push(current)
  return groups
}

export default function SegmentedOutput({ segments }: { segments: Segment[] }) {
  const [activeIndex, setActiveIndex] = useState<number | null>(null)
  const paragraphs = groupByParagraph(segments)
  let globalIndex = -1

  return (
    <div className="segmented-output">
      {paragraphs.map((paragraph, pIdx) => (
        <p key={pIdx} className="output-paragraph">
          {paragraph.map((seg) => {
            globalIndex += 1
            const idx = globalIndex
            const hasWarnings = seg.warnings.length > 0
            const isClickable = Boolean(seg.match) || hasWarnings
            const matchClass = seg.match ? `match-${seg.match.type}` : ''
            const isActive = activeIndex === idx
            return (
              <span key={idx} className="segment-wrap">
                <span
                  className={`segment ${matchClass} ${hasWarnings ? 'segment-warning' : ''} ${isActive ? 'segment-active' : ''}`.trim()}
                  onClick={() => isClickable && setActiveIndex(isActive ? null : idx)}
                >
                  {seg.translation || seg.source}
                </span>{' '}
                {isActive && (seg.match || hasWarnings) && (
                  <span className="match-popover">
                    {hasWarnings && (
                      <span className="qa-warning-block">
                        {seg.warnings.map((warning) => (
                          <span className="qa-warning-row" key={warning}>
                            ⚠ {warning}
                          </span>
                        ))}
                      </span>
                    )}
                    {seg.match && (
                      <>
                        <strong className="match-popover-title">
                          {seg.match.type === 'exact' ? 'Точное совпадение из базы' : 'Похоже на запись из базы'}
                          {' · '}
                          {Math.round(seg.match.similarity * 100)}%
                        </strong>
                        <span className="match-popover-row">
                          <span className="match-label">Оригинал в базе:</span> {seg.match.memory_source}
                        </span>
                        <span className="match-popover-row">
                          <span className="match-label">Перевод в базе:</span> {seg.match.memory_target}
                        </span>
                        {seg.match.document_title && (
                          <span className="match-popover-row match-source-doc">Источник: {seg.match.document_title}</span>
                        )}
                      </>
                    )}
                  </span>
                )}
              </span>
            )
          })}
        </p>
      ))}
    </div>
  )
}
