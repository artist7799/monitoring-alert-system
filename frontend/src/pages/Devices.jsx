import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Server, ChevronLeft, ChevronRight } from 'lucide-react';
import Layout from '../components/Layout';
import DeviceTable from '../components/DeviceTable';
import ErrorMessage from '../components/ErrorMessage';
import { statusApi } from '../api/statusApi';

export const Devices = () => {
  const [devices, setDevices] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 10, total: 0, pages: 1 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDevices = useCallback(async (page = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      const params = {
        page,
        per_page: pagination.per_page
      };
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;
      if (locationFilter.trim()) params.location = locationFilter.trim();

      const response = await statusApi.getDeviceStatusList(params);
      const resData = response.data || response;
      const deviceList = Array.isArray(resData) ? resData : (resData.devices || resData.items || []);
      
      setDevices(deviceList);

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
          total: deviceList.length,
          pages: 1
        }));
      }
    } catch (err) {
      console.error('Failed to fetch devices:', err);
      setError('Failed to load monitoring devices.');
    } finally {
      setIsLoading(false);
    }
  }, [search, statusFilter, locationFilter, pagination.per_page]);

  useEffect(() => {
    fetchDevices(1);
  }, [fetchDevices]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
      fetchDevices(newPage);
    }
  };

  return (
    <Layout title="Monitoring Devices">
      <ErrorMessage message={error} onRetry={() => fetchDevices(pagination.page)} />

      <div className="table-card">
        {/* Filters and Search Bar */}
        <div className="table-header-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
            <div className="search-input-wrapper">
              <Search size={16} />
              <input
                type="text"
                className="form-control"
                placeholder="Search by code, name or location..."
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
                <option value="ONLINE">ONLINE</option>
                <option value="OFFLINE">OFFLINE</option>
                <option value="WARNING">WARNING</option>
              </select>

              <input
                type="text"
                className="form-control"
                placeholder="Location..."
                style={{ width: '160px' }}
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Devices Table */}
        <DeviceTable devices={devices} isLoading={isLoading} />

        {/* Pagination Bar */}
        {pagination.pages > 1 && (
          <div className="pagination">
            <span>
              Showing Page <strong>{pagination.page}</strong> of <strong>{pagination.pages}</strong> ({pagination.total || devices.length} total)
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

export default Devices;
