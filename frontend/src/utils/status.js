export const DEVICE_STATUS = {
  ONLINE: 'ONLINE',
  OFFLINE: 'OFFLINE',
  WARNING: 'WARNING'
};

export const ALERT_SEVERITY = {
  LOW: 'LOW',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL'
};

export const ALERT_STATUS = {
  OPEN: 'OPEN',
  ACKNOWLEDGED: 'ACKNOWLEDGED',
  RESOLVED: 'RESOLVED'
};

export const USER_ROLES = {
  ADMIN: 'ADMIN',
  OPERATOR: 'OPERATOR',
  VIEWER: 'VIEWER'
};

export const getStatusClass = (status) => {
  switch (String(status).toUpperCase()) {
    case 'ONLINE':
      return 'badge-status-online';
    case 'WARNING':
      return 'badge-status-warning';
    case 'OFFLINE':
      return 'badge-status-offline';
    default:
      return 'badge-status-unknown';
  }
};

export const getSeverityClass = (severity) => {
  switch (String(severity).toUpperCase()) {
    case 'CRITICAL':
      return 'badge-severity-critical';
    case 'HIGH':
      return 'badge-severity-high';
    case 'LOW':
      return 'badge-severity-low';
    default:
      return 'badge-severity-info';
  }
};

export const getAlertStatusClass = (status) => {
  switch (String(status).toUpperCase()) {
    case 'OPEN':
      return 'badge-alert-open';
    case 'ACKNOWLEDGED':
      return 'badge-alert-ack';
    case 'RESOLVED':
      return 'badge-alert-resolved';
    default:
      return 'badge-alert-default';
  }
};
