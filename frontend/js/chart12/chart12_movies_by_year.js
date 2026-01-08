// js/chart_movies_by_year.js
// Movies Collected by Release Year - Line Chart with Points

const moviesByYearData = [
    { year: 1915, count: 1 },
    { year: 1920, count: 2 },
    { year: 1925, count: 2 },
    { year: 1930, count: 3 },
    { year: 1935, count: 3 },
    { year: 1940, count: 3 },
    { year: 1945, count: 3 },
    { year: 1950, count: 5 },
    { year: 1955, count: 7 },
    { year: 1960, count: 8 },
    { year: 1965, count: 10 },
    { year: 1970, count: 12 },
    { year: 1975, count: 18 },
    { year: 1980, count: 25 },
    { year: 1985, count: 35 },
    { year: 1990, count: 50 },
    { year: 1995, count: 80 },
    { year: 2000, count: 120 },
    { year: 2005, count: 150 },
    { year: 2010, count: 180 },
    { year: 2015, count: 220 },
    { year: 2018, count: 250 },
    { year: 2019, count: 270 },
    { year: 2020, count: 280 },
    { year: 2021, count: 310 },
    { year: 2022, count: 200 }
  ];
  
  function renderMoviesByYear(containerId, data) {
    // Sort data by year
    data = data.slice().sort((a, b) => d3.ascending(a.year, b.year));
  
    const margin = { top: 20, right: 20, bottom: 50, left: 70 };
    const container = d3.select(`#${containerId}`);
    const width = container.node().clientWidth;
    const height = container.node().clientHeight;
  
    // Clear previous render
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
      .domain([0, d3.max(data, d => d.count)]).nice()
      .range([innerHeight, 0]);
  
    // Line generator with smooth curve
    const line = d3.line()
      .x(d => x(d.year))
      .y(d => y(d.count))
      .curve(d3.curveMonotoneX);
  
    // X-axis
    g.append("g")
      .attr("transform", `translate(0,${innerHeight})`)
      .call(d3.axisBottom(x)
        .ticks(8)
        .tickFormat(d3.format("d")))
      .style("font-size", "12px");
  
    // Y-axis
    g.append("g")
      .call(d3.axisLeft(y)
        .ticks(6))
      .style("font-size", "12px");
  
    // Grid lines (optional, improves readability)
    g.append("g")
      .attr("class", "grid-lines")
      .call(d3.axisLeft(y)
        .tickSize(-innerWidth)
        .tickFormat(""))
      .style("stroke", "#f0f0f0")
      .style("stroke-dasharray", "4,4");
  
    // Line path
    g.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#5b7fff")
      .attr("stroke-width", 2.5)
      .attr("d", line);
  
    // Points/dots
    g.selectAll("circle")
      .data(data)
      .join("circle")
      .attr("cx", d => x(d.year))
      .attr("cy", d => y(d.count))
      .attr("r", 3.5)
      .attr("fill", "#5b7fff")
      .attr("opacity", 0.8)
      .on("mouseover", function() {
        d3.select(this)
          .transition()
          .duration(150)
          .attr("r", 5);
      })
      .on("mouseout", function() {
        d3.select(this)
          .transition()
          .duration(150)
          .attr("r", 3.5);
      });
  
    // X-axis label
    g.append("text")
      .attr("x", innerWidth / 2)
      .attr("y", innerHeight + 40)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .style("font-size", "13px")
      .style("fill", "#333")
      .text("Year");
  
    // Y-axis label
    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("x", -innerHeight / 2)
      .attr("y", -50)
      .attr("text-anchor", "middle")
      .attr("class", "axis-label")
      .style("font-size", "13px")
      .style("fill", "#333")
      .text("Number of Movies");
  }
  
  // Initialize on DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("chart-movies-by-year");
    if (container) {
      renderMoviesByYear("chart-movies-by-year", moviesByYearData);
    }
  });