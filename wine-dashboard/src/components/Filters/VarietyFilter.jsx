import React from 'react';
import Select from 'react-select';

const VarietyFilter = ({ filters, setFilters, data }) => {
  const options = [...new Set(data.map(d => d.review_variety).filter(Boolean))].sort()
                  .map(v => ({ value: v, label: v }));

  const handleChange = selected => {
    setFilters(prev => ({ ...prev, varietals: selected ? selected.map(s => s.value) : [] }));
  };

  const value = options.filter(o => filters.varietals.includes(o.value));

  return (
    <div className="filter">
      <label>Varietals:</label>
      <Select
        options={options}
        value={value}
        onChange={handleChange}
        isMulti
        isSearchable
        placeholder="Select varietals..."
      />
    </div>
  );
};

export default VarietyFilter;
