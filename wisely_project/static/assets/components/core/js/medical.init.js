(function($)
{
	if (typeof charts == 'undefined') 
		return;

	charts.chart_gender = 
	{
		// chart data
		data: null,

		// will hold the chart object
		plot: null,

		// chart options
		options:
		{
			bars: {
				show:true,
				barWidth: 0.3,
				fill:1
			},
			grid: {
				show: true,
			    aboveData: false,
			    color: "#3f3f3f",
			    labelMargin: 5,
			    axisMargin: 0, 
			    borderWidth: 0,
			    borderColor:null,
			    minBorderMargin: 5,
			    clickable: true, 
			    hoverable: true,
			    autoHighlight: false,
			    mouseActiveRadius: 20,
			    backgroundColor : { }
			},
	        legend: { show: false, position: "ne", backgroundColor: null, backgroundOpacity: 0 },
	        colors: []
		},
		
		placeholder: "#chart_gender",

		// initialize
		init: function()
		{
			// apply styling
			this.options.colors = ["#D67FB0", "#4193d0"];
			this.options.grid.backgroundColor = { colors: ["transparent", "transparent"]};
			this.options.grid.borderColor = primaryColor;
			this.options.grid.color = primaryColor;
			
			//some data
			var d1 = [];
		    for (var i = 0; i <= 10; i += 1)
		        d1.push([i, parseInt(Math.random() * 30)]);
		 
		    var d2 = [];
		    for (var i = 0; i <= 10; i += 1)
		        d2.push([i, parseInt(Math.random() * 30)]);
		 
		    var ds = new Array();
		 
		    ds.push({
		     	label: "Data One",
		        data:d1,
		        bars: {order: 1}
		    });
		    ds.push({
		    	label: "Data Two",
		        data:d2,
		        bars: {order: 2}
		    });
			this.data = ds;

			this.plot = $.plot($(this.placeholder), this.data, this.options);
		}
	};
		
	$(window).on('load', function(){
		setTimeout(function(){
			charts.chart_gender.init();
		}, 100);
	});
})(jQuery);