// If you want an event to work on your page, 
         // you should call it inside the $(document).ready()
         $(document).ready(function(){
            // load everything you can before the data so the page do not move once data is loaded
            var margin = {top: 20, right: 20, bottom: 70, left: 100},
               width = $("#main").width() - margin.left - margin.right,
               height = 500 - margin.top - margin.bottom;



              // graph //////////////////////////////////////////////
              var graphSvg = d3.select(".graph");

              var color = d3.scaleOrdinal(d3.schemeCategory20);

              var simulation = d3.forceSimulation()
                .force("link", d3.forceLink().distance(100).id(function(d) { return d.id; }))
                .force("charge", d3.forceManyBody())
                .force("center", d3.forceCenter(width / 4, height / 2));


              d3.json("graph.json", function(error, graph) {
                if (error) throw error;

                var link = graphSvg.append("g")
                    .attr("class", "links")
                  .selectAll("line")
                  .data(graph.links)
                  .enter().append("line");
                    //.attr("stroke-width", function(d) { return Math.sqrt(d.amount); });

                var node = graphSvg.append("g")
                    .attr("class", "nodes")
                  .selectAll("circle")
                  .data(graph.nodes)
                  .enter().append("circle")
                    .attr("r", 10)
                    .attr("fill", function(d) { return color(d.group); })
                    .call(d3.drag()
                        .on("start", dragstarted)
                        .on("drag", dragged)
                        .on("end", dragended));

                node.append("title")
                  .text(function(d) { return d.id; });

                simulation
                    .nodes(graph.nodes)
                    .on("tick", ticked);

                simulation.force("link")
                    .links(graph.links);

                function ticked() {
                  link
                      .attr("x1", function(d) { return d.source.x; })
                      .attr("y1", function(d) { return d.source.y; })
                      .attr("x2", function(d) { return d.target.x; })
                      .attr("y2", function(d) { return d.target.y; });

                  node
                      .attr("cx", function(d) { return d.x; })
                      .attr("cy", function(d) { return d.y; });
                }

              });

              function dragstarted(d) {
                if (!d3.event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
              }

              function dragged(d) {
                d.fx = d3.event.x;
                d.fy = d3.event.y;
              }

              function dragended(d) {
                if (!d3.event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
              }





            /// CHARTS ////////////////////////

            var xscale = d3.scaleBand()
               .rangeRound([0, width])
               .paddingInner(0.1);
            // scale y
            var yscale = d3.scaleLinear()
               .range([height,0]);

            // Setup the tool tip.  Note that this is just one example, and that many styling options are available.
            // See original documentation for more details on styling: http://labratrevenge.com/d3-tip/
            var tool_tip = d3.tip()
               .attr("class", "d3-tip")
               .offset([-8, 0])
               .html(function(d) { return "Amount: " + d.value / 1000000 + " Millions.<br>Holding: " + d.link; });

            var chart = d3.select(".chart")
               .attr("width", width + margin.left + margin.right)
               .attr("height", height + margin.top + margin.bottom)
               .append("g")
               .attr("transform", "translate(" + margin.left + "," + margin.top + ")"); // Any elements subsequently added to chart will thus inherit the margins.

            chart.call(tool_tip);

            
            var stackedChart = d3.select(".stacked")
               .attr("width", width + margin.left + margin.right)
               .attr("height", height + margin.top + margin.bottom)
               .append("g")
               .attr("transform", "translate(" + margin.left + "," + margin.top + ")"); // Any elements subsequently added to chart will thus inherit the margins.
             
            
            // use d3 to load data from file
            d3.json("holdings_list.json", function(error, data) {
               /*if(error) { $("#floating_alert").append('<div class="alert alert-danger float-right alert-trim" role="alert" data-alert="alert">  <!-- singular --><a class="close" data-dismiss="alert" style="padding-left:1em;">x</a>' + error + '</div><br>'); }
               else { $("#floating_alert").append('<div class="alert alert-success float-right alert-trim" role="alert" data-alert="alert">  <!-- singular --><a class="close" data-dismiss="alert" style="padding-left:1em;">x</a>Data loaded successfully.</div><br>'); }*/

               // Not grouped chart

               var dataset = [];
               data.forEach(function(d){
                  dataset.push({id:d.pk,security:d.fields.security,value:parseFloat(d.fields.amount),link:d.fields.party_from + " -> " + d.fields.party_to});
               });

               xscale.domain(dataset.map(function(d) { return d.id; }));
               yscale.domain([0, d3.max(dataset, function(d) { return d.value; })]);

               

               var bar = chart.selectAll("g")
                  .data(dataset)
                  .enter().append("g")
                  .attr("transform", function(d, i) { return "translate(" + xscale(d.id) + ",0)"; }); // scale on d.link to stack same links on each other

               bar.append("rect")
                  .attr("y", function(d) { return yscale(d.value); })
                  .attr("height", function(d) { return height - yscale(d.value); })
                  .attr("width", xscale.bandwidth())
                  .on('mouseover', tool_tip.show)
                  .on('mouseout', tool_tip.hide);

               bar.append("text")
                  .attr("x", xscale.bandwidth())
                  .attr("y", function(d) { return yscale(d.value) + 3; })
                  .attr("dy", ".75em")
                  .text(function(d) { return d.value / 1000000; });

               // add the x axis
               chart.append("g")
                  .attr("transform", "translate(0," + height + ")")
                  .call(d3.axisBottom(xscale));
               // text label for the x axis
               chart.append("text")             
                  .attr("transform",
                        "translate(" + (width/2) + " ," + 
                                       (height + margin.top + 20) + ")")
                  .attr("style" ,"fill:black;")
                  .style("text-anchor", "middle")
                  .text("Holdings");

               // Add the y Axis
               chart.append("g")
                  .call(d3.axisLeft(yscale).ticks(null, "s"));

               // text label for the y axis
               chart.append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 0 - margin.left)
                  .attr("x",0 - (height / 2))
                  .attr("dy", "1em")
                  .attr("style" ,"fill:black;")
                  .style("text-anchor", "middle")
                  .text("Value, in millions."); 
               
               // Stacked chart ////////////////////////////////////////////////////

               var stacked_tip = d3.tip()
                 .attr("class", "d3-tip")
                 .offset([-8, 0])
                 .html(function(d) { return d[1]-d[0]});

                var svg = d3.select(".stacked"),
                  g = svg.append("g").attr("transform", "translate(" + margin.left + "," + margin.top + ")");

                svg.call(stacked_tip);

                var z = d3.scaleOrdinal(d3.schemeCategory20);



                var objects = groupBy(dataset, 'link');
                var stackedData = [];
                var stackedKeys = [];

                for (var key in objects) {
                  //console.log(key);
                  //var dict = {"link":key};
                  for (item in objects[key]) {
                    //console.log(objects[key][item]['value']);  
                    if (!(objects[key][item]['id'] in stackedKeys)) {
                      stackedKeys.push(objects[key][item]['id']);
                    }
                    //dict[objects[key][item]['id']] = objects[key][item]['value'];
                  };
                  //stackedData.push(dict);
                };
                for (var key in objects) {
                  //console.log(key);
                  var dict = {"link":key};
                  for (k in stackedKeys) {
                    dict[stackedKeys[k]] = 0;
                  }
                  for (item in objects[key]) {
                    //console.log(objects[key][item]['value']);
                    dict[objects[key][item]['id']] = objects[key][item]['value'];
                  };
                  stackedData.push(dict);
                };

                //console.log(stackedKeys);
                //console.log(stackedData);
                xscale.domain(stackedData.map(function(d) { return d.link; }));
                //yscale.domain([0, d3.max(stackedData, function(d) { return d.total; })]).nice();
                //z.domain(stackedKeys);

                // stack = d3.stack().keys([0,1,2,3]);
                /*var stack = d3.stack()
                    .keys(stackedKeys)
                    .order(d3.stackOrderNone)
                    .offset(d3.stackOffsetNone);*/

                //var series = stack(stackedData); // d3.stack().keys(keys)(data)

                //console.log(series);

                g.selectAll(".serie")
                  .data(d3.stack().keys(stackedKeys)(stackedData))
                  .enter().append("g")
                  .attr("class", "serie")
                  .attr("fill", function(d) { return z(d.key); })
                  .selectAll("rect")
                  .data(function(d) { return d; })
                  .enter().append("rect")
                  .attr("x", function(d) { return xscale(d.data.link); })
                  .attr("y", function(d) { return yscale(d[1]); })
                  .attr("height", function(d) { return yscale(d[0]) - yscale(d[1]); })
                  .attr("width", xscale.bandwidth())
                  .on('mouseover', stacked_tip.show)
                  .on('mouseout', stacked_tip.hide);

                // add the axis
               g.append("g")
                  .attr("transform", "translate(0," + height + ")")
                  .call(d3.axisBottom(xscale))
                  
                g.append("text")             
                  .attr("transform",
                        "translate(" + (width/2) + " ," + 
                                       (height + margin.top + 20) + ")")
                  .attr("style" ,"fill:black;")
                  .style("text-anchor", "middle")
                  .text("Stacked Holdings");

                g.append("g")
                  .call(d3.axisLeft(yscale).ticks(null, "s"))
                  .append("text")
                  .attr("transform", "rotate(-90)")
                  .attr("y", 0 - margin.left)
                  .attr("x",0 - (height / 2))
                  .attr("dy", "1em")
                  .attr("style" ,"fill:black;")
                  .style("text-anchor", "middle")
                  .text("Value, in millions.");    

            });

            var groupBy = function(xs, key) {
              return xs.reduce(function(rv, x) {
                (rv[x[key]] = rv[x[key]] || []).push(x);
                return rv;
              }, {});
            };
               
         });