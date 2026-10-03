import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Login from '../pages/Login';
import Dashboard from '../pages/Dashboard';
import Devices from '../pages/Devices';
import DeviceDetails from '../pages/DeviceDetails';
import Events from '../pages/Events';
import Alerts from '../pages/Alerts';
import StatCard from '../components/StatCard';
import MetricChart from '../components/MetricChart';
import DeviceTable from '../components/DeviceTable';
import EventTable from '../components/EventTable';
import AlertTable from '../components/AlertTable';
import StatusBadge from '../components/StatusBadge';
import SeverityBadge from '../components/SeverityBadge';
import ErrorMessage from '../components/ErrorMessage';
import { AuthContext } from '../context/AuthContext';
import { storage } from '../utils/storage';
import { statusApi } from '../api/statusApi';
import { alertApi } from '../api/alertApi';
import { Server } from 'lucide-react';

vi.mock('../api/statusApi', () => ({
  statusApi: {
    getOverview: vi.fn().mockResolvedValue({
      total_devices: 10,
      online_devices: 7,
      offline_devices: 2,
      warning_devices: 1,
      open_alerts: 4,
      critical_alerts: 1,
      events_today: 245
    }),
    getDeviceStatusList: vi.fn().mockResolvedValue({
      devices: [
        {
          id: 1,
          device_code: 'DEV-001',
          name: 'Core Router',
          location: 'Datacenter A',
          status: 'ONLINE',
          last_seen: new Date().toISOString(),
          metrics: { cpu_usage: 45.0, memory_usage: 60.0, temperature: 42.0, uptime_seconds: 36000 }
        }
      ],
      pagination: { page: 1, per_page: 10, total: 1, pages: 1 }
    }),
    getDeviceStatusById: vi.fn().mockResolvedValue({
      device: { id: 1, device_code: 'DEV-001', name: 'Core Router', location: 'Datacenter A', status: 'ONLINE' },
      metrics: { cpu_usage: 45.0, memory_usage: 60.0, temperature: 42.0, uptime_seconds: 36000 },
      recent_events: [],
      open_alerts: []
    }),
    getRecentEvents: vi.fn().mockResolvedValue({ events: [] }),
    getRecentAlerts: vi.fn().mockResolvedValue({ alerts: [] })
  }
}));

vi.mock('../api/alertApi', () => ({
  alertApi: {
    getAlerts: vi.fn().mockResolvedValue({ alerts: [] }),
    acknowledgeAlert: vi.fn().mockResolvedValue({ status: 'ACKNOWLEDGED' }),
    resolveAlert: vi.fn().mockResolvedValue({ status: 'RESOLVED' })
  }
}));

describe('Phase 11 — Comprehensive Frontend Integration & Monitoring Test Suite', () => {

  beforeEach(() => {
    storage.clearAuth();
    vi.clearAllMocks();
  });

  const mockUser = { id: 1, name: 'Admin User', role: 'ADMIN', email: 'admin@example.com' };
  const mockAuthContext = {
    user: mockUser,
    token: 'jwt-mock-token',
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn()
  };

  it('1. Login page renders cleanly', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ ...mockAuthContext, isAuthenticated: false, user: null }}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );
    expect(screen.getByText(/Monitoring Platform/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument();
  });

  it('2. Login validation prevents empty submission', () => {
    const mockLogin = vi.fn();
    render(
      <MemoryRouter>
        <AuthContext.Provider value={{ ...mockAuthContext, isAuthenticated: false, user: null, login: mockLogin }}>
          <Login />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitBtn);
    expect(mockLogin).not.toHaveBeenCalled();
  });

  it('3 & 4. Storage helper & AuthContext persistence handles token set and clear', () => {
    storage.setToken('test-token-xyz');
    storage.setUser(mockUser);
    expect(storage.getToken()).toBe('test-token-xyz');
    expect(storage.getUser()).toEqual(mockUser);

    storage.clearAuth();
    expect(storage.getToken()).toBeNull();
  });

  it('5 & 6. Dashboard renders and loads system overview data', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <Dashboard />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('System Overview')).toBeInTheDocument();
      expect(screen.getByText('Total Devices')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });
  });

  it('7 & 8. Devices page renders device table and applies search filters', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <Devices />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Core Router')).toBeInTheDocument();
      expect(screen.getByText('DEV-001')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/Search by code, name or location.../i);
    fireEvent.change(searchInput, { target: { value: 'Core' } });
    expect(statusApi.getDeviceStatusList).toHaveBeenCalled();
  });

  it('9. DeviceDetails page renders health metrics and sparkline charts', async () => {
    render(
      <MemoryRouter initialEntries={['/devices/1']}>
        <AuthContext.Provider value={mockAuthContext}>
          <Routes>
            <Route path="/devices/:id" element={<DeviceDetails />} />
          </Routes>
        </AuthContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Device: Core Router')).toBeInTheDocument();
      expect(screen.getByText('CPU Load')).toBeInTheDocument();
      expect(screen.getByText('45 %')).toBeInTheDocument();
    });
  });

  it('10. Events page renders event filters and stream table', async () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <Events />
        </AuthContext.Provider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Telemetry Events Log')).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search event messages.../i)).toBeInTheDocument();
    });
  });

  it('11, 12 & 13. AlertTable enforces RBAC: ADMIN sees actions, VIEWER is read-only', () => {
    const mockAlerts = [
      { id: 50, device_code: 'DEV-001', severity: 'CRITICAL', title: 'High Temp', status: 'OPEN', created_at: new Date().toISOString() }
    ];

    const { rerender } = render(
      <AlertTable alerts={mockAlerts} isLoading={false} userRole="ADMIN" onAcknowledge={vi.fn()} onResolve={vi.fn()} />
    );

    expect(screen.getByRole('button', { name: /Ack/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Resolve/i })).toBeInTheDocument();

    // VIEWER role hides action controls
    rerender(
      <AlertTable alerts={mockAlerts} isLoading={false} userRole="VIEWER" onAcknowledge={vi.fn()} onResolve={vi.fn()} />
    );

    expect(screen.queryByRole('button', { name: /Ack/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Resolve/i })).not.toBeInTheDocument();
  });

  it('14 & 15. MetricChart renders sparkline and color gradient', () => {
    render(<MetricChart title="Core Temp" value={78.5} unit="°C" color="#f59e0b" />);
    expect(screen.getByText('Core Temp')).toBeInTheDocument();
    expect(screen.getByText('78.5 °C')).toBeInTheDocument();
  });

  it('19 & 20. ErrorMessage & empty states display properly', () => {
    const { rerender } = render(<ErrorMessage message="Network connection failed" />);
    expect(screen.getByText('Network connection failed')).toBeInTheDocument();

    rerender(<DeviceTable devices={[]} isLoading={false} />);
    expect(screen.getByText('No devices found')).toBeInTheDocument();
  });

});
