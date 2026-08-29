( function () {
	'use strict';
	function init( el ) {
		if ( ! window.Swiper || el.dataset.baklySocialInit ) { return; }
		el.dataset.baklySocialInit = '1';
		new window.Swiper( el, {
			slidesPerView: 2,
			spaceBetween: 16,
			loop: true,
			speed: 600,
			grabCursor: true,
			autoplay: {
				delay: 5000,
				disableOnInteraction: false,
				pauseOnMouseEnter: true
			},
			breakpoints: {
				782:  { slidesPerView: 3, spaceBetween: 16 },
				1200: { slidesPerView: 6, spaceBetween: 16 }
			},
			a11y: { slideLabelMessage: '{{index}} / {{slidesLength}}' }
		} );
	}
	document.querySelectorAll( '.bakly-social-grid.swiper' ).forEach( init );
} )();
