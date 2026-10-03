import React from 'react';

export const MetricChart = ({ title, value, unit = '%', type = 'line', history = [], color = '#3b82f6' }) => {
  const numericVal = typeof value === 'number' ? value : parseFloat(value) || 0;
  
  // Default sample history points if none provided for visual sparkline
  const points = history.length > 0 ? history : [
    Math.max(0, numericVal - 15),
    Math.max(0, numericVal - 8),
    Math.max(0, numericVal + 5),
    Math.max(0, numericVal - 3),
    numericVal
  ];

  const min = 0;
  const max = 100;
  const height = 60;
  const width = 200;

  // Compute SVG polyline points
  const svgPoints = points
    .map((val, idx) => {
      const x = (idx / (points.length - 1 || 1)) * width;
      const normalizedVal = Math.min(Math.max(val, min), max);
      const y = height - (normalizedVal / max) * height;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div style={{
      backgroundColor: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '12px',
      padding: '1.25rem',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.75rem'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {title}
        </span>
        <span className="mono" style={{ fontSize: '1.25rem', fontWeight: 700, color: color }}>
          {numericVal} {unit}
        </span>
      </div>

      {/* Progress Bar / Gauge */}
      <div style={{
        height: '6px',
        width: '100%',
        backgroundColor: 'rgba(255, 255, 255, 0.08)',
        borderRadius: '3px',
        overflow: 'hidden'
      }}>
        <div style={{
          height: '100%',
          width: `${Math.min(Math.max(numericVal, 0), 100)}%`,
          backgroundColor: color,
          borderRadius: '3px',
          transition: 'width 0.4s ease'
        }} />
      </div>

      {/* SVG Sparkline */}
      <div style={{ height: `${height}px`, width: '100%', marginTop: '0.25rem' }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '100%', overflow: 'visible' }}>
          <defs>
            <linearGradient id={`grad-${title.replace(/\s+/g, '')}`} x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0.0" />
            </linearGradient>
          </defs>
          <polygon
            points={`0,${height} ${svgPoints} ${width},${height}`}
            fill={`url(#grad-${title.replace(/\s+/g, '')})`}
          />
          <polyline
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={svgPoints}
          />
        </svg>
      </div>
    </div>
  );
};

export default MetricChart;
