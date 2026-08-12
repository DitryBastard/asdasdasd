import type { Segment } from '../types'

export default function TranslationReview({
  segments,
  onEdit,
}: {
  segments: Segment[]
  onEdit: (index: number, value: string) => void
}) {
  return (
    <div className="review-table">
      <div className="review-row review-row-header">
        <span>Оригинал</span>
        <span>Перевод (можно исправить)</span>
      </div>
      {segments.map((seg, idx) => (
        <div className="review-row" key={idx}>
          <div className="review-source">{seg.source}</div>
          <div className="review-target-wrap">
            <textarea
              className="review-target"
              value={seg.translation}
              onChange={(e) => onEdit(idx, e.target.value)}
            />
            {(seg.match || seg.warnings.length > 0) && (
              <div className="review-meta">
                {seg.match && (
                  <span className={`review-badge review-badge-${seg.match.type}`}>
                    {seg.match.type === 'exact' ? 'точное совпадение из базы' : `похоже ${Math.round(seg.match.similarity * 100)}% на базу`}
                  </span>
                )}
                {seg.warnings.map((warning) => (
                  <span className="review-badge review-badge-warning" key={warning}>
                    ⚠ {warning}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
