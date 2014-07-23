var SimpleBarChart = function (options) {
	this.margin = options.margin; 
	this.width = options.width - this.margin.left - this.margin.right; 
	this.height = options.height - this.margin.bottom - this.margin.top; 
	this.svgContainer = options.svgContainer; 
	this.data = options.data; 
	this.colorfn = options.colorfn;
	this.yValue = options.yValue; 
	this.xValue = options.xValue; 
	this.space = options.space; 
	this.mean = options.mean; 
	this.meanLineText = options.meanLineText; 
	this.showTip = options.showTip; 
	this.showLabels = options.showLabels; 
	this.showValues = options.showValues;
	this.useNumericAxis = options.useNumericAxis; 
	this.tickValues = options.tickValues; 
	this.valuesFontSize = options.valuesFontSize; 
	this.tickValuesFontSize = options.tickValuesFontSize; 
	
	if (typeof this.showTip == 'undefined') this.showTip = false;
	if (typeof this.showLabels == 'undefined') this.showLabels = false;
	if (typeof this.showValues == 'undefined') this.showValues = false; 
	if (typeof this.useNumericAxis == 'undefined') this.useNumericAxis = false; 
	if (typeof this.valuesFontSize == 'undefined') this.valuesFontSize = 14;
	if (typeof this.tickValuesFontSize == 'undefined') this.tickValuesFontSize = 10;
	
	/** Event Handlers **/ 
	this.mouseover = options.mouseover; 
	this.mouseout = options.mouseout; 
	this.click = options.click; 
	
	if (typeof this.mouseover == 'undefined') this.mouseover = function(){};
	if (typeof this.mouseout == 'undefined') this.mouseout = function(){}; 
	if (typeof this.click == 'undefined') this.click = function(){}; 
	
	if (typeof this.space == 'undefined') this.space = 0.1; 
	
	this.x = d3.scale.ordinal().rangeBands([0, this.width], this.space); 
	this.y = d3.scale.linear().range([this.height, 0]); 
	
	this.svg = null; 
	
	this.tip = d3.tip()
	  .attr('class', 'd3-tip')
	  .offset([-10, 0])
	  .html(function(d) {
	    return "<div style='color:#fff; max-width: 200px; font-weight: normal; text-align: center;'>" + d.text + "</div>";
	  });
	
	this.format = d3.format(".01%");
}

SimpleBarChart.prototype.initialize = function () {
	var chart = this;
	console.log(this);
	
	this.svg = d3.select(this.svgContainer)
		.append("svg")
	    .attr("width", this.width + this.margin.left + this.margin.right)
	    .attr("height", this.height + this.margin.top + this.margin.bottom)
	 	.append("g")
	    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
	
	this.svg.call(this.tip);
		
	this.x.domain(this.data.map(function (d) { return chart.xValue(d) }));
	this.y.domain([0, d3.max(this.data, function(d) { return chart.yValue(d) })]); 
	
	if (this.showLabels) {
		if (!this.useNumericAxis) {
			this.xAxis = d3.svg.axis()
			    .scale(this.x)
			    .orient("bottom")
				.tickSize(0);
			
			this.svg.append("g")
				.attr("class", "x axis")
		    	.attr("transform", "translate(0," + this.height + ")")
		    	.call(this.xAxis)
				.selectAll('text')
				.attr('dy', '10');
		} else {
			var spacing = this.width / this.data.length; 
			this.svg.append('g')
				.attr('class', 'x axis')
				.attr("transform", "translate(0," + this.height + ")")
				.selectAll('text')
				.data(this.tickValues)
				.enter().append('text')
				.attr('x', function (d, i) { return i * spacing })
				.attr('dy', '12')
				.attr('text-anchor', 'middle')
				.attr('font-size', this.tickValuesFontSize)
				.attr('fill', 'gray')
				.text(function (d, i) { return chart.tickValues[i]; });
		}
	}
	
	this.svg.selectAll(".bar")
		.data(this.data)
		.enter().append("rect")
		.attr("class", "bar")
		.attr("x", function(d) { return chart.x(chart.xValue(d)); })
		.attr("width", this.x.rangeBand())
		.attr("y", this.height)
		.attr("height", 0)
		.attr('fill', this.colorfn)
		.on('click', this.click)
		.on('mouseover', function (d, i) { 
			chart.mouseover(d, i); 
			if (chart.showTip) chart.tip.show(d, this); 
		})
		.on('mouseout', function (d, i) { 
			chart.mouseout(d, i); 
			if (chart.showTip) chart.tip.hide(d, this); 
		})
		.transition()
		.duration(700)
		.attr('x', function (d) {return chart.x(chart.xValue(d));})
		.attr("y", function(d) {return chart.y(chart.yValue(d)); })
		.attr("height", function(d) { return chart.height - chart.y(chart.yValue(d)); });
	
	if (typeof this.mean != 'undefined') {
		this.meanLine = d3.svg.line()
			.x(function (d) { return d[0] })
			.y(function (d) { return d[1] }); 
		var lineData = [[0, this.y(this.mean)], [this.width, this.y(this.mean)]]

		this.svg.append('path')
			.attr('d', this.meanLine(lineData))
			.attr('stroke', 'red')
			.attr('class', 'mean-line')
			.attr('stroke-width', 0.8)
			.attr('stroke-dasharray', "5 2");
		
		this.svg.append('text')
			.attr('x', 0)
			.attr('y', this.y(this.mean) - 5)
			.attr('fill', 'rgb(255, 100, 100)')
			.attr('font-weight', 5)
			.attr('class', 'mean-line-text')
			.text(function () {
				if (typeof chart.meanLineText != 'undefined') {
					return chart.meanLineText; 
				}
				return 'Average (' + chart.format(chart.mean) + ')';
			});
	}
	
	if (this.showValues) {
		this.svg.selectAll('.value')
			.data(this.data)
			.enter().append('text')
			.attr('class', 'value')
			.attr('x', function (d, i) {return chart.x(chart.xValue(d)) + chart.x.rangeBand() / 2; })
			.attr('y', function (d, i) { return chart.y(chart.yValue(d)) - 5; })
			.text(function (d) { return chart.format(chart.yValue(d));})
			.attr('font-size', this.valuesFontSize)
			.attr('fill', 'gray')
			.attr('text-anchor', 'middle')
	}
}

