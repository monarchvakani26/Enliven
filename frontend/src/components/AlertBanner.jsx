import React from 'react';

export default function AlertBanner({ alerts, onDismiss }) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <>
      {alerts.map(alert => (
        <div key={alert.id} className="alert-banner">
          <span className="alert-icon">🚨</span>
          <div className="alert-text">
            <strong>{alert.title}</strong>
            <p>{alert.message}</p>
          </div>
          <button
            className="alert-close"
            onClick={() => onDismiss(alert.id)}
            aria-label="Dismiss alert"
          >
            ✕
          </button>
        </div>
      ))}
    </>
  );
}
