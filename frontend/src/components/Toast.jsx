import React, { useEffect } from 'react';
import { Bell, AlertTriangle, CheckCircle, X } from 'lucide-react';

export const Toast = ({ toast, onClose }) => {
  const { id, title, message, severity, duration = 6000 } = toast;

  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);
    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  const getSeverityIcon = () => {
    switch (String(severity).toUpperCase()) {
      case 'CRITICAL':
        return <AlertTriangle size={18} color="#ef4444" />;
      case 'HIGH':
        return <AlertTriangle size={18} color="#f97316" />;
      case 'LOW':
        return <Bell size={18} color="#3b82f6" />;
      default:
        return <CheckCircle size={18} color="#10b981" />;
    }
  };

  const isCritical = String(severity).toUpperCase() === 'CRITICAL';
  const isHigh = String(severity).toUpperCase() === 'HIGH';

  return (
    <div className={`toast ${isCritical ? 'critical' : isHigh ? 'high' : ''}`}>
      {getSeverityIcon()}
      <div style={{ flex: 1 }}>
        <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-main)' }}>{title}</h4>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{message}</p>
      </div>
      <button
        onClick={() => onClose(id)}
        style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '0.2rem' }}
      >
        <X size={14} />
      </button>
    </div>
  );
};

export default Toast;
