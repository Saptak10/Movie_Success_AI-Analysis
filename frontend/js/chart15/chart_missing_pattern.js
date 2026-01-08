// js/chart_missing_pattern.js
// Missing Data Pattern (stripe plot) using D3 v7

function renderMissingPattern(containerId, data) {
    if (typeof d3 === "undefined") {
      console.error("D3 not loaded");
      return;
    }
  
    const container = d3.select(`#${containerId}`);
    if (container.empty()) {
      console.error("Container not found:", containerId);
      return;
    }
  
    container.selectAll("*").remove();
  
    const margin = { top: 30, right: 20, bottom: 40, left: 90 };
    const width = container.node().clientWidth || 700;
    const height = container.node().clientHeight || 260;
  
    const svg = container
      .append("svg")
      .attr("width", width)
      .attr("height", height);
  
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
  
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);
  
    const movies = Array.from(new Set(data.map(d => d.movie_index))).sort((a, b) => a - b);
    const features = Array.from(new Set(data.map(d => d.feature)));
  
    // Horizontal = features (like in your chart), vertical = movie index 1..500
    const x = d3.scaleBand()
      .domain(features)
      .range([0, innerWidth])
      .paddingInner(0.05);
  
    const y = d3.scaleLinear()
      .domain([1, d3.max(movies)])  // 1..500
      .range([0, innerHeight]);
  
    // 0 = missing (dark grey), 1 = present (light grey/white)
    const color = d3.scaleLinear()
      .domain([0, 1])
      .range(["#3a3a3a", "#f5f5f5"]);
  
    const cellHeight = innerHeight / movies.length;
  
    g.selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", d => x(d.feature))
      .attr("y", d => y(d.movie_index))
      .attr("width", x.bandwidth())
      .attr("height", cellHeight)
      .attr("fill", d => color(d.value));
  
    // Y labels (1 and 500 on the left, like the figure)
    const yAxisScale = d3.scaleLinear()
      .domain([1, d3.max(movies)])
      .range([0, innerHeight]);
  
    const yAxis = d3.axisLeft(yAxisScale)
      .tickValues([1, d3.max(movies)])
      .tickFormat(d => d.toString());
  
    g.append("g")
      .call(yAxis)
      .selectAll("text")
      .style("font-size", "11px");
  
    // X labels rotated at top (feature names)
    const xAxisTop = d3.axisTop(x).tickFormat(d => d.replace(/_/g, " "));
  
    const gx = g.append("g")
      .call(xAxisTop)
      .selectAll("text")
      .style("font-size", "10px")
      .attr("transform", "rotate(-45)")
      .attr("text-anchor", "end")
      .attr("dx", "-0.3em")
      .attr("dy", "-0.2em");
  
    // Title (small)
    svg.append("text")
      .attr("x", width / 2)
      .attr("y", 16)
      .attr("text-anchor", "middle")
      .style("font-size", "13px")
      .style("fill", "#f8f9fa")
      .text("Missing Data Pattern (Synthetic Sample)");
  }
  
  // Auto-render
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("chart-missing-pattern");
    if (container && typeof missingPatternData !== "undefined") {
      renderMissingPattern("chart-missing-pattern", missingPatternData);
    }
  });
  