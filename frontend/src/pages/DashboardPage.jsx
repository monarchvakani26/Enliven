import React, { useEffect, useState, useCallback } from 'react';
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title,
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const API = 'http://localhost:8000';

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { labels: { color: '#8892b0', font: { size: 12 } } },
  },
};

export default function DashboardPage() {
  const [stats, setStats]     = useState(null);
  const [recent, setRecent]   = useState([]);
  const [mlMeta, setMlMeta]   = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [s, r, ml] = await Promise.all([
        fetch(`${API}/api/stats`).then(r => r.json()),
        fetch(`${API}/api/recent?n=15&flagged_only=false`).then(r => r.json()),
        fetch(`${API}/api/ml-metrics`).then(r => r.json()),
      ]);
      setStats(s);
      setRecent(r.logs || []);
      setMlMeta(ml);
    } catch (e) {
      console.warn('Could not fetch dashboard data:', e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const categoryChartData = stats ? {
    labels: ['Safe', 'Risky', 'Toxic'],
    datasets: [{
      data: [stats.safe_count, stats.risky_count, stats.toxic_count],
      backgroundColor: ['rgba(0,214,143,0.8)', 'rgba(255,170,0,0.8)', 'rgba(255,61,113,0.8)'],
      borderColor:     ['#00d68f', '#ffaa00', '#ff3d71'],
      borderWidth: 2,
    }],
  } : null;

  const typeLabels = stats ? Object.keys(stats.type_distribution) : [];
  const typeValues = stats ? Object.values(stats.type_distribution) : [];

  const typeChartData = {
    labels: typeLabels,
    datasets: [{
      label: 'Count',
      data: typeValues,
      backgroundColor: 'rgba(108, 99, 255, 0.7)',
      borderColor: '#6c63ff',
      borderWidth: 2,
      borderRadius: 6,
    }],
  };

  const typeChartOpts = {
    ...CHART_OPTS,
    plugins: { ...CHART_OPTS.plugins, legend: { display: false } },
    scales: {
      x: { ticks: { color: '#8892b0', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#8892b0' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
    },
  };

  const statCards = stats ? [
    { label: 'Total Analyzed', value: stats.total_analyzed,  sub: 'messages',             color: 'var(--brand)' },
    { label: 'Safe',           value: stats.safe_count,       sub: `${stats.safe_percent}%`,  color: 'var(--safe)' },
    { label: 'Risky',          value: stats.risky_count,      sub: `${stats.risky_percent}%`, color: 'var(--risky)' },
    { label: 'Toxic',          value: stats.toxic_count,      sub: `${stats.toxic_percent}%`, color: 'var(--toxic)' },
  ] : [];

  const classColors = { Safe: 'var(--safe)', Risky: 'var(--risky)', Toxic: 'var(--toxic)' };

  return (
    <div>
      <div className="page-header">
        <h1>📊 Moderation Dashboard</h1>
        <p>Real-time analytics and monitoring. Auto-refreshes every 5 seconds.</p>
      </div>

      {loading ? (
        <div className="empty-state" style={{ padding: '60px' }}>
          <div className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
          <p style={{ color: 'var(--text-muted)', marginTop: 12 }}>Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* Stat Cards */}
          <div className="stats-grid">
            {statCards.map(card => (
              <div key={card.label} className="stat-card" style={{ '--accent-color': card.color }}>
                <span className="stat-label">{card.label}</span>
                <span className="stat-value">{card.value.toLocaleString()}</span>
                <span className="stat-sub">{card.sub}</span>
              </div>
            ))}
          </div>

          {/* 🤖 AI Pipeline Card */}
          {mlMeta && (
            <div className="chart-card" style={{ marginBottom: 24 }}>
              <h3 style={{ marginBottom: 16 }}>🤖 AI Pipeline — 3-Layer Architecture</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 20 }}>
                {/* Layer 1 */}
                <div style={{ background: 'rgba(108,99,255,0.1)', borderRadius: 12, padding: '16px', border: '1px solid rgba(108,99,255,0.3)' }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#6c63ff', marginBottom: 8 }}>Layer 1 — Local ML Model</div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>TF-IDF + Logistic Regression</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Trained on {mlMeta.training_examples} multilingual examples</div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: '#6c63ff' }}>{(mlMeta.cv_accuracy * 100).toFixed(1)}%</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>5-Fold CV Acc</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--safe)' }}>{(mlMeta.training_accuracy * 100).toFixed(0)}%</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Train Acc</div>
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--risky)' }}>{mlMeta.features?.toLocaleString()}</div>
                      <div style={{ fontSize: 10, color: 'var(--text-muted)' }}>Features</div>
                    </div>
                  </div>
                </div>

                {/* Layer 2 */}
                <div style={{ background: 'rgba(0,214,143,0.08)', borderRadius: 12, padding: '16px', border: '1px solid rgba(0,214,143,0.25)' }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--safe)', marginBottom: 8 }}>Layer 2 — Google LLM</div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>Gemini 2.0 Flash</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Context-aware · Multilingual · Explainable</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {['English', 'Hindi', 'Hinglish'].map(lang => (
                      <div key={lang} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--safe)' }} />
                        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{lang}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Layer 3 */}
                <div style={{ background: 'rgba(255,170,0,0.08)', borderRadius: 12, padding: '16px', border: '1px solid rgba(255,170,0,0.25)' }}>
                  <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--risky)', marginBottom: 8 }}>Layer 3 — Fusion</div>
                  <div style={{ fontSize: 13, color: 'var(--text-primary)', fontWeight: 600, marginBottom: 4 }}>Confidence Fusion</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>Gemini 70% · ML 30% weighted vote</div>
                  <div style={{ fontSize: 11, color: 'var(--risky)', fontFamily: 'JetBrains Mono, monospace' }}>
                    if ML=Toxic &gt; Gemini+1<br/>→ escalate to Risky
                  </div>
                </div>
              </div>

              {/* Per-class metrics */}
              {mlMeta.per_class && (
                <div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 10 }}>ML Model — Per-Class Performance</div>
                  <div style={{ display: 'flex', gap: 12 }}>
                    {Object.entries(mlMeta.per_class).map(([cls, m]) => (
                      <div key={cls} style={{
                        flex: 1, background: 'rgba(255,255,255,0.03)', borderRadius: 8, padding: '10px 12px',
                        border: `1px solid ${classColors[cls]}33`
                      }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: classColors[cls], marginBottom: 6 }}>{cls}</div>
                        <div style={{ display: 'flex', gap: 8 }}>
                          {[['P', m.precision], ['R', m.recall], ['F1', m.f1]].map(([label, val]) => (
                            <div key={label} style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                              <span style={{ color: classColors[cls], fontWeight: 600 }}>{(val * 100).toFixed(0)}%</span> {label}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Charts */}
          <div className="dashboard-grid">
            <div className="chart-card">
              <h3>Content Type Distribution</h3>
              <div style={{ height: 220 }}>
                {typeLabels.length > 0
                  ? <Bar data={typeChartData} options={typeChartOpts} />
                  : <div className="empty-state"><p>No data yet</p></div>
                }
              </div>
            </div>

            <div className="chart-card">
              <h3>Category Breakdown</h3>
              <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {categoryChartData && stats.total_analyzed > 0
                  ? <Doughnut data={categoryChartData} options={CHART_OPTS} />
                  : <div className="empty-state"><p>No data yet</p></div>
                }
              </div>
            </div>
          </div>

          {/* Recent Logs */}
          <div className="table-wrap">
            <div className="table-card">
              <div className="table-header">
                <h3>Recent Moderation Logs</h3>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                  Showing last {recent.length} entries
                </span>
              </div>
              {recent.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Message</th>
                      <th>Category</th>
                      <th>Type</th>
                      <th>Confidence</th>
                      <th>ML Layer</th>
                      <th>Language</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((log, i) => {
                      const cat = (log.result?.category || 'safe').toLowerCase();
                      const mlCat = log.result?.layers?.ml?.category;
                      const mlConf = log.result?.layers?.ml?.confidence;
                      return (
                        <tr key={i}>
                          <td><span className="cell-text">{log.text}</span></td>
                          <td><span className={`badge ${cat}`}>{log.result?.category}</span></td>
                          <td><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{log.result?.type || '—'}</span></td>
                          <td>
                            <span style={{
                              fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                              color: cat === 'safe' ? 'var(--safe)' : cat === 'risky' ? 'var(--risky)' : 'var(--toxic)',
                            }}>
                              {log.result?.confidence}%
                            </span>
                          </td>
                          <td>
                            {mlCat ? (
                              <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                                <span style={{ color: classColors[mlCat] }}>{mlCat}</span> {mlConf}%
                              </span>
                            ) : <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>—</span>}
                          </td>
                          <td><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{log.result?.language || '—'}</span></td>
                          <td><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{log.source || '—'}</span></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <div className="empty-state-icon">📂</div>
                  <p>No logs yet. Start the live feed or use the tester.</p>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
