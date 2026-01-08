// js/chart_completeness_heatmap.js

function renderCompletenessHeatmap(containerId, data) {
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
  
    const margin = { top: 20, right: 50, bottom: 80, left: 130 };
    const width = container.node().clientWidth || 700;
    const height = container.node().clientHeight || 320;
  
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
  
    const x = d3.scaleBand()
      .domain(movies)
      .range([0, innerWidth])
      .padding(0.02);
  
    const y = d3.scaleBand()
      .domain(features)
      .range([0, innerHeight])
      .padding(0.02);
  
    const color = d3.scaleLinear()
      .domain([0, 1])
      .range(["#b11226", "#006d2c"]);
  
    g.selectAll("rect")
      .data(data)
      .join("rect")
      .attr("x", d => x(d.movie_index))
      .attr("y", d => y(d.feature))
      .attr("width", x.bandwidth())
      .attr("height", y.bandwidth())
      .attr("fill", d => color(d.value));
  
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(
        d3.axisBottom(x)
          .tickValues(movies.filter((_, i) => i % 5 === 0))
          .tickFormat(d => d.toString())
      )
      .selectAll("text")
      .style("font-size", "9px")
      .attr("transform", "rotate(60)")
      .attr("text-anchor", "start")
      .attr("dx", "0.3em")
      .attr("dy", "0.1em");
  
    g.append("g")
      .call(d3.axisLeft(y))
      .selectAll("text")
      .style("font-size", "10px");
  
    g.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 60)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .text("Movie Index");
  
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -110)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .text("Features");
  
    const legendHeight = 140;
    const legendWidth = 12;
  
    const legendScale = d3.scaleLinear()
      .domain([0, 1])
      .range([legendHeight, 0]);
  
    const legendAxis = d3.axisRight(legendScale).ticks(5);
  
    const defs = svg.append("defs");
    const gradient = defs.append("linearGradient")
      .attr("id", "completeness-gradient")
      .attr("x1", "0%")
      .attr("y1", "100%")
      .attr("x2", "0%")
      .attr("y2", "0%");
  
    gradient.append("stop")
      .attr("offset", "0%")
      .attr("stop-color", "#b11226");
  
    gradient.append("stop")
      .attr("offset", "100%")
      .attr("stop-color", "#006d2c");
  
    const legend = svg.append("g")
      .attr("transform", `translate(${width - margin.right + 10},${margin.top})`);
  
    legend.append("rect")
      .attr("width", legendWidth)
      .attr("height", legendHeight)
      .style("fill", "url(#completeness-gradient)");
  
    legend.append("g")
      .attr("transform", `translate(${legendWidth},0)`)
      .call(legendAxis)
      .selectAll("text")
      .style("font-size", "10px");
  
    legend.append("text")
      .attr("x", -4)
      .attr("y", legendHeight + 20)
      .attr("text-anchor", "start")
      .attr("class", "axis-label")
      .text("Data Present");
  }
  
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("chart-completeness-heatmap");
    if (container && typeof completenessHeatmapData !== "undefined") {
      renderCompletenessHeatmap("chart-completeness-heatmap", completenessHeatmapData);
    }
  });
  