SimpleBarChart.prototype.updateData = function (options) {
	this.data = options.data;
	if (typeof options.colorfn != 'undefined') {
		this.colorfn = options.colorfn;
	}
	this.mean = options.mean; 
	this.meanLineText = options.meanLineText;
	var chart = this; 
	
	this.x.domain(this.data.map(function (d) { return chart.xValue(d); }));
	this.y.domain([0, d3.max(this.data, function(d) { return chart.yValue(d) })]); 
	
	var d3data = this.svg.selectAll('.bar').data(this.data)
	d3data.enter().append('rect').attr('class', 'bar'); 
	d3data.exit().remove(); 
	
	this.svg.selectAll('.bar')
		.on('click', this.click)
		.on('mouseover', function (d, i) { 
			chart.mouseover(d, i); 
			if (chart.showTip) chart.tip.show(d, this); 
		})
		.on('mouseout', function (d, i) { 
			chart.mouseout(d, i); 
			if (chart.showTip) chart.tip.hide(d, this); 
		})
		.transition()
		.attr('fill',this.colorfn)
		.attr('x', function (d) {return chart.x(chart.xValue(d));})
		.attr("y", function(d) {return chart.y(chart.yValue(d)); })
		.attr('width', this.x.rangeBand())
		.attr("height", function(d) { return chart.height - chart.y(chart.yValue(d)); });
	
	if (typeof this.mean != 'undefined') {
		var lineData = [[0, this.y(this.mean)], [this.width, this.y(this.mean)]]; 

		this.svg.select('.mean-line')
			.transition()
			.attr('d', this.meanLine(lineData));
		
		this.svg.select('.mean-line-text')
			.text(function () {
				if (typeof chart.meanLineText != 'undefined') {
					return chart.meanLineText; 
				}
				return 'Average (' + chart.format(chart.mean) + ')';
			})
			.transition()
			.attr('y', this.y(this.mean) - 5);
	}
	
	if (this.showValues) {
		this.svg.selectAll('.value')
			.data(this.data)
			.transition()
			.attr('x', function (d, i) {return chart.x(chart.xValue(d)) + chart.x.rangeBand() / 2; })
			.attr('y', function (d, i) { return chart.y(chart.yValue(d)) - 5; })
			.text(function (d) { return chart.format(chart.yValue(d));});
	}
}

SimpleBarChart.prototype.highlight = function (start, length) {
	this.svg.selectAll('.bar')
	.transition()
	.duration(100)
	.delay(function (d, i) {
		if (i >= start - 5 && i < start) {
			return (i - (start - 5)) * 50;
		} 
		if (i >= start + length - 5 && i < start + length) {
			return (5 - (start + length - i)) * 50; 
		}
		return 0;
	})
	.attr('fill', function (d, i) {
		if (i >= start && i < start + length) {
			return 'red';
		}
		return '#DEDEDE';
	});
}

/*******************************************************************
********************* === Bar Chart ==== ***************************
********************************************************************/

