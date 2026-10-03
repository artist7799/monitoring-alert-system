import React from 'react';
import { SSE_STATUS } from '../hooks/useSSE';

export const Header = ({ title = 'Dashboard', sseStatus = SSE_STATUS.CONNECTED }) => {
  const getStatusDisplay = () => {
    return { label: 'Live', class: 'live' };
  };

  const statusDisplay = getStatusDisplay();

  return (
    <header className="header">
      <div>
        <h1 className="page-title">{title}</h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div className="connection-indicator">
          <span className={`status-dot ${statusDisplay.class}`}></span>
          <span>● {statusDisplay.label}</span>
        </div>
      </div>
    </header>
  );
};

export default Header;
