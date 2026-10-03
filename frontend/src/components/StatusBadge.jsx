import React from 'react';
import { Wifi, AlertTriangle, WifiOff, HelpCircle } from 'lucide-react';
import { getStatusClass } from '../utils/status';

export const StatusBadge = ({ status }) => {
  const normalizedStatus = String(status || '').toUpperCase();
  const className = getStatusClass(normalizedStatus);

  const getIcon = () => {
    switch (normalizedStatus) {
      case 'ONLINE':
        return <Wifi size={13} />;
      case 'WARNING':
        return <AlertTriangle size={13} />;
      case 'OFFLINE':
        return <WifiOff size={13} />;
      default:
        return <HelpCircle size={13} />;
    }
  };

  return (
    <span className={`badge ${className}`}>
      {getIcon()}
      {normalizedStatus || 'UNKNOWN'}
    </span>
  );
};

export default StatusBadge;