var D3BarChart = function (options) {
	/** Initialize Variables **/ 

	this.margin = options.margin; 
	this.width = options.width; 
	this.height = options.height;
	this.svgContainer = options.svgContainer; 
	this.showPercentage = options.showPercentage; 
	this.maxItems = options.maxItems;
	this.svg = null;
	this.datumKey = options.datumKey; 
	this.datumValue = options.datumValue;
	this.referenceData = options.referenceData; 
	this.data = options.data; 
	this.totalCount = options.totalCount; 
	this.refTotalCount = options.refTotalCount;
	this.colorFunction = options.colorFunction; 
	this.isSameData = false;
	this.datumKeyToDescMap = options.datumKeyToDescMap; 
	this.numTicks = options.numTicks; 
	this.onmouseover = options.onmouseover; 
	this.onmouseout = options.onmouseout; 
	this.yTitle = options.yTitle; 
	
	if (typeof this.onmouseover == 'undefined') this.onmouseover = function () {}; 
	if (typeof this.onmouseout == 'undefined') this.onmouseout = function () {};
	if (typeof this.yTitle == 'undefined') this.yTitle = "Frequency"; 

	var format; 
	if (this.showPercentage) {
		format = d3.format(".01%");
	} else {
		format = d3.format(".0f");
	}

	this.x = d3.scale.ordinal()
	    .rangeRoundBands([0, this.width], .1);

	this.y = d3.scale.linear()
	    .range([this.height, 0]);

	this.xAxis = d3.svg.axis()
	    .scale(this.x)
	    .orient("bottom");

	this.yAxis = d3.svg.axis()
	    .scale(this.y)
	    .orient("left")
	    .tickFormat(format);
		
	if (typeof this.numTicks !== 'undefined') {
		this.yAxis = this.yAxis.ticks(this.numTicks); 
	}
	var chart = this;

	this.tip = d3.tip()
	  .attr('class', 'd3-tip')
	  .offset([-10, 0])
	  .html(function(d) {
	    return "<div style='color:#fff; max-width: 200px; text-align: center;'>" + chart.datumKeyToDescMap[d[chart.datumKey]] + "</div>";
	  });


}

D3BarChart.prototype.initialize = function () {
	var chart = this;

	this.svg = d3.select(this.svgContainer)
		.append("svg")
	    .attr("width", this.width + this.margin.left + this.margin.right)
	    .attr("height", this.height + this.margin.top + this.margin.bottom)
	 	.append("g")
	    .attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
	
	this.svg.call(this.tip);

	this.x.domain(this.data.map(function (d) { return d[chart.datumKey] }));
	this.y.domain([0, d3.max(this.data, function(d) { return d[chart.datumValue] / chart.totalCount })]); 
	//y.domain([0, 0.25]);
	// this.svg.append("g")
	// 	.attr("class", "x axis")
 //    	.attr("transform", "translate(0," + this.height + ")")
 //    	.call(this.xAxis)
 //    	.selectAll('text')
 //    	.attr('dy', '0.5em')
 //    	.attr('dx', '-1.5em')
 //    	.attr('transform', 'rotate(-65)');

	this.svg.append("g")
		.attr("class", "y axis")
		.call(this.yAxis)
		.append("text")
		//.attr("transform", "rotate(-90)")
		.attr("y", 6)
		.attr('x', 0)
		.attr('dx', -30)
		.attr("dy", "-1.71em")
		// .style("text-anchor", "end")
		.text(this.yTitle);

	 this.svg.append("g")
	 	.attr('class', 'layer1');
	 this.svg.append("g")
	 	.attr('class', 'layer2');

	this.svg.select('.layer2')
		.selectAll(".bar")
		.data(this.data)
		.enter().append("rect")
		.attr("class", "bar")
		.attr("x", function(d) { return chart.x(d[chart.datumKey]); })
		.attr("width", this.x.rangeBand())
		.attr("y", this.height)
		.attr('opacity', '0.75')
		.attr("height", 0)
		.on('mouseover', function (d, i) { chart.tip.show(d); chart.onmouseover(d, i); })
		.on('mouseout', function (d, i) { chart.tip.hide(); chart.onmouseout(d, i); })
		.transition()
		.delay(function (d, i) { return i * 10 })
		.attr('x', function (d) { return chart.x(d[chart.datumKey]);})
		.attr("y", function(d) { return chart.y(d[chart.datumValue] / chart.totalCount); })
		.attr("height", function(d) { return chart.height - chart.y(d[chart.datumValue] / chart.totalCount); })
		.duration(700)
		.attr('fill', function (d) { return chart.colorFunction(d)});

	this.svg.select('.layer1')
		.selectAll(".bar")
		.data(this.referenceData)
		.enter().append("rect")
		.attr("class", "bar")
		.attr("x", function(d) { return chart.x(d[chart.datumKey]); })
		.attr("width", this.x.rangeBand())
		.attr("y", this.height)
		.attr("height", 0)
		.attr('opacity', '0.75')
		// .on('mouseover', function (d, i) { chart.tip.show(d); chart.onmouseover(d, i); })
		// .on('mouseout', function (d, i) { chart.tip.hide(); chart.onmouseout(d, i); })
		.transition()
		.delay(function (d, i) { return i * 10 })
		.attr('x', function (d) { return chart.x(d[chart.datumKey]);})
		.attr("y", function(d) { return chart.y(d[chart.datumValue] / chart.refTotalCount); })
		.attr("height", function(d) { return chart.height - chart.y(d[chart.datumValue] / chart.refTotalCount); })
		.duration(700)
		.attr('fill', function (d) { return chart.colorFunction(d)});
}

