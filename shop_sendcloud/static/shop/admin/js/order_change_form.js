django.jQuery(function($) {
	'use strict';

	$('iframe.shop-pdf-panel').on('load', function(event) {
		var pdfFrame = window.frames[event.target.name];
		pdfFrame.focus();
		pdfFrame.print();
	});
});
