(function () {
	'use strict';

	function initBuilder(root) {
		if (!root || root.dataset.baklyReady === '1') {
			return;
		}
		root.dataset.baklyReady = '1';
		var currency = root.dataset.currencySymbol || '';
		var inputs = Array.prototype.slice.call(root.querySelectorAll('.bakly-builder-opt-input'));
		var totalEl = root.querySelector('[data-bakly-total]');
		var totalMobileEl = root.querySelector('[data-bakly-total-mobile]');
		var errorEl = root.querySelector('[data-bakly-error]');
		var stickybar = root.querySelector('[data-bakly-stickybar]');
		var form = root.closest('.bakly-single-layout') ? root.closest('.bakly-single-layout').querySelector('form.variations_form, form.cart') : null;

		function selected() {
			return inputs.filter(function (input) { return input.checked; });
		}
		function updateCaps() {
			root.querySelectorAll('.bakly-builder-step').forEach(function (step) {
				if ('checkbox' !== step.dataset.baklyType) { return; }
				var max = parseInt(step.dataset.baklyMax || '0', 10);
				var choices = Array.prototype.slice.call(step.querySelectorAll('.bakly-builder-opt-input'));
				var count = choices.filter(function (input) { return input.checked; }).length;
				choices.forEach(function (input) { input.disabled = !input.checked && max > 0 && count >= max; });
				step.classList.toggle('is-capped', max > 0 && count >= max);
			});
		}
		function validate(showError) {
			var valid = true;
			root.querySelectorAll('.bakly-builder-step').forEach(function (step) {
				if ('1' === step.dataset.baklyRequired && !step.querySelector('.bakly-builder-opt-input:checked')) { valid = false; }
			});
			if (errorEl) { errorEl.hidden = valid || !showError; errorEl.textContent = valid ? '' : 'Please complete the required selections.'; }
			root.classList.toggle('is-invalid', !valid);
			return valid;
		}
		function update() {
			var total = selected().reduce(function (sum, input) { return sum + (parseFloat(input.dataset.price) || 0); }, 0);
			var display = currency + total.toFixed(2);
			if (totalEl) { totalEl.textContent = display; }
			if (totalMobileEl) { totalMobileEl.textContent = display; }
			updateCaps();
		}
		inputs.forEach(function (input) { input.addEventListener('change', function () { update(); validate(false); }); });
		if (form) {
			form.addEventListener('submit', function (event) { if (!validate(true)) { event.preventDefault(); root.scrollIntoView({ behavior: 'smooth', block: 'start' }); } });
			if (stickybar) { stickybar.hidden = false; }
		}
		update();
	}

	document.querySelectorAll('.bakly-product-builder').forEach(initBuilder);
})();