// Charts/PerformanceBenchmark.js
import React from "react";
import Plot from "react-plotly.js";

function PerformanceBenchmark({ data, selectedVarieties }) {
  const perfData = {};

  data.forEach(row => {
    const variety = row.final_variety || "Unclassified";
    if (selectedVarieties && !selectedVarieties.includes(variety)) return;
    const name = row.WINE_NAME_EXTRACTED || "Unknown";
    const key = `${name} (${variety})`;
    perfData[key] = (perfData[key] || 0) + (row['RETAIL SALES'] || 0) + (row['WAREHOUSE SALES'] || 0);
  });

  const labels = Object.keys(perfData).slice(0, 10);
  const totals = labels.map(l => perfData[l]);

  // Random trend simulation
  const trends = ["Great!", "Wonderful!", "Take the L!"];
  const changes = totals.map(() => `${trends[Math.floor(Math.random() * trends.length)]} ${Math.floor(Math.random() * 40 - 15)}%`);

  return (
    <Plot
      data={[
        {
          y: labels,
          x: totals,
          type: "bar",
          orientation: "h",
          text: changes,
          textposition: "inside",
          marker: { color: "#8B0000" },
        },
      ]}
      layout={{
        title: "Top Product / Variety Performance with Trend Indicators",
        xaxis: { title: "Total Depletions ($)" },
        yaxis: { automargin: true },
        height: 500,
      }}
      style={{ width: "100%" }}
    />
  );
}

export default PerformanceBenchmark;
