import React, { useState, useEffect, useCallback } from 'react';
import { Server, Wifi, WifiOff, AlertTriangle, Bell, ShieldAlert, Radio } from 'lucide-react';
import Layout from '../components/Layout';
import StatCard from '../components/StatCard';
import EventTable from '../components/EventTable';
import AlertTable from '../components/AlertTable';
import Loading from '../components/Loading';
import ErrorMessage from '../components/ErrorMessage';
import { statusApi } from '../api/statusApi';
import { alertApi } from '../api/alertApi';
import { useSSE } from '../hooks/useSSE';
import { useAuth } from '../hooks/useAuth';

export const Dashboard = () => {
  const { user } = useAuth();
  const [overview, setOverview] = useState(null);
  const [recentEvents, setRecentEvents] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toasts, setToasts] = useState([]);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev.slice(-4), { ...toast, id }]);
  }, []);

  // Fetch initial REST data
  const loadDashboardData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [overviewRes, eventsRes, alertsRes] = await Promise.all([
        statusApi.getOverview(),
        statusApi.getRecentEvents(10),
        statusApi.getRecentAlerts(10)
      ]);

      setOverview(overviewRes.data || overviewRes);
      
      const eventsList = eventsRes.data || eventsRes.events || [];
      setRecentEvents(Array.isArray(eventsList) ? eventsList : []);

      const alertsList = alertsRes.data || alertsRes.alerts || [];
      setRecentAlerts(Array.isArray(alertsList) ? alertsList : []);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Unable to connect to monitoring API. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  // Handle SSE real-time updates
  const handleSSEEvent = useCallback((event) => {
    const { type, data } = event;
    if (!data) return;

    if (type === 'system_status') {
      setOverview((prev) => ({
        ...prev,
        ...data
      }));
    } else if (type === 'event') {
      const newEvent = typeof data === 'string' ? JSON.parse(data) : data;
      setRecentEvents((prev) => {
        // Prevent duplicate events
        if (prev.some((e) => e.id && newEvent.id && e.id === newEvent.id)) {
          return prev;
        }
        return [newEvent, ...prev].slice(0, 10);
      });
      // Increment events_today in overview counter
      setOverview((prev) => prev ? { ...prev, events_today: (prev.events_today || 0) + 1 } : prev);
    } else if (type === 'alert') {
      const newAlert = typeof data === 'string' ? JSON.parse(data) : data;
      setRecentAlerts((prev) => {
        if (prev.some((a) => a.id && newAlert.id && a.id === newAlert.id)) {
          return prev;
        }
        return [newAlert, ...prev].slice(0, 10);
      });

      // Update counters in overview
      setOverview((prev) => {
        if (!prev) return prev;
        const isCritical = String(newAlert.severity).toUpperCase() === 'CRITICAL';
        return {
          ...prev,
          open_alerts: (prev.open_alerts || 0) + 1,
          critical_alerts: isCritical ? (prev.critical_alerts || 0) + 1 : (prev.critical_alerts || 0)
        };
      });

      // Trigger toast notification
      addToast({
        title: `🚨 ${newAlert.title || 'New Alert Triggered'}`,
        message: `${newAlert.device_name || newAlert.device_code || 'Device'}: ${newAlert.message || ''}`,
        severity: newAlert.severity || 'HIGH'
      });
    } else if (type === 'device_status') {
      // Refresh overview data on device status change
      statusApi.getOverview().then((res) => setOverview(res.data || res)).catch(() => {});
    }
  }, [addToast]);

  const { connectionStatus } = useSSE(handleSSEEvent);

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await alertApi.acknowledgeAlert(alertId);
      setRecentAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
      );
      addToast({ title: 'Alert Acknowledged', message: `Alert #${alertId} status updated to ACKNOWLEDGED`, severity: 'LOW' });
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await alertApi.resolveAlert(alertId);
      setRecentAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'RESOLVED' } : a))
      );
      addToast({ title: 'Alert Resolved', message: `Alert #${alertId} status updated to RESOLVED`, severity: 'LOW' });
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  return (
    <Layout title="System Overview" sseStatus={connectionStatus} toasts={toasts} removeToast={removeToast}>
      <ErrorMessage message={error} onRetry={loadDashboardData} />

      {isLoading ? (
        <Loading message="Fetching real-time monitoring overview..." />
      ) : (
        <>
          {/* Overview Stat Cards */}
          <div className="stats-grid">
            <StatCard
              title="Total Devices"
              value={overview?.total_devices}
              description="Configured monitors"
              icon={Server}
              color="#3b82f6"
            />
            <StatCard
              title="Online"
              value={overview?.online_devices}
              description="Healthy connection"
              icon={Wifi}
              color="#10b981"
            />
            <StatCard
              title="Warning"
              value={overview?.warning_devices}
              description="Threshold warning"
              icon={AlertTriangle}
              color="#f59e0b"
            />
            <StatCard
              title="Offline"
              value={overview?.offline_devices}
              description="Unreachable devices"
              icon={WifiOff}
              color="#64748b"
            />
            <StatCard
              title="Open Alerts"
              value={overview?.open_alerts}
              description="Pending resolution"
              icon={Bell}
              color="#f97316"
            />
            <StatCard
              title="Critical Alerts"
              value={overview?.critical_alerts}
              description="Requires immediate action"
              icon={ShieldAlert}
              color="#ef4444"
            />
            <StatCard
              title="Events Today"
              value={overview?.events_today}
              description="Telemetry records"
              icon={Radio}
              color="#6366f1"
            />
          </div>

          {/* Tables Grid */}
          <div className="dashboard-grid">
            {/* Recent Alerts Column */}
            <div className="dashboard-col-7">
              <div className="table-card">
                <div className="table-header-bar">
                  <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Bell size={18} color="#f97316" />
                    <span>Recent System Alerts</span>
                  </h3>
                </div>
                <AlertTable
                  alerts={recentAlerts}
                  isLoading={false}
                  userRole={user?.role}
                  onAcknowledge={handleAcknowledgeAlert}
                  onResolve={handleResolveAlert}
                />
              </div>
            </div>

            {/* Live Event Stream Column */}
            <div className="dashboard-col-5">
              <div className="table-card">
                <div className="table-header-bar">
                  <h3 style={{ fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Radio size={18} color="#3b82f6" />
                    <span>Live Telemetry Stream</span>
                  </h3>
                </div>
                <EventTable events={recentEvents} isLoading={false} />
              </div>
            </div>
          </div>
        </>
      )}
    </Layout>
  );
};

export default Dashboard;