D3BarChart.prototype.updateData = function (options) {
	console.log(options);
	var newData = options.data; 
	var newRefData = options.referenceData; 
	console.log(newData, newRefData);
	var newDataTotalCount = options.totalCount; 
	var newRefDataTotalCount = options.refTotalCount; 
	this.isSameData = options.isSameData; 


	var chart = this;

	this.x.domain(newData.map(function (d) { return d[chart.datumKey] }));
	var dataMaxY = d3.max(newData, function (d) { 
		if (newDataTotalCount == 0) return 0; 
		return d[chart.datumValue] / newDataTotalCount 
	});
	var refDataMaxY = d3.max(newRefData, function (d) { 
		if (newRefDataTotalCount == 0) return 0;
		return d[chart.datumValue] / newRefDataTotalCount 
	});
	this.y.domain([0, Math.max(dataMaxY, refDataMaxY)]); 
	//y.domain([0, 0.25]);

	// this.svg.select(".x.axis")
	// 	.call(this.xAxis)
	// 	.selectAll('text')
	//     .attr('dy', '0.5em')
	//     .attr('dx', '-1.5em')
	//     .attr('transform', 'rotate(-65)'); 

	this.svg.select(".y.axis")
		.call(this.yAxis); 


	var l2 = this.svg.select('.layer2').selectAll('.bar');
	l2.data(newData)
		.enter().append('rect')
		.attr('class', 'bar');
	l2.data(newData).exit().remove(); 
		
	l1 = this.svg.select('.layer1').selectAll('.bar');
	l1.data(newRefData)
		.enter().append('rect')
		.attr('class', 'bar');
	l1.data(newRefData).exit().remove()
		
	this.svg.select('.layer2')
		.selectAll('.bar')
		.attr("width", this.x.rangeBand())
		.on('mouseover', function (d, i) { chart.tip.show(d); chart.onmouseover(d, i); })
		.on('mouseout', function (d, i) { chart.tip.hide(); chart.onmouseout(d, i); })
		.attr('opacity', 0.75)
		.transition()
		.duration(700)
		.delay(function (d, i) { return i * 50;})
		.attr("x", function (d) {return chart.x(d[chart.datumKey])})
		.attr("y", function (d) { 
			if (newDataTotalCount == 0) return chart.height;
			return chart.y(d[chart.datumValue] / newDataTotalCount
		)})
		.attr("height", function (d) { 
			if (newRefDataTotalCount == 0) return 0; 
			return chart.height - chart.y(d[chart.datumValue] / newDataTotalCount
		)})
		.attr('fill', function (d) { return chart.colorFunction(d)});

	this.svg.select('.layer1')
		.selectAll('.bar')
		.attr('width', this.x.rangeBand())
		// .on('mouseover', function (d, i) { chart.tip.show(d); chart.onmouseover(d, i); })
		// .on('mouseout', function (d, i) { chart.tip.hide(); chart.onmouseout(d, i); })
		.attr('opacity', 0.75)
		.transition()
		.duration(700)
		.attr('x', function (d) { return chart.x(d[chart.datumKey])})
		.attr('y', function (d) { 
			if (newRefDataTotalCount == 0) return chart.height;
			return chart.y(d[chart.datumValue] / newRefDataTotalCount)
		})
		.attr('height', function (d) {
			if (newRefDataTotalCount == 0) return 0;
			return chart.height - chart.y(d[chart.datumValue] / newRefDataTotalCount)
		});

	if (typeof this.isSameData == 'undefined' || !(this.isSameData)) {
		this.svg.select('.layer1').selectAll('.bar').attr('fill', 'black')
			.attr('fill', 'white')
			.attr('fill-opacity', 0.0)
			.attr('stroke', 'black')
			.attr('stroke-opacity', 0.7);
	} else {
		this.svg.select('.layer1').selectAll('.bar').attr('fill', this.colorFunction)
			.attr('opacity', 0.75)
			.attr('stroke', null);
	}
}

D3BarChart.prototype.highlight = function (fn) {
	this.svg.select('.layer2')
		.selectAll('.bar')
		.transition()
		.attr('fill', function (d) { return fn(d) }); 

	this.svg.select('.layer1')
		.selectAll('.bar')
		.transition()
		.attr('fill', function (d) {return fn(d) });
}

D3BarChart.prototype.unhighlight = function () {
	this.svg.select('.layer2')
		.selectAll('.bar')
		.transition()
		.attr('fill', this.colorFunction); 


	this.svg.select('.layer1')
		.selectAll('.bar')
		.transition()
		.attr('fill', 'white');
}

/*******************************************************************
********************* === Pie Chart ==== ***************************/

var D3PieChart = function (options) {
	this.width = 300,
	this.height = 200,
	this.radius = Math.min(this.width, this.height) / 2.1;
	console.log(this.radius); 

	this.color = d3.scale.ordinal()
	    .range(["#4ABAFF", "#8a89a6"]);

	this.arc = d3.svg.arc()
		.outerRadius(this.radius - 10)
		.innerRadius(0);

	this.pie = d3.layout.pie()
		.sort(null)
		.value(function(d) { return d.count ; });

	this.data = options.data; 
	this.svgContainer = options.svgContainer; 
	this.totalCount = 0; 
	var chart = this;
	this.data.forEach(function (d, i) { chart.totalCount += d.count });
	this.format = d3.format(".0%");
}

