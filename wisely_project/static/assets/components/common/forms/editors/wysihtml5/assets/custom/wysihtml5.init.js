(function($){
	
	$(window).on('load', function(){
		setTimeout(function(){
			/* wysihtml5 */
			if ($('textarea.wysihtml5').size() > 0)
				$('textarea.wysihtml5').wysihtml5();
		}, 200);
	});

})(jQuery);