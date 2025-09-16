export function computeMetrics(data) {
  const control_state_sales = data.reduce((sum, d) => sum + (d.RETAIL_SALES || 0), 0);
  const licensed_retailer_sales = data.reduce((sum, d) => sum + (d.WAREHOUSE_SALES || 0), 0);
  const inventory_transfers = data.reduce((sum, d) => sum + (d.RETAIL_TRANSFERS || 0), 0);
  const unique_skus = new Set(data.map(d => d['ITEM CODE'])).size;
  const unique_varieties = new Set(data.map(d => d.review_variety)).size;
  const sparkling_volume = data.reduce((sum, d) => sum + (d.total_sparkling ? 1 : 0), 0); 
  return {
    control_state_sales,
    licensed_retailer_sales,
    inventory_transfers,
    unique_skus,
    unique_varieties,
    sparkling_volume,
  };
}
