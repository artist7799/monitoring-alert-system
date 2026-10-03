import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Server, Radio, Bell, LogOut, Shield } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

export const Sidebar = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { label: 'Devices', path: '/devices', icon: Server },
    { label: 'Events', path: '/events', icon: Radio },
    { label: 'Alerts', path: '/alerts', icon: Bell }
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand-icon">
          <Shield size={20} />
        </div>
        <div>
          <span className="brand-title">Monitoring Hub</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <span className="user-name">{user?.name || 'User'}</span>
          <span className="user-role-badge">{user?.role || 'VIEWER'}</span>
        </div>
        <button className="logout-btn" onClick={logout} title="Logout">
          <LogOut size={16} />
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
