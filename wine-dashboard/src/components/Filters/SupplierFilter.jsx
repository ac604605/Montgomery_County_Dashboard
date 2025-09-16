import React from 'react';

function SupplierFilter({ filters, setFilters, data }) {
  const suppliers = [...new Set(data.map(d => d.SUPPLIER).filter(Boolean))].sort();

  const handleChange = (event) => {
    const selected = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, suppliers: selected }));
  };

  return (
    <div className="filter">
      <label>Supplier:</label>
      <select multiple value={filters.suppliers} onChange={handleChange}>
        {suppliers.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
    </div>
  );
}

export default SupplierFilter;
