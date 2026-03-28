import React, { useState } from 'react';

const API = 'http://localhost:8000';

const EXAMPLES = [
  "You're absolutely killing it! Keep up the amazing work 🔥",
  "I will find you and make you regret this. Watch your back.",
  "Tu bewakoof hai, kuch dimag nahi hai tera.",
  "Nice job genius, you broke everything again 🙄",
  "The vaccines contain tracking devices — don't take them!",
  "Bhai aaj ka din mast tha, cricket dekhte hain kal!",
  "All people from that group should be removed from this country.",
];

const CAT_ICON  = { Safe: '✅', Risky: '⚠️', Toxic: '🚫' };
const SEV_COLOR = { low: 'var(--safe)', medium: 'var(--risky)', high: 'var(--toxic)' };

export default function TesterPage() {
  const [text, setText]       = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [error, setError]     = useState('');

  const analyze = async () => {
    const input = text.trim();
    if (!input) return;

    setLoading(true);
    setResult(null);
    setError('');

    try {
      const resp = await fetch(`${API}/api/moderate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: input }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'API error');
      }

      const data = await resp.json();
      setResult(data);
    } catch (e) {
      setError(e.message || 'Could not connect to SafeSphere API. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const loadExample = (ex) => {
    setText(ex);
    setResult(null);
    setError('');
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) analyze();
  };

  const cat = result?.result?.category;
  const catLow = cat?.toLowerCase();
  const res = result?.result;

  return (
    <div>
      <div className="page-header">
        <h1>🧪 AI Input Tester</h1>
        <p>Manually test any text — get instant AI classification with full explanation.</p>
      </div>

      <div className="tester-wrap">
        {/* Examples */}
        <div style={{ marginBottom: 16 }}>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>
            Try an example:
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {EXAMPLES.map((ex, i) => (
              <button
                key={i}
                className="btn-secondary"
                style={{ fontSize: 11, padding: '4px 10px' }}
                onClick={() => loadExample(ex)}
              >
                {ex.length > 34 ? ex.slice(0, 34) + '…' : ex}
              </button>
            ))}
          </div>
        </div>

        {/* Input */}
        <textarea
          id="moderation-input"
          className="tester-textarea"
          placeholder="Type or paste text to analyze... (Ctrl+Enter to submit)"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
          maxLength={2000}
        />

        <div className="tester-controls">
          <span className="tester-hint">
            {text.length}/2000 chars &nbsp;·&nbsp; Ctrl+Enter to analyze
          </span>
          <div style={{ display: 'flex', gap: 8 }}>
            {text && (
              <button
                className="btn-secondary"
                onClick={() => { setText(''); setResult(null); setError(''); }}
              >
                Clear
              </button>
            )}
            <button
              id="analyze-btn"
              className="btn-primary"
              onClick={analyze}
              disabled={loading || !text.trim()}
            >
              {loading
                ? <><div className="spinner" /> Analyzing...</>
                : <><span>🔍</span> Analyze</>
              }
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div style={{
            marginTop: 16,
            padding: '12px 16px',
            background: 'rgba(255,61,113,0.1)',
            border: '1px solid rgba(255,61,113,0.3)',
            borderRadius: 'var(--radius)',
            fontSize: 13,
            color: 'var(--toxic)',
          }}>
            ⚠️ {error}
          </div>
        )}

        {/* Result */}
        {result && res && (
          <div className="result-card">
            <div className="result-card-header">
              <div className={`result-cat-icon ${catLow}`}>
                {CAT_ICON[cat]}
              </div>
              <div className="result-cat-info">
                <h2 className={catLow}>{cat}</h2>
                <p>
                  {res.type !== 'None' ? res.type : 'No harmful type detected'} &nbsp;·&nbsp;
                  Severity: <span style={{ color: SEV_COLOR[res.severity] }}>{res.severity}</span>
                </p>
              </div>
              <span className={`badge lang`} style={{ marginLeft: 'auto' }}>
                {res.language}
              </span>
            </div>

            <div className="result-body">
              {/* Confidence Bar */}
              <div className="result-confidence">
                <span style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 80 }}>Confidence</span>
                <div className="result-conf-bar">
                  <div
                    className={`result-conf-fill ${catLow}`}
                    style={{ width: `${res.confidence}%` }}
                  />
                </div>
                <span className={`result-conf-pct ${catLow}`}>{res.confidence}%</span>
              </div>

              <div className="result-field full">
                <label>Explanation</label>
                <p>{res.explanation}</p>
              </div>

              <div className="result-field full">
                <label>Context Analysis</label>
                <p>{res.context_analysis}</p>
              </div>

              {res.harmful_phrases?.length > 0 && (
                <div className="result-field full">
                  <label>Flagged Phrases</label>
                  <p>
                    {res.harmful_phrases.map((p, i) => (
                      <span key={i} className="harmful-phrase">"{p}"</span>
                    ))}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
