import React, { useState, useEffect, useCallback } from 'react';
import { Search, Filter, Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import Layout from '../components/Layout';
import EventTable from '../components/EventTable';
import ErrorMessage from '../components/ErrorMessage';
import { eventApi } from '../api/eventApi';

export const Events = () => {
  const [events, setEvents] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, per_page: 15, total: 0, pages: 1 });
  const [search, setSearch] = useState('');
  const [eventTypeFilter, setEventTypeFilter] = useState('');
  const [metricFilter, setMetricFilter] = useState('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [sortField, setSortField] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEvents = useCallback(async (page = 1) => {
    try {
      setIsLoading(true);
      setError(null);

      const params = {
        page,
        per_page: pagination.per_page,
        sort: sortField,
        order: sortOrder
      };
      if (search.trim()) params.search = search.trim();
      if (eventTypeFilter) params.event_type = eventTypeFilter;
      if (metricFilter.trim()) params.metric_name = metricFilter.trim();
      if (fromDate) params.from_date = fromDate;
      if (toDate) params.to_date = toDate;

      const response = await eventApi.getEvents(params);
      const resData = response.data || response;
      const eventList = Array.isArray(resData) ? resData : (resData.events || resData.items || []);

      setEvents(eventList);

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
          total: eventList.length,
          pages: 1
        }));
      }
    } catch (err) {
      console.error('Failed to fetch events:', err);
      setError('Failed to load telemetry events.');
    } finally {
      setIsLoading(false);
    }
  }, [search, eventTypeFilter, metricFilter, fromDate, toDate, sortField, sortOrder, pagination.per_page]);

  useEffect(() => {
    fetchEvents(1);
  }, [fetchEvents]);

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= pagination.pages) {
      fetchEvents(newPage);
    }
  };

  return (
    <Layout title="Telemetry Events Log">
      <ErrorMessage message={error} onRetry={() => fetchEvents(pagination.page)} />

      <div className="table-card">
        {/* Filters and Search Bar */}
        <div className="table-header-bar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap', flex: 1 }}>
            <div className="search-input-wrapper">
              <Search size={16} />
              <input
                type="text"
                className="form-control"
                placeholder="Search event messages..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
              <Filter size={16} color="var(--text-dim)" />
              <select
                className="select-control"
                value={eventTypeFilter}
                onChange={(e) => setEventTypeFilter(e.target.value)}
              >
                <option value="">All Event Types</option>
                <option value="TEMPERATURE">TEMPERATURE</option>
                <option value="HUMIDITY">HUMIDITY</option>
                <option value="CPU_USAGE">CPU_USAGE</option>
                <option value="MEMORY_USAGE">MEMORY_USAGE</option>
                <option value="SMOKE">SMOKE</option>
                <option value="SYSTEM_ERROR">SYSTEM_ERROR</option>
                <option value="STATUS_CHANGE">STATUS_CHANGE</option>
              </select>

              <input
                type="text"
                className="form-control"
                placeholder="Metric..."
                style={{ width: '130px' }}
                value={metricFilter}
                onChange={(e) => setMetricFilter(e.target.value)}
              />

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                <Calendar size={14} color="var(--text-dim)" />
                <input
                  type="date"
                  className="form-control"
                  style={{ width: '135px', padding: '0.45rem' }}
                  value={fromDate}
                  onChange={(e) => setFromDate(e.target.value)}
                  title="From Date"
                />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>to</span>
                <input
                  type="date"
                  className="form-control"
                  style={{ width: '135px', padding: '0.45rem' }}
                  value={toDate}
                  onChange={(e) => setToDate(e.target.value)}
                  title="To Date"
                />
              </div>

              <select
                className="select-control"
                value={`${sortField}-${sortOrder}`}
                onChange={(e) => {
                  const [field, order] = e.target.value.split('-');
                  setSortField(field);
                  setSortOrder(order);
                }}
              >
                <option value="timestamp-desc">Newest First</option>
                <option value="timestamp-asc">Oldest First</option>
                <option value="metric_value-desc">Highest Value</option>
                <option value="metric_value-asc">Lowest Value</option>
              </select>
            </div>
          </div>
        </div>

        {/* Event Table */}
        <EventTable events={events} isLoading={isLoading} />

        {/* Pagination Bar */}
        {pagination.pages > 1 && (
          <div className="pagination">
            <span>
              Showing Page <strong>{pagination.page}</strong> of <strong>{pagination.pages}</strong> ({pagination.total || events.length} total)
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

export default Events;
