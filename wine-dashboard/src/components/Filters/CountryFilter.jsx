import React from 'react';

function CountryFilter({ filters, setFilters, data }) {
  const countries = [...new Set(data.map(d => d.review_country).filter(Boolean))].sort();

  const handleChange = (event) => {
    const selected = Array.from(event.target.selectedOptions, option => option.value);
    setFilters(prev => ({ ...prev, countries: selected }));
  };

  return (
    <div className="filter">
      <label>Country:</label>
      <select multiple value={filters.countries} onChange={handleChange}>
        {countries.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
    </div>
  );
}

export default CountryFilter;
