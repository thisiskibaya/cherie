( function () {
	'use strict';

	var reduce = window.matchMedia( '(prefers-reduced-motion: reduce)' );

	function init( root ) {
		var sections = root.querySelectorAll( '[data-menu-section]' );
		var links = root.querySelectorAll( '[data-menu-link]' );
		if ( ! sections.length || ! links.length ) { return; }
		if ( ! window.gsap || ! window.ScrollTrigger ) { return; }

		var gsap = window.gsap;
		var ScrollTrigger = window.ScrollTrigger;
		var lenis = null;

		if ( window.Lenis && ! reduce.matches ) {
			lenis = new window.Lenis( { respectReducedMotion: true } );
			lenis.on( 'scroll', ScrollTrigger.update );
			gsap.ticker.add( function ( time ) {
				lenis.raf( time * 1000 );
			} );
			gsap.ticker.lagSmoothing( 0 );
		}

		var ctx = gsap.context( function () {
			root.querySelectorAll( '[data-marquee]' ).forEach( function ( marquee ) {
				var track = marquee.querySelector( '.bakly-marquee-track' );
				if ( ! track ) { return; }
				gsap.to( track, {
					xPercent: -25,
					ease: 'none',
					scrollTrigger: {
						trigger: marquee,
						start: 'top bottom',
						end: 'bottom top',
						scrub: 1.5
					}
				} );
			} );

			root.querySelectorAll( '[data-parallax]' ).forEach( function ( layer ) {
				var speed = parseFloat( layer.getAttribute( 'data-parallax' ) ) || 0;
				if ( ! speed ) { return; }
				gsap.to( layer, {
					yPercent: speed,
					ease: 'none',
					scrollTrigger: {
						trigger: layer.parentNode,
						start: 'top bottom',
						end: 'bottom top',
						scrub: 1.2
					}
				} );
			} );

			root.querySelectorAll( '[data-reveal]' ).forEach( function ( el ) {
				gsap.fromTo( el, { autoAlpha: 0, y: 40 }, {
					autoAlpha: 1,
					y: 0,
					duration: 1,
					ease: 'power3.out',
					scrollTrigger: {
						trigger: el,
						start: 'top 85%',
						once: true
					}
				} );
			} );

			root.querySelectorAll( '[data-reveal-group]' ).forEach( function ( group ) {
				var items = group.children;
				if ( ! items.length ) { return; }
				gsap.fromTo( items, { autoAlpha: 0, y: 30 }, {
					autoAlpha: 1,
					y: 0,
					duration: 0.8,
					stagger: 0.08,
					ease: 'power3.out',
					scrollTrigger: {
						trigger: group,
						start: 'top 85%',
						once: true
					}
				} );
			} );

			links.forEach( function ( link, i ) {
				ScrollTrigger.create( {
					trigger: sections[ i ],
					start: 'top center',
					end: 'bottom center',
					onToggle: function ( self ) {
						if ( self.isActive ) {
							links.forEach( function ( l ) { l.classList.remove( 'is-active' ); } );
							link.classList.add( 'is-active' );
						}
					}
				} );
			} );
		}, root );

		function go( e ) {
			var target = document.getElementById( ( e.currentTarget.getAttribute( 'href' ) || '' ).slice( 1 ) );
			if ( ! target ) { return; }
			e.preventDefault();
			if ( lenis ) {
				lenis.scrollTo( target, { offset: 0, duration: 1.4 } );
			} else {
				target.scrollIntoView( { behavior: reduce.matches ? 'auto' : 'smooth', block: 'start' } );
			}
		}
		links.forEach( function ( link ) {
			link.addEventListener( 'click', go );
		} );

		root.setAttribute( 'data-enhanced', 'true' );
	}

	document.querySelectorAll( '[data-menu-page]' ).forEach( init );
} )();