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

          {/* 3-Layer Pipeline breakdown */}
          {result.layers && (
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text-muted)', marginBottom: 8 }}>
                🤖 AI Layer Breakdown
              </div>
              <div style={{ display: 'flex', gap: 10 }}>
                {/* ML Layer */}
                {result.layers.ml && (
                  <div style={{ flex: 1, background: 'rgba(108,99,255,0.12)', borderRadius: 8, padding: '8px 10px', border: '1px solid rgba(108,99,255,0.25)' }}>
                    <div style={{ fontSize: 10, color: '#6c63ff', marginBottom: 4, fontWeight: 600 }}>LAYER 1 · ML MODEL</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {result.layers.ml.category} <span style={{ color: '#6c63ff' }}>{result.layers.ml.confidence}%</span>
                    </div>
                    {result.layers.ml.probabilities && (
                      <div style={{ marginTop: 4 }}>
                        {Object.entries(result.layers.ml.probabilities).map(([cls, prob]) => (
                          <div key={cls} style={{ fontSize: 10, color: 'var(--text-muted)', display: 'flex', justifyContent: 'space-between' }}>
                            <span>{cls}</span><span>{(prob * 100).toFixed(0)}%</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                {/* Gemini Layer */}
                {result.layers.gemini && (
                  <div style={{ flex: 1, background: 'rgba(0,214,143,0.08)', borderRadius: 8, padding: '8px 10px', border: '1px solid rgba(0,214,143,0.2)' }}>
                    <div style={{ fontSize: 10, color: 'var(--safe)', marginBottom: 4, fontWeight: 600 }}>LAYER 2 · GEMINI 2.0</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                      {result.layers.gemini.category} <span style={{ color: 'var(--safe)' }}>{result.layers.gemini.confidence}%</span>
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>Contextual + Multilingual</div>
                  </div>
                )}
                {/* Fusion */}
                <div style={{ flex: 1, background: 'rgba(255,170,0,0.08)', borderRadius: 8, padding: '8px 10px', border: '1px solid rgba(255,170,0,0.2)' }}>
                  <div style={{ fontSize: 10, color: 'var(--risky)', marginBottom: 4, fontWeight: 600 }}>LAYER 3 · FUSED</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>
                    {result.category} <span style={{ color: 'var(--risky)' }}>{result.confidence}%</span>
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4 }}>Gemini 70% · ML 30%</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
