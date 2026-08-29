(function () {
	'use strict';

	var MAX_TOPPINGS = 4;

	function initBuilder(root) {
		if (!root || root.dataset.baklyReady === '1') {
			return;
		}
		root.dataset.baklyReady = '1';

		var CURRENCY = root.dataset.currencySymbol || '$';

		var inputs = Array.prototype.slice.call(root.querySelectorAll('.bakly-builder-opt-input'));
		if (!inputs.length) {
			return;
		}

		var totalEl = root.querySelector('[data-bakly-total]');
		var totalMobileEl = root.querySelector('[data-bakly-total-mobile]');
		var errorEl = root.querySelector('[data-bakly-error]');
		var stickybar = root.querySelector('[data-bakly-stickybar]');
		var gotoCartBtn = root.querySelector('[data-bakly-goto-cart]');

		var form = document.querySelector('form.variations_form, form.cart');
		var mirror = document.getElementById('bakly-build-input');
		var variations = [];
		var variationSource = document.querySelector('[data-product_variations]');

		if (variationSource) {
			try {
				variations = JSON.parse(variationSource.getAttribute('data-product_variations')) || [];
			} catch (e) {
				variations = [];
			}
		}

		function basePrice() {
			if (!variations.length) {
				return 0;
			}
			var sizeSelect = form ? form.querySelector('select[name="attribute_pa_size"]') : null;
			if (!sizeSelect || !sizeSelect.value) {
				var min = Infinity;
				variations.forEach(function (v) {
					if (v.display_price < min) {
						min = v.display_price;
					}
				});
				return isFinite(min) ? min : 0;
			}
			for (var i = 0; i < variations.length; i++) {
				var attrs = variations[i].attributes || {};
				if (attrs.attribute_pa_size === sizeSelect.value) {
					return parseFloat(variations[i].display_price);
				}
			}
			return 0;
		}

		function money(value) {
			return CURRENCY + value.toFixed(2);
		}

		function selected() {
			return inputs.filter(function (input) {
				return input.checked;
			});
		}

		function enforceCaps() {
			inputs.forEach(function (input) {
				var fieldset = input.closest('.bakly-builder-step');
				if (!fieldset || fieldset.dataset.baklyGroup !== 'toppings') {
					return;
				}
				if (input.checked) {
					input.disabled = false;
					return;
				}
				var count = selected().filter(function (sel) {
					return sel.closest('.bakly-builder-step').dataset.baklyGroup === 'toppings';
				}).length;
				input.disabled = MAX_TOPPINGS > 0 && count >= MAX_TOPPINGS && fieldset.dataset.baklyMax !== '0';
				fieldset.classList.toggle('is-capped', count >= MAX_TOPPINGS);
			});
		}

		function validate(showError) {
			var flavour = inputs.filter(function (input) {
				return input.type === 'radio' && input.checked;
			});
			var ok = flavour.length >= 1;
			if (errorEl) {
				errorEl.hidden = ok || !showError;
				errorEl.textContent = ok ? '' : 'Please choose a flavour for your cake.';
			}
			root.classList.toggle('is-invalid', !ok);
			return ok;
		}

		function syncMirror() {
			if (!mirror) {
				return;
			}
			mirror.value = JSON.stringify(selected().map(function (input) {
				return { id: parseInt(input.value, 10), qty: 1 };
			}));
		}

		function update() {
			var extras = 0.0;
			selected().forEach(function (input) {
				extras += parseFloat(input.dataset.price) || 0;
			});
			var total = basePrice() + extras;
			if (totalEl) {
				totalEl.textContent = money(total);
			}
			if (totalMobileEl) {
				totalMobileEl.textContent = money(total);
			}
			enforceCaps();
			syncMirror();
		}

		inputs.forEach(function (input) {
			input.addEventListener('change', function () {
				update();
				validate(false);
			});
		});

		if (form) {
			form.addEventListener('submit', function (event) {
				syncMirror();
				if (!validate(true)) {
					event.preventDefault();
					root.scrollIntoView({ behavior: 'smooth', block: 'start' });
					return;
				}
				var firstInvalid = selected().length === 0;
				if (firstInvalid) {
					event.preventDefault();
					if (errorEl) {
						errorEl.hidden = false;
						errorEl.textContent = 'Please build your cake before adding to cart.';
					}
					root.classList.add('is-invalid');
				}
			});

			if (stickybar) {
				stickybar.hidden = false;
			}
		} else if (stickybar) {
			stickybar.hidden = true;
		}

		if (gotoCartBtn && form) {
			gotoCartBtn.addEventListener('click', function () {
				var button = form.querySelector('button[type="submit"], .single_add_to_cart_button');
				if (button) {
					button.scrollIntoView({ behavior: 'smooth', block: 'center' });
					button.focus({ preventScroll: true });
				}
			});
		}

		document.addEventListener('change', function (event) {
			if (form && event.target && event.target.name === 'attribute_pa_size') {
				update();
			}
		}, true);

		update();
	}

	function boot() {
		document.querySelectorAll('.bakly-cake-builder').forEach(initBuilder);
	}

	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', boot);
	} else {
		boot();
	}
})();
