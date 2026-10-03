import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Server, Bell, Radio, Activity } from 'lucide-react';
import Layout from '../components/Layout';
import MetricChart from '../components/MetricChart';
import StatusBadge from '../components/StatusBadge';
import AlertTable from '../components/AlertTable';
import EventTable from '../components/EventTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { statusApi } from '../api/statusApi';
import { formatRelativeTime } from '../utils/formatDate';
import { useAuth } from '../hooks/useAuth';

export const DeviceDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [deviceData, setDeviceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await statusApi.getDeviceStatusById(id);
        setDeviceData(response.data || response);
      } catch (err) {
        console.error('Failed to load device details:', err);
        setError(`Failed to load device #${id} status information.`);
      } finally {
        setIsLoading(false);
      }
    };

    if (id) {
      fetchDetails();
    }
  }, [id]);

  if (isLoading) {
    return (
      <Layout title="Device Details">
        <Loading message={`Loading device telemetry for #${id}...`} />
      </Layout>
    );
  }

  if (error || !deviceData) {
    return (
      <Layout title="Device Details">
        <ErrorMessage message={error || 'Device not found.'} />
        <button className="btn btn-secondary" onClick={() => navigate('/devices')}>
          <ArrowLeft size={16} /> Back to Devices
        </button>
      </Layout>
    );
  }

  const device = deviceData.device || deviceData;
  const metrics = deviceData.metrics || device.metrics || {};
  const recentEvents = deviceData.recent_events || [];
  const openAlerts = deviceData.open_alerts || [];

  const cpuVal = typeof metrics.cpu_usage === 'number' ? metrics.cpu_usage : parseFloat(metrics.cpu_usage) || 0;
  const memVal = typeof metrics.memory_usage === 'number' ? metrics.memory_usage : parseFloat(metrics.memory_usage) || 0;
  const tempVal = typeof metrics.temperature === 'number' ? metrics.temperature : parseFloat(metrics.temperature) || 0;
  const uptimeVal = metrics.uptime_seconds ? `${Math.floor(metrics.uptime_seconds / 3600)} hrs` : 'N/A';

  // Determine temp color based on threshold
  const tempColor = tempVal > 80 ? '#ef4444' : tempVal > 65 ? '#f59e0b' : '#10b981';

  return (
    <Layout title={`Device: ${device.name || device.device_code}`}>
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <button className="btn btn-secondary" onClick={() => navigate('/devices')}>
          <ArrowLeft size={16} /> Back to Devices
        </button>
        <StatusBadge status={device.status} />
      </div>

      {/* Device Overview Banner */}
      <div className="table-card" style={{ padding: '1.5rem', marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap' }}>
          <div className="brand-icon" style={{ width: '52px', height: '52px', borderRadius: '12px' }}>
            <Server size={28} />
          </div>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700 }}>{device.name}</h2>
            <div style={{ display: 'flex', gap: '1.5rem', marginTop: '0.35rem', fontSize: '0.85rem', color: 'var(--text-muted)', flexWrap: 'wrap' }}>
              <span>Code: <strong className="mono" style={{ color: 'var(--primary)' }}>{device.device_code || device.code}</strong></span>
              <span>Type: <strong>{device.device_type || 'Server'}</strong></span>
              <span>Location: <strong>{device.location || 'Unspecified'}</strong></span>
              <span>Last Seen: <strong>{formatRelativeTime(device.last_seen)}</strong></span>
              <span>Uptime: <strong>{uptimeVal}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Metric Visualizations & Sparkline Charts */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ fontSize: '1.05rem', marginBottom: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={18} color="var(--primary)" />
          <span>Real-Time Metric Telemetry</span>
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
          <MetricChart title="CPU Load" value={cpuVal} unit="%" color="#3b82f6" />
          <MetricChart title="Memory Allocation" value={memVal} unit="%" color="#6366f1" />
          <MetricChart title="Core Temperature" value={tempVal} unit="°C" color={tempColor} />
        </div>
      </div>

      {/* Device Specific Tables */}
      <div className="dashboard-grid">
        <div className="dashboard-col-12">
          <div className="table-card" style={{ marginBottom: '1.5rem' }}>
            <div className="table-header-bar">
              <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Bell size={18} color="#f97316" />
                <span>Open Alerts ({openAlerts.length})</span>
              </h3>
            </div>
            <AlertTable alerts={openAlerts} isLoading={false} userRole={user?.role} />
          </div>
        </div>

        <div className="dashboard-col-12">
          <div className="table-card">
            <div className="table-header-bar">
              <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Radio size={18} color="#3b82f6" />
                <span>Recent Device Events</span>
              </h3>
            </div>
            <EventTable events={recentEvents} isLoading={false} />
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default DeviceDetails;
