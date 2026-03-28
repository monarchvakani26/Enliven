import React, { useEffect, useRef, useState, useCallback } from 'react';
import ModerationCard from '../components/ModerationCard';
import AlertBanner from '../components/AlertBanner';

const WS_URL = 'ws://localhost:8000/ws/feed';
const MAX_ITEMS = 60;

const FILTERS = ['All', 'Safe', 'Risky', 'Toxic'];

export default function LiveFeedPage() {
  const [items, setItems]       = useState([]);
  const [filter, setFilter]     = useState('All');
  const [status, setStatus]     = useState('connecting'); // connecting | live | offline
  const [alerts, setAlerts]     = useState([]);
  const [counter, setCounter]   = useState({ safe: 0, risky: 0, toxic: 0 });
  const wsRef                   = useRef(null);
  const alertIdRef              = useRef(0);
  const toxicWindowRef          = useRef([]);
  const feedEndRef              = useRef(null);

  // Auto-scroll to top (new items prepend)
  // Actually we append and scroll to bottom
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [items]);

  const pushAlert = useCallback((title, message) => {
    const id = ++alertIdRef.current;
    setAlerts(prev => [...prev, { id, title, message }]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== id));
    }, 8000);
  }, []);

  const dismissAlert = useCallback((id) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
  }, []);

  const checkToxicSpike = useCallback((category) => {
    const now = Date.now();
    toxicWindowRef.current.push({ category, time: now });
    // Keep last 30 seconds
    toxicWindowRef.current = toxicWindowRef.current.filter(e => now - e.time < 30000);
    const recentToxic = toxicWindowRef.current.filter(e => e.category === 'Toxic').length;
    if (recentToxic >= 3) {
      pushAlert(
        '⚠️ Toxic Spike Detected!',
        `${recentToxic} toxic messages detected in the last 30 seconds. Review immediately.`
      );
      toxicWindowRef.current = []; // reset window
    }
  }, [pushAlert]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setStatus('connecting');
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('live');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'moderation') {
          const cat = data.result?.category;
          setItems(prev => {
            const next = [data, ...prev];
            return next.slice(0, MAX_ITEMS);
          });
          setCounter(prev => ({
            ...prev,
            safe:  cat === 'Safe'  ? prev.safe  + 1 : prev.safe,
            risky: cat === 'Risky' ? prev.risky + 1 : prev.risky,
            toxic: cat === 'Toxic' ? prev.toxic + 1 : prev.toxic,
          }));
          checkToxicSpike(cat);
        }
      } catch (_) {}
    };

    ws.onclose = () => {
      setStatus('offline');
      // Auto-reconnect after 4s
      setTimeout(connect, 4000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [checkToxicSpike]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const filteredItems = filter === 'All'
    ? items
    : items.filter(i => i.result?.category === filter);

  const total = counter.safe + counter.risky + counter.toxic;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <AlertBanner alerts={alerts} onDismiss={dismissAlert} />

      <div className="page-header">
        <h1>📡 Live Moderation Feed</h1>
        <p>Real-time AI-powered content classification stream</p>
      </div>

      <div className="feed-toolbar">
        <div className="feed-indicator">
          <div className={`live-dot ${status === 'live' ? '' : 'offline'}`} />
          <span>
            {status === 'connecting' && 'Connecting to feed...'}
            {status === 'live' && `LIVE — ${total} analyzed`}
            {status === 'offline' && 'Reconnecting...'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          {/* Mini counters */}
          <div style={{ display: 'flex', gap: 14, fontSize: 12 }}>
            <span style={{ color: 'var(--safe)' }}>✅ {counter.safe}</span>
            <span style={{ color: 'var(--risky)' }}>⚠️ {counter.risky}</span>
            <span style={{ color: 'var(--toxic)' }}>🚫 {counter.toxic}</span>
          </div>

          <div className="filter-tabs">
            {FILTERS.map(f => (
              <button
                key={f}
                className={`filter-tab ${f.toLowerCase()} ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="feed-list">
        {filteredItems.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">📭</div>
            <p>
              {status === 'connecting' ? 'Waiting for AI moderation feed...' : 'No messages match this filter.'}
            </p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <ModerationCard key={item.id} item={item} />
          ))
        )}
        <div ref={feedEndRef} />
      </div>
    </div>
  );
}
