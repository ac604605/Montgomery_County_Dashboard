import React from 'react';

function MonthFilter({ filters, setFilters, data }) {
  const months = [...new Set(data.map(d => d.MONTH_NAME))];

  const handleChange = (event) => {
    const selected = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, months: selected }));
  };

  return (
    <div className="filter">
      <label>Month:</label>
      <select multiple value={filters.months} onChange={handleChange}>
        {months.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
    </div>
  );
}

export default MonthFilter;
