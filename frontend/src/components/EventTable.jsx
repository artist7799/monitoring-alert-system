import React from 'react';
import { Radio } from 'lucide-react';
import { formatDate } from '../utils/formatDate';

export const EventTable = ({ events = [], isLoading = false }) => {
  if (isLoading) {
    return (
      <div className="empty-state">
        <div className="spinner" style={{ margin: '0 auto 1rem auto' }}></div>
        <p>Loading events...</p>
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="empty-state">
        <Radio className="empty-icon" />
        <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>No events recorded</h3>
        <p style={{ fontSize: '0.85rem' }}>No monitoring telemetry events match the criteria.</p>
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Device</th>
            <th>Event Type</th>
            <th>Metric</th>
            <th>Value</th>
            <th>Message</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => {
            const deviceCode = event.device_code || event.device?.code || `DEV-${event.device_id}`;
            const formattedValue = event.metric_value !== null && event.metric_value !== undefined 
              ? `${event.metric_value} ${event.unit || ''}`.trim() 
              : 'N/A';

            return (
              <tr key={event.id}>
                <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                  {formatDate(event.timestamp || event.created_at)}
                </td>
                <td className="mono" style={{ fontWeight: 600, color: 'var(--primary)' }}>
                  {deviceCode}
                </td>
                <td>
                  <span className="badge" style={{ backgroundColor: 'rgba(255,255,255,0.06)', color: 'var(--text-main)', border: '1px solid var(--border-color)' }}>
                    {event.event_type}
                  </span>
                </td>
                <td className="mono" style={{ color: 'var(--text-muted)' }}>
                  {event.metric_name || 'N/A'}
                </td>
                <td className="mono" style={{ fontWeight: 600, color: 'var(--text-main)' }}>
                  {formattedValue}
                </td>
                <td style={{ color: 'var(--text-muted)', maxWidth: '300px', whiteSpace: 'normal' }}>
                  {event.message || '-'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default EventTable;