D3PieChart.prototype.initialize = function () {
	var chart = this; 
	
	this.svg = d3.select(this.svgContainer).append("svg")
		.attr("width", this.width)
	    .attr("height", this.height)
	  	.append("g")
	    .attr("transform", "translate(" + this.width / 2 + "," + this.height / 2 + ")");

	//var pieColors = ["#FF924A", "#a05d56"];
	var pieColors = ['#d95f0e', '#fec44f'];

	this.svg.append('g').attr('class', 'arc'); 
	this.svg.append('g').attr('class', 'label');

	this.svg.selectAll('.arc').selectAll('path')
		.data(this.pie(this.data))
		.enter()
		.append('path')
		.each(function (d) {this._current = d})
	    .attr("d", this.arc)
	    .style("fill", function(d, i) { return pieColors[i]; })
	    .style('stroke', 'white')
	    .style('stroke-width', 2)
	    .transition()
	    // .ease('quad-in-out')
	    .attrTween('d', function (a) {
	    	console.log('this: ', this._current, 'a: ', a);
			var i = d3.interpolate(this._current, a);
			var k = d3.interpolate(chart.arc.outerRadius()(), chart.radius);
			this._current = i(0);
			return function(t) { 
				chart.arc.outerRadius(k(t));
				return chart.arc(i(t)); 
			};
	    })
	    .each('end', function (d, i) {
	    	console.log(d, i);
	    	var dd = d; 
	    	var data = d.data; 
			chart.svg.selectAll('.label')
				.append('text')
			    .attr("transform", function(d) { return "translate(" + chart.arc.centroid(dd) + ")"; })
			    .attr('fill', 'white')
			    .attr('font-size', 9)
			    .attr("dy", ".35em")
			    .style("text-anchor", "middle")
			    .text(function(d) { 
			    	console.log(data.aprdrg_code);
			     	if (data.aprdrg_code == 560) {
			     		return "Vaginal (" + chart.format(data.count/chart.totalCount) + ")" ;
			     	} 
			     	return "Cesarean (" + chart.format(data.count/chart.totalCount) + ")"; 
			    });
	    })


}

D3PieChart.prototype.updateData = function (options) {
	this.totalCount = 0;
	this.data = options.data;
	var chart = this; 
	console.log(options.data);
	var pieColors = ["#4ABAFF", "#E7FF4A"];

	options.data.forEach(function (d, i) { chart.totalCount += d.count });

		var path = this.svg.selectAll('path')
		.each(function (d) { this._current = d})
	   	.data(this.pie(options.data))
		.transition()
	    .ease('quad-in-out')
	    .attrTween('d', function (a) {
	    	console.log('attrTween')
	    	console.log('this: ', this._current, 'a: ', a);
			var i = d3.interpolate(this._current, a);
			var k = d3.interpolate(chart.arc.outerRadius()(), chart.radius);
			this._current = i(0);
			return function(t) { 
				chart.arc.outerRadius(k(t));
				return chart.arc(i(t)); 
			};
	    })
	    .each('end', function (d, i) {
	    	console.log(d, i);
	    	var dd = d; 
	    	var data = d.data; 
	    	if (i == 0) {
		    	chart.svg.select('.label')
		    		.selectAll('text')
		    		.remove();
	    	}

			chart.svg.select('.label')
				.append('text')
			    .attr("transform", function(d) { return "translate(" + chart.arc.centroid(dd) + ")"; })
			    .attr('fill', 'white')
			    .attr('font-size', 9)
			    .attr("dy", ".35em")
			    .style("text-anchor", "middle")
			    .text(function(d) { 
			    	console.log(data.aprdrg_code);
			     	if (data.aprdrg_code == 560) {
			     		return "Vaginal (" + chart.format(data.count/chart.totalCount) + ")" ;
			     	} 
			     	return "Cesarean (" + chart.format(data.count/chart.totalCount) + ")"; 
			    });
	    })

}

/*******************************************************************
************************ === Circle ==== ***************************/

var CircleVis = function (options) {
	this.width = options.width; 
	this.height = options.height;
	this.dataList = options.dataList; 
	this.svgContainer = options.svgContainer;
	this.colorfn = options.colorfn; 
	this.keyDesc = options.keyDesc; 
	this.labels = options.labels; 
	this.svg = null;
	this.numVariables = options.numVariables;

	var chart = this; 
	this.tip = d3.tip()
	  .attr('class', 'd3-tip')
	  .offset([-10, 0])
	  .html(function(d) {
	  	console.log(d);
	  	return "<div style='max-width: 200px; text-align: center;'>" + chart.keyDesc[d.code] + "</div>";
	    //return "<div style='color:" + chart.colorFunction(d) + "; max-width: 200px; text-align: center;'>" + chart.datumKeyToDescMap[d[chart.datumKey]] + "</div>";
	 });
}

