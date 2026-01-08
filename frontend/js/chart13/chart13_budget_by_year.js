// js/chart_budget_by_year.js
// Movie Budget Distribution by Year – Scatter with vertical jitter

// Example data (replace with your own extracted data if available)
const budgetByYearData = [
    // early years: low budgets
    { year: 1920, budget: 1 },
    { year: 1925, budget: 2 },
    { year: 1930, budget: 3 },
    { year: 1935, budget: 2 },
    { year: 1940, budget: 4 },
    { year: 1945, budget: 3 },
    { year: 1950, budget: 5 },
    { year: 1955, budget: 6 },
    { year: 1960, budget: 8 },
    { year: 1965, budget: 12 },
    { year: 1970, budget: 15 },
    { year: 1975, budget: 20 },
    { year: 1980, budget: 30 },
    { year: 1985, budget: 40 },
    { year: 1990, budget: 60 },
    { year: 1995, budget: 80 },
    { year: 1998, budget: 90 },
    { year: 2000, budget: 110 },
    { year: 2002, budget: 130 },
    { year: 2004, budget: 150 },
    { year: 2006, budget: 170 },
    { year: 2008, budget: 180 },
    { year: 2010, budget: 200 },
    { year: 2012, budget: 220 },
    { year: 2014, budget: 250 },
    { year: 2016, budget: 260 },
    { year: 2018, budget: 280 },
    { year: 2019, budget: 300 },
    { year: 2020, budget: 250 },
    { year: 2021, budget: 400 },
    { year: 2022, budget: 320 },
    { year: 2023, budget: 350 }
    // In your real data you will have many points per year.
  ];
  
  function renderBudgetByYear(containerId, data) {
    if (typeof d3 === "undefined") {
      console.error("D3 not loaded");
      return;
    }
  
    const container = d3.select(`#${containerId}`);
    if (container.empty()) {
      console.error("Container not found:", containerId);
      return;
    }
  
    const margin = { top: 20, right: 20, bottom: 50, left: 80 };
    const width = container.node().clientWidth || 400;
    const height = container.node().clientHeight || 260;
  
    container.selectAll("*").remove();
  
    const svg = container
      .append("svg")
      .attr("width", width)
      .attr("height", height);
  
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
  
    // Scales
    const x = d3.scaleLinear()
      .domain(d3.extent(data, d => d.year))
      .range([0, innerWidth]);
  
    const y = d3.scaleLinear()
      // budgets in millions; top at ~500M
      .domain([0, d3.max(data, d => d.budget) * 1.1])
      .range([innerHeight, 0]);
  
    // Axes
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x).ticks(8).tickFormat(d3.format("d")))
      .style("font-size", "12px");
  
    g.append("g")
      .call(d3.axisLeft(y).ticks(6).tickFormat(d => `${d}M`))
      .style("font-size", "12px");
  
    // Gridlines for y
    g.append("g")
      .attr("class", "grid-lines")
      .call(d3.axisLeft(y).tickSize(-innerWidth).tickFormat(""));
  
    // Scatter points with small vertical jitter to avoid overplotting
    const jitter = 2; // pixels
    g.selectAll("circle")
      .data(data)
      .join("circle")
      .attr("cx", d => x(d.year))
      .attr("cy", d => y(d.budget) + (Math.random() - 0.5) * jitter)
      .attr("r", 3)
      .attr("fill", "#5b7fff")
      .attr("opacity", 0.4);
  
    // Axis labels
    g.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 38)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .text("Release Year");
  
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -55)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .text("Budget (USD, millions)");
  }
  
  // Auto-render when DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("chart-budget-by-year");
    if (container) {
      renderBudgetByYear("chart-budget-by-year", budgetByYearData);
    }
  });
  