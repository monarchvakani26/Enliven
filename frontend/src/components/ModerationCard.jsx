import React, { useState } from 'react';

const CATEGORY_ICON = { Safe: '✅', Risky: '⚠️', Toxic: '🚫' };
const SEVERITY_MAP  = { low: '🟢', medium: '🟡', high: '🔴' };

export default function ModerationCard({ item, compact = false }) {
  const [expanded, setExpanded] = useState(false);

  if (!item?.result) return null;

  const { result, text, timestamp } = item;
  const cat = (result.category || 'Safe').toLowerCase();
  const conf = Number(result.confidence) || 0;

  const ts = timestamp
    ? new Date(timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';

  return (
    <div className={`mod-card ${cat}`}>
      <div className="mod-card-header">
        <span className="mod-card-text">{text}</span>
        <div className="mod-card-badges">
          <span className={`badge lang`}>{result.language || 'EN'}</span>
          {result.type && result.type !== 'None' && (
            <span className="badge type">{result.type}</span>
          )}
          <span className={`badge ${cat}`}>
            {CATEGORY_ICON[result.category]} {result.category}
          </span>
        </div>
      </div>

      {!compact && (
        <p className="mod-card-explanation">{result.explanation}</p>
      )}

      <div className="mod-card-footer">
        <div className="confidence-bar-wrap">
          <span className="confidence-label">Confidence</span>
          <div className="confidence-bar">
            <div
              className={`confidence-fill ${cat}`}
              style={{ width: `${conf}%` }}
            />
          </div>
          <span className={`confidence-value ${cat}`}>{conf}%</span>
        </div>

        {!compact && (
          <button
            className="expand-toggle"
            onClick={() => setExpanded(e => !e)}
            aria-label="Toggle detail"
          >
            {expanded ? '▲ Less' : '▼ Details'}
          </button>
        )}

        {ts && <span className="mod-timestamp">{ts}</span>}
      </div>

      {expanded && !compact && (
        <div className="mod-card-detail">
          <div className="detail-row">
            <strong>Severity:</strong>
            <span>{SEVERITY_MAP[result.severity] || '—'} {result.severity}</span>
          </div>
          <div className="detail-row">
            <strong>Context:</strong>
            <span>{result.context_analysis || '—'}</span>
          </div>
          {result.harmful_phrases?.length > 0 && (
            <div className="detail-row" style={{ flexWrap: 'wrap' }}>
              <strong>Flagged:</strong>
              <span>
                {result.harmful_phrases.map((p, i) => (
                  <span key={i} className="harmful-phrase">"{p}"</span>
                ))}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
