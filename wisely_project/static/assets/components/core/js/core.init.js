/* Required for iframe origin policy in our Live Preview - safe to remove in production */
if (window.location != window.parent.location) 
{
	if (document.domain == 'demo.mosaicpro.biz') {
        document.domain = "mosaicpro.biz";
    }
}

var randNum,
	equalHeight,
	genSparklines,
	beautify,
	mt_rand;

(function($, window)
{

	$.expr[':'].scrollable = function( elem ) 
    {
      var scrollable = false,
          props = [ '', '-x', '-y' ],
          re = /^(?:auto|scroll)$/i,
          elem = $(elem);
      
      $.each( props, function(i,v){
        return !( scrollable = scrollable || re.test( elem.css( 'overflow' + v ) ) );
      });
      
      return scrollable;
    };

	if (!Modernizr.touch && $('[href="#template-options"][data-auto-open]').length)
		$('#template-options').collapse('show');

	// generate a random number
	window.randNum = function()
	{
		return (Math.floor( Math.random()* (1+40-20) ) ) + 20;
	}

	window.equalHeight = function(boxes, substract)
	{
		if (typeof substract == 'undefined')
			var substract = 0;
		
		boxes.height('auto');
		if (parseInt($(window).width()) <= 400)
			return;
			
		var maxHeight = Math.max.apply( Math, boxes.map(function(){ return $(this).height() - substract; }).get());
		boxes.height(maxHeight);
	}

	function parse_url (str, component) {
		var query, key = ['source', 'scheme', 'authority', 'userInfo', 'user', 'pass', 'host', 'port',
		                  'relative', 'path', 'directory', 'file', 'query', 'fragment'],
		                  ini = (this.php_js && this.php_js.ini) || {},
		                  mode = (ini['phpjs.parse_url.mode'] &&
		                		  ini['phpjs.parse_url.mode'].local_value) || 'php',
		                		  parser = {
		                	  php: /^(?:([^:\/?#]+):)?(?:\/\/()(?:(?:()(?:([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?))?()(?:(()(?:(?:[^?#\/]*\/)*)()(?:[^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
		                	  strict: /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
		                	  loose: /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/\/?)?((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/ // Added one optional slash to post-scheme to catch file:/// (should restrict this)
		                  };

		                  var m = parser[mode].exec(str),
		                  uri = {},
		                  i = 14;
		                  while (i--) {
		                	  if (m[i]) {
		                		  uri[key[i]] = m[i];
		                	  }
		                  }

		                  if (component) {
		                	  return uri[component.replace('PHP_URL_', '').toLowerCase()];
		                  }
		                  if (mode !== 'php') {
		                	  var name = (ini['phpjs.parse_url.queryKey'] &&
		                			  ini['phpjs.parse_url.queryKey'].local_value) || 'queryKey';
		                	  parser = /(?:^|&)([^&=]*)=?([^&]*)/g;
		                	  uri[name] = {};
		                	  query = uri[key[12]] || '';
		                	  query.replace(parser, function ($0, $1, $2) {
		                		  if ($1) {uri[name][$1] = $2;}
		                	  });
		                  }
		                  delete uri.source;
		                  return uri;
	}

	function PDFTarget(target)
	{
		var doc = $('html').clone();
		var target = $(target).clone();
		var form = $('#PDFTargetForm');
		if (!form.length) {
			$('<form id="PDFTargetForm"></form>').appendTo('body');
			form = $('#PDFTargetForm');
		}
		
		form.attr('action', rootPath + 'admin/php/pdf.php');
		form.attr('method', 'POST');
		$('<input type="hidden" name="target" value="" />').appendTo(form);
		
		target.find('.hidden-print').remove();
		doc.find('body').html(target);
		var html = doc.html();
		
		form.find('input').val(html);
		form.submit();
	}

	// save to PDF
	$('[data-toggle*="pdf"]').on('click', function(e){
		e.preventDefault();
		PDFTarget($(this).attr('data-target'));
	});

	window.beautify = function (source)
	{
		var output,
			opts = {};

	 	opts.preserve_newlines = false;
		output = html_beautify(source, opts);
	    return output;
	}

	// generate a random number within a range (PHP's mt_rand JavaScript implementation)
	window.mt_rand = function (min, max) 
	{
		var argc = arguments.length;
		if (argc === 0) {
			min = 0;
			max = 2147483647;
		}
		else if (argc === 1) {
			throw new Error('Warning: mt_rand() expects exactly 2 parameters, 1 given');
		}
		else {
			min = parseInt(min, 10);
			max = parseInt(max, 10);
		}
		return Math.floor(Math.random() * (max - min + 1)) + min;
	}

	// scroll to element animation
	function scrollTo(id)
	{
		if ($(id).length)
			$('html,body').animate({scrollTop: $(id).offset().top},'slow');
	}

	var hideDropdownTimeout = null;

	$('#menu .dropdown')
	.on('mousemove', function(e)
	{
		e.stopPropagation();
		clearTimeout(hideDropdownTimeout);

		var t = $(this),
			m = t.find('> .dropdown-menu').clone();

		$('body')
		.find('> .dropdown-menu')
		.remove()
		.end()
		.append(m);

		m.show().css({
			left: 100,
			top: t.offset().top,
			width: 160
		});

	})
	.on('mouseleave', function()
	{
		hideDropdownTimeout = setTimeout(function(){
			$('body > .dropdown-menu').remove();
		}, 100);
	});

	$('body')
	.on('mouseenter', ' > .dropdown-menu', function()
	{
		clearTimeout(hideDropdownTimeout);
	})
	.on('mouseleave', ' > .dropdown-menu', function()
	{
		$(this).remove();
	});

	$('.navbar.main [data-toggle="dropdown"]')
	.hover(function()
	{ 
		if (!$(this).parent('.dropdown').is('.open'))
			$(this).click();

	}, 
	function(){ })
	.parent()
	.find('> .dropdown-menu')
	.on('mouseleave', function(){
		$(this).click();
	});

	$('.navbar.main').on('mouseleave', function(){
		$(this).find('.dropdown.open').find('> [data-toggle="dropdown"]').click();
	});

	if (Modernizr.touch)
		$('#menu').addClass('hidden-xs');

	// handle menu toggle button action
	function toggleMenuHidden(onload)
	{
		$('.container-fluid:first').toggleClass('menu-hidden');
		$('#menu').removeClass('hidden-xs');
		
		if (typeof $.cookie != 'undefined')
			$.cookie('menuHidden', $('.container-fluid').is('.menu-hidden'));
	}

	// handle generate sparkline charts
	function genSparklines()
	{
		if (typeof $.fn.sparkline == 'undefined') 
			return;

		if ($('.sparkline').length)
		{
			$.each($('#content .sparkline'), function(k,v)
			{
				var size = { w: 150, h: 28 };
				if ($(this).parent().is('.widget-stats'))
					size = { w: 150, h: 35 }
				
				var color = primaryColor;
				if ($(this).is('.danger')) color = dangerColor;
				if ($(this).is('.success')) color = successColor;
				if ($(this).is('.warning')) color = warningColor;
				if ($(this).is('.inverse')) color = inverseColor;
				
				var data = [[1, 3+randNum()], [2, 5+randNum()], [3, 8+randNum()], [4, 11+randNum()],[5, 14+randNum()],[6, 17+randNum()],[7, 20+randNum()], [8, 15+randNum()], [9, 18+randNum()], [10, 22+randNum()]];
			 	$(v).sparkline(data, 
				{ 
					type: 'bar',
					width: size.w,
					height: size.h,
					stackedBarColor: ["#444", color],
					lineWidth: 2
				});
			});
			$.each($('#menu .sparkline'), function(k,v)
			{
				var size = { w: 150, h: 20 };
				if ($(this).parent().is('.widget-stats-3'))
					size = { w: 150, h: 35 }
				
				var color = primaryColor;
				if ($(this).is('.danger')) color = dangerColor;
				if ($(this).is('.success')) color = successColor;
				if ($(this).is('.warning')) color = warningColor;
				if ($(this).is('.inverse')) color = inverseColor;
				
				var data = [[1, 3+randNum()], [2, 5+randNum()], [3, 8+randNum()], [4, 11+randNum()],[5, 14+randNum()],[6, 17+randNum()],[7, 20+randNum()], [8, 15+randNum()], [9, 18+randNum()], [10, 22+randNum()]];
			 	$(v).sparkline(data, 
				{ 
					type: 'bar',
					width: size.w,
					height: size.h,
					stackedBarColor: ["#dadada", color],
					lineWidth: 2
				});
			});
		}
	}

	if (!Modernizr.touch)
	{
		// dropdown menus
		$('html.sidebar.sidebar-dropdown').find('.slim-scroll > ul, > ul').on('mouseenter', '> li.dropdown:not(.open)', function(){
			$(this).find('> [data-toggle="dropdown"]').click();
		});
		
		// Dropdowns
		$('.navbar.main ul.topnav').on('mouseenter', '> li.dropdown:not(.open)', function(){
			$(this).find('> [data-toggle="dropdown"]').click();
		});
		$('.navbar.main').on('mouseleave', 'li.dropdown.open', function(){
			$(this).find('> [data-toggle="dropdown"]').click();
		});
	}
	
	// main menu visibility toggle
	$('.navbar.main .btn-navbar, #menu .btn-navbar').click(function()
	{
		var disabled = typeof toggleMenuButtonWhileTourOpen != 'undefined' ? toggleMenuButtonWhileTourOpen(true) : false;
		if (!disabled)
			toggleMenuHidden();
	});

	// multi-level top menu
	$('.submenu').hover(function()
	{
        $(this).children('ul').removeClass('submenu-hide').addClass('submenu-show');
    }, function()
    {
    	$(this).children('ul').removeClass('submenu-show').addClass('submenu-hide');
    });
	
	// tooltips
	$('body').tooltip({ selector: '[data-toggle="tooltip"]' });
	
	// popovers
	$('[data-toggle="popover"]').popover();
	
	// print
	$('[data-toggle="print"]').click(function(e)
	{
		e.preventDefault();
		window.print();
	});
	
	// carousels
	$('.carousel').carousel();
	
	// generate sparkline charts
	genSparklines();
	
	// Google Code Prettify
	if ($('.prettyprint').length && typeof prettyPrint != 'undefined')
		prettyPrint();
	
	// show/hide toggle buttons
	$('[data-toggle="hide"]').click(function()
	{
		if ($(this).is('.bootboxTarget'))
			bootbox.alert($($(this).attr('data-target')).html());
		else {
			$($(this).attr('data-target')).toggleClass('hide');
			if ($(this).is('.scrollTarget') && !$($(this).attr('data-target')).is('.hide'))
				scrollTo($(this).attr('data-target'));
		}
	});

	$('ul.collapse')
	.on('show.bs.collapse', function(e)
	{
		e.stopPropagation();
		$(this).parents('li:first').addClass('active');
	})
	.on('hidden.bs.collapse', function(e)
	{
		e.stopPropagation();
		$(this).parents('li:first').removeClass('active');
	});

	$('#content .col-app, .col-separator')
	.filter(':scrollable')
	.not('.col-unscrollable')
	.addClass('hasNiceScroll')
	.each(function()
	{
		$(this).niceScroll({
			horizrailenabled: false,
			zindex: 2,
			cursorborder: "none",
			cursorborderradius: "0",
			cursorcolor: primaryColor
		}).hide();
	});
	$('#menu > div')
	.addClass('hasNiceScroll')
	.niceScroll({ 
		horizrailenabled: false, 
		zindex: 2,
		cursorborder: "none",
		cursorborderradius: "0",
		cursorcolor: primaryColor
	}).hide();

	$('#sidebar-discover-wrapper > ul > li > a').on('mouseenter', function(){
		if ($(this).is('[data-toggle="sidebar-discover"]')) return;
		$('#sidebar-discover-wrapper, [data-toggle="sidebar-discover"]').removeClass('open');
	});

	var sdw_leave = null,
		sdw_hinge = null;

	$('body')
	.on('mousemove', '#sidebar-discover-wrapper.open', function()
	{
		clearTimeout(sdw_hinge);
		clearTimeout(sdw_leave);
	})
	.on('mouseleave', '#sidebar-discover-wrapper.open', function()
	{
		var that = $(this);
		sdw_hinge = setTimeout(function()
		{
			that.find('#discover > div').addClass('animated fadeOutRight');
			sdw_leave = setTimeout(function()
			{
				$('#sidebar-discover-wrapper, [data-toggle="sidebar-discover"]').removeClass('open');
			}, 
			200);
		},
		200);
	});

	$('[data-toggle="sidebar-discover"]')
	.on('click', function(e){
		e.preventDefault();
	})
	.on('mouseenter', function()
	{
		clearTimeout(sdw_hinge);
		clearTimeout(sdw_leave);

		var that = $(this);

		$('[data-toggle="sidebar-discover"]').removeClass('open');
		that.addClass('open');

		var wrapper = $('#sidebar-discover-wrapper'),
			main = wrapper.find('> ul'),
			discover = wrapper.find('> #discover'),
			target = $(that.attr('href')).clone().removeAttr('class id');

		if (!discover.length)
		{
			discover = $('<div/>').attr('id', 'discover');
			wrapper.append(discover);
		}

		discover.html(target)
		wrapper.addClass('open');
	});
	
	$(window).on('load', function()
	{
		// handle persistent menu visibility on page load
		if (typeof $.cookie != 'undefined' && $.cookie('menuHidden') && $.cookie('menuHidden') == 'true' || (!$('.container-fluid').is('.menu-hidden') && !$('#menu').is(':visible')))
			toggleMenuHidden(true);
	});

})(jQuery, window);