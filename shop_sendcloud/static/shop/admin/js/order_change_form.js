django.jQuery(function($) {
	'use strict';

	$('iframe.shop-parcel-label').on('load', function(event) {
		var pdfFrame = window.frames[event.target.name];
		pdfFrame.focus();
		pdfFrame.print();
	});
});
