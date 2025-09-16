// MetricsCard.jsx
import React from 'react';
import './MetricsCard.css'; // Import CSS here

// Component function
export default function MetricsCard({ title, value }) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <p>{value}</p>
    </div>
  );
}
