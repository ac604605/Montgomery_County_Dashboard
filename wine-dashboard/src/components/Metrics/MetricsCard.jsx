import React from 'react';

function MetricsCard({ label, value, color = "#722F37" }) {
  return (
    <div className="metrics-card" style={{ borderLeft: `4px solid ${color}`, padding: '10px' }}>
      <h3>{label}</h3>
      <p>{value}</p>
    </div>
  );
}

// This line is critical:
export default MetricsCard;
