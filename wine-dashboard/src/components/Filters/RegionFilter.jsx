import React from 'react';
import Select from 'react-select';

const RegionFilter = ({ filters, setFilters, data }) => {
  const regions = [...new Set([
    ...data.map(d => d.review_region_1).filter(Boolean),
    ...data.map(d => d.review_region_2).filter(Boolean)
  ])].sort();

  const options = regions.map(r => ({ value: r, label: r }));

  const handleChange = selected => {
    setFilters(prev => ({ ...prev, regions: selected ? selected.map(s => s.value) : [] }));
  };

  const value = options.filter(o => filters.regions.includes(o.value));

  return (
    <div className="filter">
      <label>Region:</label>
      <Select
        options={options}
        value={value}
        onChange={handleChange}
        isMulti
        isSearchable
        placeholder="Select regions..."
      />
    </div>
  );
};

export default RegionFilter;
