import React, { useState, useEffect } from 'react';
import YearFilter from './components/Filters/YearFilter';
import MonthFilter from './components/Filters/MonthFilter';
import ItemTypeFilter from './components/Filters/ItemTypeFilter';
import PriceFilter from './components/Filters/PriceFilter';
import VarietyFilter from './components/Filters/VarietyFilter';
import CountryFilter from './components/Filters/CountryFilter';
import SupplierFilter from './components/Filters/SupplierFilter';
import RegionFilter from './components/Filters/RegionFilter';
import WineryFilter from './components/Filters/WineryFilter';
import MetricsCard from './components/Metrics/MetricsCard';

function App({ wineData }) {
  const [filters, setFilters] = useState({
    years: [],
    months: [],
    itemType: ['Wine'],
    priceRange: [0, 1000],
    varietals: [],
    countries: [],
    suppliers: [],
    regions: [],
    wineries: []
  });

  const [filteredData, setFilteredData] = useState(wineData);

  useEffect(() => {
    let data = [...wineData];

    if (filters.years.length) data = data.filter(d => filters.years.includes(d.YEAR));
    if (filters.months.length) data = data.filter(d => filters.months.includes(d.MONTH));
    if (filters.itemType.length && filters.itemType[0] !== 'Both')
      data = data.filter(d => d.ITEM_TYPE.toLowerCase() === filters.itemType[0].toLowerCase());
    if (filters.priceRange.length === 2)
      data = data.filter(d => {
        const price = parseFloat(d.review_price);
        return !isNaN(price) && price >= filters.priceRange[0] && price <= filters.priceRange[1];
      });
    if (filters.varietals.length) data = data.filter(d => filters.varietals.includes(d.review_variety));
    if (filters.countries.length) data = data.filter(d => filters.countries.includes(d.review_country));
    if (filters.suppliers.length) data = data.filter(d => filters.suppliers.includes(d.SUPPLIER));
    if (filters.regions.length) data = data.filter(d =>
      filters.regions.includes(d.review_region_1) || filters.regions.includes(d.review_region_2)
    );
    if (filters.wineries.length) data = data.filter(d => filters.wineries.includes(d.review_winery));

    setFilteredData(data);
  }, [filters, wineData]);

  const metrics = {
    control_state_sales: filteredData.reduce((sum, d) => sum + (d.RETAIL_SALES || 0), 0),
    licensed_retailer_sales: filteredData.reduce((sum, d) => sum + (d.WAREHOUSE_SALES || 0), 0),
    inventory_transfers: filteredData.reduce((sum, d) => sum + (d.RETAIL_TRANSFERS || 0), 0),
    unique_skus: new Set(filteredData.map(d => d['ITEM CODE'])).size,
    sparkling_volume: filteredData.reduce((sum, d) => sum + (d.total_sparkling ? 1 : 0), 0)
  };

  return (
    <div className="App">
      <header>
        <h1>Control State Wine Market Intelligence</h1>
        <p>Distribution Channel Performance & Category Analytics</p>
      </header>

      <section className="filters">
        <YearFilter filters={filters} setFilters={setFilters} data={wineData} />
        <MonthFilter filters={filters} setFilters={setFilters} data={wineData} />
        <ItemTypeFilter filters={filters} setFilters={setFilters} data={wineData} />
        <PriceFilter filters={filters} setFilters={setFilters} data={wineData} />
        <VarietyFilter filters={filters} setFilters={setFilters} data={wineData} />
        <CountryFilter filters={filters} setFilters={setFilters} data={wineData} />
        <SupplierFilter filters={filters} setFilters={setFilters} data={wineData} />
        <RegionFilter filters={filters} setFilters={setFilters} data={wineData} />
        <WineryFilter filters={filters} setFilters={setFilters} data={wineData} />
      </section>

      <section className="summary">
        <MetricsCard label="Control State" value={metrics.control_state_sales.toLocaleString()} color="#8B0000" />
        <MetricsCard label="Off-Premise" value={metrics.licensed_retailer_sales.toLocaleString()} color="#DEB887" />
        <MetricsCard label="Transfers" value={metrics.inventory_transfers.toLocaleString()} color="#722F37" />
        <MetricsCard label="Active SKUs" value={metrics.unique_skus.toLocaleString()} color="#191970" />
        <MetricsCard label="Sparkling" value={metrics.sparkling_volume.toLocaleString()} color="#228B22" />
      </section>
    </div>
  );
}

export default App;
