import React from 'react';
import { ShieldAlert, AlertCircle, Info } from 'lucide-react';
import { getSeverityClass } from '../utils/status';

export const SeverityBadge = ({ severity }) => {
  const normalizedSeverity = String(severity || '').toUpperCase();
  const className = getSeverityClass(normalizedSeverity);

  const getIcon = () => {
    switch (normalizedSeverity) {
      case 'CRITICAL':
        return <ShieldAlert size={13} />;
      case 'HIGH':
        return <AlertCircle size={13} />;
      case 'LOW':
        return <Info size={13} />;
      default:
        return <Info size={13} />;
    }
  };

  return (
    <span className={`badge ${className}`}>
      {getIcon()}
      {normalizedSeverity || 'INFO'}
    </span>
  );
};

export default SeverityBadge;