CircleVis.prototype.initialize = function () {
	var chart = this; 
	this.svg = d3.select(this.svgContainer).append("svg")
		.attr("width", this.width)
	    .attr("height", this.height)
	  	.append("g")
	   	.attr("transform", "translate(" + 5 + "," + 5 + ")");
	this.svg.call(this.tip);

	var dataWidth = this.width / this.dataList.length; 
	var dataHeight = this.height / this.numVariables;
	this.svg.append('path')
		.attr('class', 'hover-path')
		.attr('opacity', 0);
		
	var line = d3.svg.line()
		.x(function (d) { return d[0] })
		.y(function (d) { return d[1] })
		//.interpolate('cardinal');
		
	for (var index in this.dataList) {
		var data = this.dataList[index]; 
		var g = this.svg.append('g')
				.attr('class', 'data-'+index);
		console.log(g);
		g.selectAll('.data-circle')
			.data(data.data.slice(0, this.numVariables))
			.enter().append('circle')
			.attr('class', 'data-circle')
			.attr('cx', function (d, i) {
				return 300
			})
			.attr('cy', function (d, i) { 
				return 300; 
			})
			.attr('r', function (d) {
				return 0;
			})
		g.selectAll('.data-circle')
			.on('mouseover', this.tip.show)
			.on('mouseout', this.tip.hide)
			.transition()
			.ease('elastic', 3, 2)
			.duration(1000)
			.delay(function (d, i) {
				//return i*100;
				return Math.pow(i, 0.7)*50;
			})
			.attr('cx', function (d, i) {
				return index*dataWidth;
			})
			.attr('cy', function (d, i) { 
				return i*dataHeight + 3*dataHeight/4.0 + 10; 
			})
			.attr('r', function (d) {
				this._total_count  = data.data[0].count;
				return 5; 
				return Math.sqrt((d.count / data.data[0].count)) * 5;
			})
			.attr('fill', function (d) {
				return chart.colorfn(d)
			});
		g.selectAll('.clabel')
			.data(data.data.slice(0, this.numVariables))
			.enter().append('text')
			.attr("transform", function(d, i) { 
				var dx = index*dataWidth + 10; 
				var dy = i*dataHeight + 3*dataHeight/4.0 + 15;
				return "translate(" + dx + ',' + dy +  ")"; 
			})
			.attr('width', 100)
			.text(function (d) {
				var desc = chart.keyDesc[d.code].split(' '); 
				//return desc[0] + ' ' + desc[1] + '...'
				return chart.keyDesc[d.code] + ' (' + d.count + ')';
			})
			.attr('class', function (d) {
				return 'clabel c' + d.code;
			})
			.attr('font-size', function (d, i2) {
				return Math.pow(0.95, i2 ) * 46;
			})
			.attr('fill', function (d) {
				return chart.colorfn(d);
			})
			.on('mouseover', function (d1, i) {
				chart.svg.selectAll('.clabel').attr('font-weight', 'normal').attr('fill', 'black'); 
				chart.svg.selectAll('.c' + d1.code).attr('font-weight', 'bold').attr('fill', 'blue');
				var aItem = chart.svg.select('.data-0').select('circle:nth-child(' + (i+1).toString() + ')'); 
				var bItem = chart.svg.select('.data-1')
					.selectAll('circle')
					.filter(function (d2) { return d1.code == d2.code }); 
				
				var lineData = [
						[parseInt(aItem.attr('cx')) - 10, parseInt(aItem.attr('cy')) + 2],
						[parseInt(aItem.attr('cx')) + 3*dataWidth/4 - 10, parseInt(aItem.attr('cy')) + 2],
						[parseInt(bItem.attr('cx')) + 10, parseInt(bItem.attr('cy')) + 2],
						[parseInt(bItem.attr('cx')) + dataWidth - 10, parseInt(bItem.attr('cy')) + 2]
					];
				console.log(lineData);
				// chart.svg.selectAll('.hover-path')
				// 	//.transition()
				// 	.attr('d', line(lineData))
				// 	.attr('opacity', 1.0)
				// 	.attr('fill', 'none')
				// 	.attr('stroke', '#BFE3F5')
				// 	.attr('stroke-width', 10)
			})
		g.append('text')
			.text(this.labels[index])
			.attr('transform', function (d, i) {
				var dx =  index*dataWidth + 10;
				return 'translate(' + dx + ',' + 10 + ')';
			})
			.attr('font-weight', 'bold')
			.attr('letter-spacing', 3.0)
			.attr('font-size', 16);
			
	}
}

/*******************************************************************
*************************** === Circle2D === ***********************/

var CircleVis2D = function (options) {
	this.width = options.width; 
	this.height = options.height;
	this.data = options.data;
	this.totalCount = options.totalCount; 
	this.svgContainer = options.svgContainer;
	this.colorfn = options.colorfn; 
	this.keyDesc = options.keyDesc; 
	this.labels = options.labels; 
	this.onmouseover = options.onmouseover;
	this.onmouseout = options.onmouseout; 
	this.onclick = options.onclick;
	this.svg = null;

	var chart = this; 
	this.rowSize = 19; 
	this.colSize = 13;
	this.NUMBER_CIRCLES = this.rowSize * this.colSize; 
}

