import React, { useEffect, useState, useCallback } from 'react';
import {
  Chart as ChartJS,
  ArcElement, Tooltip, Legend,
  CategoryScale, LinearScale, BarElement, Title,
} from 'chart.js';
import { Doughnut, Bar } from 'react-chartjs-2';
import ModerationCard from '../components/ModerationCard';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title);

const API = 'http://localhost:8000';

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: { color: '#8892b0', font: { size: 12 } },
    },
  },
};

export default function DashboardPage() {
  const [stats, setStats]   = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([
        fetch(`${API}/api/stats`).then(r => r.json()),
        fetch(`${API}/api/recent?n=15&flagged_only=false`).then(r => r.json()),
      ]);
      setStats(s);
      setRecent(r.logs || []);
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
    plugins: {
      ...CHART_OPTS.plugins,
      legend: { display: false },
    },
    scales: {
      x: { ticks: { color: '#8892b0', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
      y: { ticks: { color: '#8892b0' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
    },
  };

  const statCards = stats ? [
    { label: 'Total Analyzed', value: stats.total_analyzed, sub: 'messages', color: 'var(--brand)' },
    { label: 'Safe',   value: stats.safe_count,  sub: `${stats.safe_percent}%`,  color: 'var(--safe)' },
    { label: 'Risky',  value: stats.risky_count, sub: `${stats.risky_percent}%`, color: 'var(--risky)' },
    { label: 'Toxic',  value: stats.toxic_count, sub: `${stats.toxic_percent}%`, color: 'var(--toxic)' },
  ] : [];

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
              <div
                key={card.label}
                className="stat-card"
                style={{ '--accent-color': card.color }}
              >
                <span className="stat-label">{card.label}</span>
                <span className="stat-value">{card.value.toLocaleString()}</span>
                <span className="stat-sub">{card.sub}</span>
              </div>
            ))}
          </div>

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
                      <th>Language</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((log, i) => {
                      const cat = (log.result?.category || 'safe').toLowerCase();
                      return (
                        <tr key={i}>
                          <td><span className="cell-text">{log.text}</span></td>
                          <td><span className={`badge ${cat}`}>{log.result?.category}</span></td>
                          <td><span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{log.result?.type || '—'}</span></td>
                          <td>
                            <span style={{
                              fontFamily: 'JetBrains Mono, monospace',
                              fontSize: 13,
                              color: cat === 'safe' ? 'var(--safe)' : cat === 'risky' ? 'var(--risky)' : 'var(--toxic)',
                            }}>
                              {log.result?.confidence}%
                            </span>
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
