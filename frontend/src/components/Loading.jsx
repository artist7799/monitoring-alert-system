import React from 'react';

export const Loading = ({ message = 'Loading monitoring data...' }) => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>{message}</p>
    </div>
  );
};

export default Loading;
