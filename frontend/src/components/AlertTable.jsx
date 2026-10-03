import React from 'react';
import { Bell, Check, ShieldCheck } from 'lucide-react';
import SeverityBadge from './SeverityBadge';
import { formatDate } from '../utils/formatDate';
import { getAlertStatusClass, USER_ROLES } from '../utils/status';

export const AlertTable = ({
  alerts = [],
  isLoading = false,
  userRole = USER_ROLES.VIEWER,
  onAcknowledge,
  onResolve
}) => {
  if (isLoading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '0 auto 1rem auto' }}></div>
        <p>Loading alerts...</p>
      </div>
    );
  }

  if (!alerts || alerts.length === 0) {
    return (
      <div className="empty-state">
        <Bell className="empty-icon" />
        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>No alerts found</h3>
        <p style={{ fontSize: '0.85rem' }}>No monitoring alerts match the criteria.</p>
      </div>
    );
  }

  const canManageAlerts = userRole === USER_ROLES.ADMIN || userRole === USER_ROLES.OPERATOR;

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Alert ID</th>
            <th>Device</th>
            <th>Severity</th>
            <th>Title</th>
            <th>Message</th>
            <th>Status</th>
            <th>Created At</th>
            {canManageAlerts && <th>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {alerts.map((alert) => {
            const statusUpper = String(alert.status || '').toUpperCase();
            const deviceName = alert.device_name || alert.device?.name || alert.device_code || `DEV-${alert.device_id}`;

            return (
              <tr key={alert.id}>
                <td className="mono" style={{ color: 'var(--text-muted)' }}>
                  #{alert.id}
                </td>
                <td style={{ fontWeight: 600 }}>{deviceName}</td>
                <td>
                  <SeverityBadge severity={alert.severity} />
                </td>
                <td style={{ fontWeight: 500, color: 'var(--text-main)' }}>{alert.title}</td>
                <td style={{ color: 'var(--text-muted)', maxWidth: '280px', whiteSpace: 'normal' }}>
                  {alert.message}
                </td>
                <td>
                  <span className={`badge ${getAlertStatusClass(statusUpper)}`}>
                    {statusUpper}
                  </span>
                </td>
                <td>{formatDate(alert.created_at)}</td>
                {canManageAlerts && (
                  <td>
                    <div style={{ display: 'flex', gap: '0.35rem' }}>
                      {statusUpper === 'OPEN' && (
                        <button
                          className="btn btn-ack btn-sm"
                          onClick={() => onAcknowledge && onAcknowledge(alert.id)}
                          title="Acknowledge Alert"
                        >
                          <Check size={13} />
                          Ack
                        </button>
                      )}
                      {statusUpper !== 'RESOLVED' && (
                        <button
                          className="btn btn-resolve btn-sm"
                          onClick={() => onResolve && onResolve(alert.id)}
                          title="Resolve Alert"
                        >
                          <ShieldCheck size={13} />
                          Resolve
                        </button>
                      )}
                      {statusUpper === 'RESOLVED' && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>Done</span>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default AlertTable;
