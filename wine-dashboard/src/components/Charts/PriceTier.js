// Charts/PriceTier.js
import React from "react";
import Plot from "react-plotly.js";

function PriceTier({ data }) {
  const tierCounts = {};
  data.forEach(row => {
    const tier = row.price_tier || "Unclassified";
    tierCounts[tier] = (tierCounts[tier] || 0) + (row['RETAIL SALES'] || 0) + (row['WAREHOUSE SALES'] || 0);
  });

  const tiers = Object.keys(tierCounts).sort();
  const totals = tiers.map(t => tierCounts[t]);

  return (
    <Plot
      data={[
        {
          x: tiers,
          y: totals,
          type: "bar",
          text: totals.map(x => x.toLocaleString()),
          textposition: "outside",
          marker: { color: "#8B0000" },
        },
      ]}
      layout={{
        title: "Market Performance by Price Tier",
        xaxis: { title: "Price Tier" },
        yaxis: { title: "Total Depletions (Cases)" },
        height: 500,
      }}
      style={{ width: "100%" }}
    />
  );
}

export default PriceTier;
