// <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/d3/4.10.0/d3.min.js"></script>


d3.json("/party/count", function(error, json) {
	if (error) return console.warn(error);
  	var dataset = json;

  	var width = 150, // $(".card").width()
    height = 150,
    radius = Math.min(width, height) / 2;
    var donutWidth = 25;

	// color schemes: https://github.com/d3/d3-scale/blob/master/README.md#category-scales
	var color = d3.scaleOrdinal(d3.schemeCategory20c);

	var svg = d3.select('#partyChart')
	  .append('svg')
	  .attr('width', width)
	  .attr('height', height)
	  .append('g')
	  .attr('transform', 'translate(' + (width / 2) +  ',' + (height / 2) + ')');

	var arc = d3.arc()
	  .innerRadius(radius - donutWidth)
	  .outerRadius(radius);

	var pie = d3.pie()
	  .value(function(d) { return d.count; })
	  .sort(null);

	var path = svg.selectAll('path')
	  .data(pie(dataset))
	  .enter()
	  .append('path')
	  .attr('d', arc)
	  .attr('fill', function(d, i) {
	    return color(d.data.label);
	  });

	var legendRectSize = 12;
	var legendSpacing = 4;
	var legend = svg.selectAll('.legend')
	  .data(color.domain())
	  .enter()
	  .append('g')
	  .attr('class', 'legend')
	  .attr('transform', function(d, i) {
	    var height = legendRectSize + legendSpacing;
	    var offset =  height * color.domain().length / 2;
	    var horz = -2 * legendRectSize;
	    var vert = i * height - offset;
	    return 'translate(' + horz + ',' + vert + ')';
	  });
	legend.append('rect')
	  .attr('width', legendRectSize)
	  .attr('height', legendRectSize)
	  .style('fill', color)
	  .style('stroke', color);

	legend.append('text')
	  .attr('x', legendRectSize + legendSpacing)
	  .attr('y', legendRectSize - legendSpacing)
	  .text(function(d) { return d; });
});