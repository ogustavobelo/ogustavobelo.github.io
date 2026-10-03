// Shelf filters (/estante/): toggles works by kind and status and keeps the
// selection in the query string (?kind=book&status=concluded) so it can be shared.
(function () {
  const filters = document.querySelector('.shelf-filters');
  if (!filters) return;

  const items = document.querySelectorAll('.shelf-item');
  const shelfGroups = document.querySelectorAll('.shelf-group');
  const empty = document.querySelector('.shelf-empty');
  const groups = filters.querySelectorAll('.shelf-filter');
  const params = new URLSearchParams(window.location.search);
  const state = {};

  groups.forEach((group) => {
    const name = group.dataset.filter;
    const wanted = params.get(name) || '';
    const known = group.querySelector(`.shelf-chip[data-value="${CSS.escape(wanted)}"]`);
    state[name] = known ? wanted : '';
  });

  function render() {
    groups.forEach((group) => {
      group.querySelectorAll('.shelf-chip').forEach((chip) => {
        chip.setAttribute('aria-pressed', String(chip.dataset.value === state[group.dataset.filter]));
      });
    });

    let visible = 0;
    items.forEach((item) => {
      const show = Object.keys(state).every((name) => !state[name] || item.dataset[name] === state[name]);
      item.hidden = !show;
      if (show) visible++;
    });
    shelfGroups.forEach((group) => {
      group.hidden = !group.querySelector('.shelf-item:not([hidden])');
    });
    if (empty) empty.hidden = visible > 0;

    const url = new URL(window.location.href);
    Object.keys(state).forEach((name) => {
      if (state[name]) url.searchParams.set(name, state[name]);
      else url.searchParams.delete(name);
    });
    window.history.replaceState(null, '', url);
  }

  filters.addEventListener('click', (event) => {
    const chip = event.target.closest('.shelf-chip');
    if (!chip) return;
    state[chip.closest('.shelf-filter').dataset.filter] = chip.dataset.value;
    render();
  });

  filters.hidden = false;
  render();
})();