CircleVis2D.prototype.initialize = function () {
	console.log(this.width, this.height);
	var chart = this; 
	this.svg = d3.select(this.svgContainer).append("svg")
		.attr("width", this.width)
	    .attr("height", this.height)
	  	.append("g")
		.attr('transform', 'translate(10, 0)');

	var data = []; 
	var round = 0;
	for (var i in this.data) {
		var item = this.data[i];
		var count = (item.count / this.totalCount) * this.NUMBER_CIRCLES; 
		for (var j = 0; j < Math.ceil(count); j++) {
			if (round >= this.NUMBER_CIRCLES) break;
			data.push(item); 
			round++; 
		}
	}
	
	var radius = 10;
	this.radius = radius; 
	this.svg.append('g')
		.attr('class', 'circle-container')
		.selectAll('.data-circle')
		.data(data)
		.enter().append('circle')
		.attr('class', function (d) {
			var cat = 'mdc-' + d.aprmdc_code;
			return 'data-circle ' + cat; 
		})
		.attr('cx', 400)
		.attr('cy', 400)
		.attr('fill', this.colorfn)
		.attr('fill-opacity', '0.0')
		.attr('r', radius);


	this.svg.select('.circle-container')
		.selectAll('.data-circle')
		.transition()
		.ease('elastic', 1.0, 0.8)
		.duration(1000)
		.attr('cx', function (d, i) {
			return (i % chart.rowSize) * 30 + 20;
		})
		.delay(function (d, i) {
			return (i % chart.rowSize) * 5;
		})
		.attr('cy', function (d, i) {
			return Math.floor(i / chart.rowSize) * 30 + 20; 
		})
		.attr('fill-opacity', 1.0)
		.each('end', function (d, i) {
			d3.select(this)
			.on('mouseover',chart.onmouseover)
			.on('mouseout', chart.onmouseout)
			.on('click', chart.onclick);
		});
}

CircleVis2D.prototype.reset = function () {
	this.svg.selectAll('.data-circle')
	.transition()
	.duration(700)
	.attr('fill', this.colorfn)
	.attr('fill-opacity', 1.0)
	.attr('r', this.radius);
}

/*******************************************************************
*************************** === Map ==== ***************************/

