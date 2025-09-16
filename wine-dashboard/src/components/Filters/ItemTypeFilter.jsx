import React from 'react';

function ItemTypeFilter({ filters, setFilters, data }) {
  const types = [...new Set(data.map(d => d.ITEM_TYPE))].sort();

  const handleChange = (event) => {
    const selected = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, itemType: selected }));
  };

  return (
    <div className="filter">
      <label>Item Type:</label>
      <select multiple value={filters.itemType} onChange={handleChange}>
        {types.map(t => <option key={t} value={t}>{t}</option>)}
      </select>
    </div>
  );
}

export default ItemTypeFilter;
