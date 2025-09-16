import React from 'react';
import Select from 'react-select';

const WineryFilter = ({ filters, setFilters, data }) => {
  const options = [...new Set(data.map(d => d.review_winery).filter(Boolean))].sort()
                  .map(w => ({ value: w, label: w }));

  const handleChange = selected => {
    setFilters(prev => ({ ...prev, wineries: selected ? selected.map(s => s.value) : [] }));
  };

  const value = options.filter(o => filters.wineries.includes(o.value));

  return (
    <div className="filter">
      <label>Winery / Designation:</label>
      <Select
        options={options}
        value={value}
        onChange={handleChange}
        isMulti
        isSearchable
        placeholder="Select wineries..."
      />
    </div>
  );
};

export default WineryFilter;