var D3Map = function (MapOptions) {
	this.src = MapOptions.src; 
	this.width = MapOptions.width; 
	this.height = MapOptions.height; 
	this.svgContainer = MapOptions.svgContainer;
	this.scale = MapOptions.scale; 
	this.roads = MapOptions.roads;
	this.lookup = MapOptions.lookup; 
	this.bbox = MapOptions.bbox;
	this.mapColor = MapOptions.mapColor;
	
	if (typeof this.lookup == 'undefined') {
		this.lookup = 'nyc_boundary';
	}
	
	if (typeof this.mapColor == 'undefined') {
		this.mapColor = '#dedede';
	}
	
	/** CONSTANTS **/ 
	SCALE = 0.95; 
	
	if (typeof this.scale == 'undefined') {
		this.scale = SCALE; 
	} 
	
	SCALE = this.scale; 
	
	this.topology = null; 
	var map = this;
	
	
	/** Setup Map **/ 
	this.svg = d3.select(this.svgContainer).append('svg')
		.attr('width', this.width).attr('height', this.height);
	
	var projection = d3.geo.mercator(); 
	var path = d3.geo.path().projection(projection); 
	
	var tip = d3.tip()
	  .attr('class', 'd3-tip')
	  .offset([-10, 0])
	  .html(function(d) {
	    return "<div style='color:#fff; max-width: 200px; text-align: center; font-weight: normal;'>" + d.text + "</div>";
	  });
  	this.svg.call(tip);
	this.tip = tip; 
	  
	/***--- Public Methods ---***/
	
	this.load = function (onloadHandler) { 
		d3.json(this.src, function (error, topology) {
			console.log(topology)
			var feature = topojson.feature(topology, topology.objects[map.lookup]); 
			console.log(feature);
			if (typeof map.bbox != 'undefined') {
				handleProjectionFromBoundingBox(map.bbox,map.width, map.height);
			} else {
				handleProjection(feature, map.width, map.height); 
			}
			map.svg.append('path')
				.datum(feature)
				.attr('d', path)
				.attr('class', 'map')
				.attr('fill', map.mapColor);
				
			map.svg.append('circle').attr('class', 'location-inner'); 
			map.svg.append('circle').attr('class', 'location-outer');
			
			map.projection = projection;
			/*** Call Handler **/
			if (typeof onloadHandler != 'undefined') onloadHandler(); 
		});
	}
	
	this.loadGeoJSON = function(onloadHandler) {
		d3.json(this.src, function (error, topology) {
			console.log(topology); 
			if (typeof map.bbox != 'undefined') {
				handleProjectionFromBoundingBox(map.bbox,map.width, map.height);
			} else {
				handleProjection(topology, map.width, map.height); 
			}
			map.svg.append('path')
				.datum(topology)
				.attr('class', 'boundary')
				.attr('d', path)
				.attr('stroke', '#dedede')
				.attr('fill', map.mapColor);
			map.projection = projection;
			if (typeof map.roads != 'undefined') {
				d3.json(map.roads, function (error, topology2) {
					var feature = topojson.feature(topology2, topology2.objects[map.lookup]);
					console.log(feature);
					map.svg.append('path')
						.datum(feature)
						.attr('class', 'road')
						.attr('d', path)
						.attr('fill', 'none')
						.attr('opacity', 0.2)
						.attr('stroke', 'gray');
					if (typeof onloadHandler != 'undefined') onloadHandler();
				});
			} else {
				if (typeof onloadHandler != 'undefined') onloadHandler();
			} 
		});
	}
	
	this.highlightLocation = function (lat, lng) {
		var pt = projection([lng, lat]); 
		this.svg.select('.location-inner')
			.attr('class', 'location-inner')
			.attr('cx', pt[0])
			.attr('cy', pt[1])
			.attr('r', 0)
			.attr('fill', '#009DFF')
			.transition()
			.duration(1000)
			.ease('elastic')
			.attr('r', 2); 
		
		this.svg.select('.location-outer')
			.attr('class', 'location-outer')
			.attr('cx', pt[0])
			.attr('cy', pt[1])
			.attr('r', 0)
			.attr('fill', 'none')
			.attr('stroke', '#009DFF')
			.attr('stroke-width', 2)
			.transition()
			.duration(1000)
			.ease('elastic')
			.attr('r', 8); 
	}
	
	this.highlightLocations = function (locationsList, events, radius) {
		var mouseover = function () {}; 
		var mouseout = function () {};
		if (typeof events !== 'undefined') {
			mouseover = events.mouseover; 
			mouseout = events.mouseout; 
		}
		if (typeof radius == 'undefined') {
			radius = 4;
		}
		this.radius = radius;
		var map = this;
		this.svg.selectAll('.location')
		.data(locationsList)
		.enter().append('circle')
		.attr('class', 'location')
		.attr('cx', function (d, i) { return projection([d.lng, d.lat])[0]})
		.attr('cy', function (d, i) { return projection([d.lng, d.lat])[1]})
		// .attr('r', 0)
		// .attr('fill', 'white')
		// .attr('opacity', 0.0)
		// .transition()
		// .ease('elastic')
		// .delay(function (d, i) { return i * 20; })
		.attr('r', radius)
		.attr('fill', '#009DFF')
		.attr('opacity', 0.8);
		
		this.svg.selectAll('.location-hover')
		.data(locationsList)
		.enter().append('circle')
		.attr('class', 'location-hover')
		.attr('cx', function (d, i) { return projection([d.lng, d.lat])[0]})
		.attr('cy', function (d, i) { return projection([d.lng, d.lat])[1]})
		.attr('r', 8)
		.attr('fill-opacity', 0.0)
		.attr('stroke', 'red')
		.attr('opacity', 0.0)
		.on('mouseover', function (d, i) {
			mouseover(d, i)
			d3.select(this).attr('opacity', 1.0);
			tip.show(d);
		})
		.on('mouseout', function (d, i) {
			mouseout(d, i);
			d3.select(this).attr('opacity', 0.0); 
			tip.hide();
		});
		
	}
	
	this.updateMarkerColors = function (colorfn, opacityfn, radius) {
		if (typeof opacityfn == 'undefined') {
			opacityfn = 0.8; 
		}
		if (typeof radius != 'undefined') {
			this.radius = radius
		}
		this.svg.selectAll('.location')
			.transition()
			.attr('fill', colorfn)
			.attr('opacity', opacityfn)
			.attr('r', this.radius);
	}
	
	/***--- Private Methods ---***/
	
	function handleProjection (feature, width, height) {
		if (typeof width == 'undefined') width = map.width; 
		if (typeof height == 'undefined') height = map.height;
		
		projection.scale(1).translate([0, 0]);
		var b = path.bounds(feature),
			s = SCALE / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
			t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];
		console.log(b);
		//console.log(b, s, t);
		projection.scale(s).translate(t);
	}
	
	function handleProjectionFromBoundingBox(bbox ,width, height) {
		if (typeof width == 'undefined') width = map.width; 
		if (typeof height == 'undefined') height = map.height;
		var feature = { 
			"type": "FeatureCollection",
			  "features": [
					{ "type": "Feature",
			        "geometry": {"type": "Point", "coordinates": bbox[0]},
			        "properties": {"prop0": "value0"}
			        },
					{ "type": "Feature",
			        "geometry": {"type": "Point", "coordinates": bbox[1]},
			        "properties": {"prop0": "value0"}
			        },
				]
		};
		projection.scale(1).translate([0, 0]);
		var b = path.bounds(feature),
			s = SCALE / Math.max((b[1][0] - b[0][0]) / width, (b[1][1] - b[0][1]) / height),
			t = [(width - s * (b[1][0] + b[0][0])) / 2, (height - s * (b[1][1] + b[0][1])) / 2];
		projection.scale(s).translate(t);	 
	}
}

/** Text Warping Fix **/
function wrap(text, width) {
  text.each(function() {
    var text = d3.select(this),
        words = text.text().split(/\s+/).reverse(),
        word,
        line = [],
        lineNumber = 0,
        lineHeight = 1.1, // ems
		emToPx = 17,
        y = text.attr("y"),
		x = text.attr('x'),
        dy = parseFloat(text.attr("dy")),
        tspan = text.text(null).append("tspan").attr('x', x).attr("dy", dy + "em");
    while (word = words.pop()) {
      line.push(word);
      tspan.text(line.join(" "));
      if (tspan.node().getComputedTextLength() > width) {
        line.pop();
        tspan.text(line.join(" "));
        line = [word];
        tspan = text.append("tspan").attr('x', x).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
      }
    }
	if (lineNumber > 0) {
		text.attr('y', y - lineNumber*emToPx/ 2);
	}
  });
}

