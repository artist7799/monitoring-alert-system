import React from 'react';
import { Link } from 'react-router-dom';
import { Eye, HardDrive } from 'lucide-react';
import StatusBadge from './StatusBadge';
import { formatRelativeTime } from '../utils/formatDate';

export const DeviceTable = ({ devices = [], isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '0 auto 1rem auto' }}></div>
        <p>Loading devices...</p>
      </div>
    );
  }

  if (!devices || devices.length === 0) {
    return (
      <div className="empty-state">
        <HardDrive className="empty-icon" />
        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>No devices found</h3>
        <p style={{ fontSize: '0.85rem' }}>No monitoring devices match your query.</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Device Code</th>
            <th>Name</th>
            <th>Location</th>
            <th>Status</th>
            <th>Last Seen</th>
            <th>CPU</th>
            <th>Memory</th>
            <th>Temp</th>
            <th>Uptime</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {devices.map((device) => {
            const metrics = device.metrics || device.latest_metrics || {};
            const cpu = metrics.cpu_usage !== undefined ? `${metrics.cpu_usage}%` : (device.cpu_usage !== undefined ? `${device.cpu_usage}%` : 'N/A');
            const memory = metrics.memory_usage !== undefined ? `${metrics.memory_usage}%` : (device.memory_usage !== undefined ? `${device.memory_usage}%` : 'N/A');
            const temp = metrics.temperature !== undefined ? `${metrics.temperature} °C` : (device.temperature !== undefined ? `${device.temperature} °C` : 'N/A');
            const uptime = metrics.uptime_seconds ? `${Math.floor(metrics.uptime_seconds / 3600)}h` : (device.uptime_seconds ? `${Math.floor(device.uptime_seconds / 3600)}h` : 'N/A');

            return (
              <tr key={device.id || device.device_code}>
                <td className="mono" style={{ fontWeight: 600, color: 'var(--primary)' }}>
                  {device.device_code || device.code}
                </td>
                <td style={{ fontWeight: 500 }}>{device.name}</td>
                <td>{device.location || 'N/A'}</td>
                <td>
                  <StatusBadge status={device.status} />
                </td>
                <td>{formatRelativeTime(device.last_seen)}</td>
                <td className="mono">{cpu}</td>
                <td className="mono">{memory}</td>
                <td className="mono">{temp}</td>
                <td className="mono">{uptime}</td>
                <td>
                  <Link
                    to={`/devices/${device.id}`}
                    className="btn btn-secondary btn-sm"
                    title="View Details"
                  >
                    <Eye size={14} />
                    View
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default DeviceTable;
