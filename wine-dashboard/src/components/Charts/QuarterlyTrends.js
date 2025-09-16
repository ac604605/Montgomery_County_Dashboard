// Charts/QuarterlyTrends.js
import React from "react";
import Plot from "react-plotly.js";

function QuarterlyTrends({ data }) {
  const quarterlyData = {};
  data.forEach(row => {
    const key = `${row.YEAR}-${row.quarter}`;
    if (!quarterlyData[key]) quarterlyData[key] = 0;
    quarterlyData[key] += (row['RETAIL SALES'] || 0) + (row['WAREHOUSE SALES'] || 0);
  });

  const quarters = ["Q1", "Q2", "Q3", "Q4"];
  const colorMap = { Q1: "#228B22", Q2: "#8B0000", Q3: "#DEB887", Q4: "#191970" };

  const traces = quarters.map(q => {
    const x = [];
    const y = [];
    Object.keys(quarterlyData).forEach(key => {
      if (key.endsWith(q)) {
        x.push(key.split("-")[0]); // year
        y.push(quarterlyData[key]);
      }
    });
    return { x, y, type: "scatter", mode: "lines+markers", name: q, line: { color: colorMap[q] } };
  });

  return (
    <Plot
      data={traces}
      layout={{
        title: "Quarterly Performance Trends",
        xaxis: { title: "Year" },
        yaxis: { title: "Total Depletions ($)" },
        height: 500,
      }}
      style={{ width: "100%" }}
    />
  );
}

export default QuarterlyTrends;
