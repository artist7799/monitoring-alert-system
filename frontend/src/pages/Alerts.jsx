import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Bell, ChevronLeft, ChevronRight } from 'lucide-react';
import Layout from '../components/Layout';
import AlertTable from '../components/AlertTable';
import ErrorMessage from '../components/ErrorMessage';
import Toast from '../components/Toast';
import { alertApi } from '../api/alertApi';
import { useAuth } from '../hooks/useAuth';

export const Alerts = () => {
  const { user } = useAuth();
  const [alerts, setAlerts] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 15, total: 0, pages: 1 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
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

  const fetchAlerts = useCallback(async (page = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      const params = {
        page,
        per_page: pagination.per_page
      };
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;

      const response = await alertApi.getAlerts(params);
      const resData = response.data || response;
      const alertList = Array.isArray(resData) ? resData : (resData.alerts || resData.items || []);

      setAlerts(alertList);

      if (resData.pagination) {
        setPagination(resData.pagination);
      } else if (resData.total !== undefined) {
        setPagination((prev) => ({
          ...prev,
          page,
          total: resData.total,
          pages: Math.ceil(resData.total / prev.per_page) || 1
        }));
      } else {
        setPagination((prev) => ({
          ...prev,
          page,
          total: alertList.length,
          pages: 1
        }));
      }
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
      setError('Failed to load alert management list.');
    } finally {
      setIsLoading(false);
    }
  }, [search, statusFilter, severityFilter, pagination.per_page]);

  useEffect(() => {
    fetchAlerts(1);
  }, [fetchAlerts]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
      fetchAlerts(newPage);
    }
  };

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await alertApi.acknowledgeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED' } : a))
      );
      addToast({
        title: 'Alert Acknowledged',
        message: `Alert #${alertId} updated to ACKNOWLEDGED`,
        severity: 'LOW'
      });
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
      const msg = err.response?.data?.message || 'Failed to acknowledge alert';
      addToast({ title: 'Action Failed', message: msg, severity: 'CRITICAL' });
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await alertApi.resolveAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.id === alertId ? { ...a, status: 'RESOLVED' } : a))
      );
      addToast({
        title: 'Alert Resolved',
        message: `Alert #${alertId} updated to RESOLVED`,
        severity: 'LOW'
      });
    } catch (err) {
      console.error('Failed to resolve alert:', err);
      const msg = err.response?.data?.message || 'Failed to resolve alert';
      addToast({ title: 'Action Failed', message: msg, severity: 'CRITICAL' });
    }
  };

  return (
    <Layout title="Alert Management" toasts={toasts} removeToast={removeToast}>
      <ErrorMessage message={error} onRetry={() => fetchAlerts(pagination.page)} />

      <div className="table-card">
        {/* Filters and Search Bar */}
        <div className="table-header-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
            <div className="search-input-wrapper">
              <Search size={16} />
              <input
                type="text"
                className="form-control"
                placeholder="Search alert title or message..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Filter size={16} color="var(--text-dim)" />
              <select
                className="select-control"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="OPEN">OPEN</option>
                <option value="ACKNOWLEDGED">ACKNOWLEDGED</option>
                <option value="RESOLVED">RESOLVED</option>
              </select>

              <select
                className="select-control"
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
              >
                <option value="">All Severities</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="LOW">LOW</option>
              </select>
            </div>
          </div>
        </div>

        {/* Alert Table */}
        <AlertTable
          alerts={alerts}
          isLoading={isLoading}
          userRole={user?.role}
          onAcknowledge={handleAcknowledgeAlert}
          onResolve={handleResolveAlert}
        />

        {/* Pagination Bar */}
        {pagination.pages > 1 && (
          <div className="pagination">
            <span>
              Showing Page <strong>{pagination.page}</strong> of <strong>{pagination.pages}</strong> ({pagination.total || alerts.length} total)
            </span>
            <div className="pagination-controls">
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handlePageChange(pagination.page - 1)}
                disabled={pagination.page <= 1}
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => handlePageChange(pagination.page + 1)}
                disabled={pagination.page >= pagination.pages}
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Alerts;
