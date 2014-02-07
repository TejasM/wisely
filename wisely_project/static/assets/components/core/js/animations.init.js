(function($)
{

	// animate only after page finished loading
	$(window).on('load', function()
	{
		// restore visibility
		$(".layout-app, #menu, .navbar.main, #footer").css('visibility', 'visible').show();

		// disable animations on touch devices
		if (Modernizr.touch)
			return;

		// // disable animations if browser doesn't support css transitions & 3d transforms
		if (!$('html.csstransitions.csstransforms3d').length)
			return;

		// animate sidebar
		$("#menu").addClass('animated fadeInLeft');

		// animate top menu & footer
		$(".navbar.main, #footer").addClass('animated fadeInUp');

		// animate layout columns
		$(".layout-app .col-app, .row-app > [class*='col-']").not('.col-unscrollable').addClass('animated fadeInDown');

		// animate dashboard friend list
		$(".friends-list > li")
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInUp');
			}, 150*k);
		});

		// animate dashboard friend list
		$(".list-group > .list-group-item")
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInUp');
			}, 150*k);
		});

		// animate timelines
		$(".timeline-activity > li")
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this),
				b = 100,
				r = (t.parent().height() / t.parent().find('> li').length) / b,
				r = (Math.round(r) * b) - b,
				r = r < 200 ? 200 : r;
			
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated bounceInUp');
			}, r*k);
		});

		// animate statistical widgets
		$(".widget-stats")
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInDown');
			}, 200*k);
		});

		// animate generic widgets
		$(".box-generic")
		.filter(function(){
			return !$(this).parents('.timeline-activity').length;
		})
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInUp');
			}, 250*k);
		});

		// animate thumbnails
		$(".thumbnail")
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInDown');
			}, 200*k);
		});

		// animate thumbnails
		$(".thumb")
		.filter(function(index) {
			return !$(this).closest('.list-group-item').length;
		})
		.css('visibility', 'hidden')
		.each(function(k,v)
		{
			var t = $(this);
			setTimeout(function(){
				t.css('visibility', 'visible').addClass('animated fadeInDown');
			}, 100*k);
		});

		// animate tabs
		$('.widget-tabs .tab-pane').addClass('animated fadeInUp');

		// animate page exits
		$('body')
		.on('click', 'a:not([data-toggle])', function(e)
		{
			e.preventDefault();
			var t = $(this);

			$('body').addClass('animated fadeOutLeft');
			setTimeout(function()
			{
				if (t.attr('href') == '#')
					location.reload();
				else
					location = t.attr('href');
			}, 
			1000);
		});

		// resize nicescroll areas after animations ended
		setTimeout(function(){
			$('.hasNiceScroll').getNiceScroll().show().resize();
		}, 1000);
	});

})(jQuery);