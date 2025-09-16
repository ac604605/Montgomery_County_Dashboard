import React from 'react';

function YearFilter({ filters, setFilters, data }) {
  const years = [...new Set(data.map(d => d.YEAR))].sort((a, b) => b - a); // descending

  const handleChange = (event) => {
    const selected = Array.from(event.target.selectedOptions, option => parseInt(option.value));
    setFilters(prev => ({ ...prev, years: selected }));
  };

  return (
    <div className="filter">
      <label>Year:</label>
      <select multiple value={filters.years} onChange={handleChange}>
        {years.map(y => <option key={y} value={y}>{y}</option>)}
      </select>
    </div>
  );
}

export default YearFilter;
