import React from 'react';

export const StatCard = ({ title, value, description, icon: Icon, color = '#3b82f6' }) => {
  return (
    <div className="stat-card">
      <div className="stat-content">
        <span className="stat-title">{title}</span>
        <span className="stat-value">{value !== undefined && value !== null ? value : 0}</span>
        {description && <span className="stat-desc">{description}</span>}
      </div>
      {Icon && (
        <div className="stat-icon-wrapper" style={{ color: color, backgroundColor: `${color}15` }}>
          <Icon size={22} />
        </div>
      )}
    </div>
  );
};

export default StatCard;
