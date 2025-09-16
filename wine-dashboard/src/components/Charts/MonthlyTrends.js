// Charts/MonthlyTrends.js
import React from "react";
import Plot from "react-plotly.js";
import moment from "moment";

function MonthlyTrends({ data }) {
  // Aggregate data by YEAR + month
  const monthlyData = {};
  data.forEach(row => {
    const dateKey = moment(`${row.YEAR}-${row.month_name}-01`, "YYYY-MMMM-DD").format("YYYY-MM-DD");
    if (!monthlyData[dateKey]) monthlyData[dateKey] = { retail: 0, warehouse: 0 };
    monthlyData[dateKey].retail += row['RETAIL SALES'] || 0;
    monthlyData[dateKey].warehouse += row['WAREHOUSE SALES'] || 0;
  });

  const dates = Object.keys(monthlyData).sort();
  const retailSales = dates.map(d => monthlyData[d].retail);
  const warehouseSales = dates.map(d => monthlyData[d].warehouse);

  return (
    <Plot
      data={[
        {
          x: dates,
          y: retailSales,
          type: "scatter",
          mode: "lines+markers",
          name: "Control State Depletions",
          line: { color: "#8B0000", width: 3 },
        },
        {
          x: dates,
          y: warehouseSales,
          type: "scatter",
          mode: "lines+markers",
          name: "Off-Premise Channel",
          line: { color: "#DEB887", width: 3 },
        },
      ]}
      layout={{
        title: "Monthly Sales Performance: Control State vs Off-Premise",
        xaxis: { title: "Date" },
        yaxis: { title: "Depletions (Cases)" },
        hovermode: "x unified",
        height: 500,
      }}
      style={{ width: "100%" }}
    />
  );
}

export default MonthlyTrends;
