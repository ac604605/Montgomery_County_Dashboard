import React, { useState, useEffect } from 'react';
import { Slider } from '@mui/material';

const PriceFilter = ({ filters, setFilters, data }) => {
  // Move all hooks to the top, before any conditional logic
  const prices = data ? data.map(d => parseFloat(d.review_price)).filter(p => !isNaN(p)) : [];
  const minPrice = prices.length > 0 ? Math.floor(Math.min(...prices, 0)) : 0;
  const maxPrice = prices.length > 0 ? Math.ceil(Math.max(...prices, 1000)) : 1000;
  
  const [range, setRange] = useState([
    filters.priceRange?.[0] || minPrice, 
    filters.priceRange?.[1] || maxPrice
  ]);
  
  useEffect(() => {
    setFilters(prev => ({ ...prev, priceRange: range }));
  }, [range, setFilters]);
  
  const handleChange = (event, newValue) => {
    setRange(newValue);
  };
  
  // Now you can do conditional rendering after all hooks
  if (!data || data.length === 0) {
    return <div>No data available</div>;
  }
  
  return (
    <div className="filter">
      <label>Price Range: ${range[0]} - ${range[1]}</label>
      <Slider
        value={range}
        onChange={handleChange}
        valueLabelDisplay="auto"
        min={minPrice}
        max={maxPrice}
        disableSwap
        sx={{ width: '100%', mt: 2 }}
      />
    </div>
  );
};

export default PriceFilter;