// Shelf (/estante/): shows one year at a time, newest first, with links to the
// neighbouring years at the end, and filters works by kind. The selection is
// kept in the query string (?year=2025&kind=book) so it can be shared.
(function () {
  const filters = document.querySelector('.shelf-filters');
  if (!filters) return;

  const shelf = document.querySelector('.shelf');
  const items = document.querySelectorAll('.shelf-item');
  const shelfGroups = document.querySelectorAll('.shelf-group');
  const empty = document.querySelector('.shelf-empty');
  const groups = filters.querySelectorAll('.shelf-filter');
  const yearNav = document.querySelector('.shelf-years');
  const yearLinks = yearNav ? Array.from(yearNav.querySelectorAll('.shelf-year')) : [];
  // Newest first, as rendered by the template.
  const years = [];
  shelfGroups.forEach((group) => {
    if (!years.includes(group.dataset.year)) years.push(group.dataset.year);
  });
  const state = {};

  function readUrl() {
    const params = new URLSearchParams(window.location.search);
    groups.forEach((group) => {
      const name = group.dataset.filter;
      const wanted = params.get(name) || '';
      const known = group.querySelector(`.shelf-chip[data-value="${CSS.escape(wanted)}"]`);
      state[name] = known ? wanted : '';
    });
    const year = params.get('year');
    state.year = years.includes(year) ? year : years[0];
  }

  function writeUrl(push) {
    const url = new URL(window.location.href);
    Object.keys(state).forEach((name) => {
      // The newest year is the default page, so it needs no parameter.
      const value = name === 'year' && state.year === years[0] ? '' : state[name];
      if (value) url.searchParams.set(name, value);
      else url.searchParams.delete(name);
    });
    window.history[push ? 'pushState' : 'replaceState'](null, '', url);
  }

  function render() {
    groups.forEach((group) => {
      group.querySelectorAll('.shelf-chip').forEach((chip) => {
        chip.setAttribute('aria-pressed', String(chip.dataset.value === state[group.dataset.filter]));
      });
    });

    let visible = 0;
    shelfGroups.forEach((group) => {
      const inYear = group.dataset.year === state.year;
      group.querySelectorAll('.shelf-item').forEach((item) => {
        const show = inYear && Object.keys(state).every(
          (name) => name === 'year' || !state[name] || item.dataset[name] === state[name]
        );
        item.hidden = !show;
        if (show) visible++;
      });
      group.hidden = !group.querySelector('.shelf-item:not([hidden])');
    });
    if (empty) empty.hidden = visible > 0;

    const index = years.indexOf(state.year);
    yearLinks.forEach((link) => {
      const position = years.indexOf(link.dataset.year);
      link.hidden = Math.abs(position - index) !== 1;
      link.classList.toggle('shelf-year-older', position > index);
    });
  }

  filters.addEventListener('click', (event) => {
    const chip = event.target.closest('.shelf-chip');
    if (!chip) return;
    state[chip.closest('.shelf-filter').dataset.filter] = chip.dataset.value;
    render();
    writeUrl(false);
  });

  if (yearNav) {
    yearNav.addEventListener('click', (event) => {
      const link = event.target.closest('.shelf-year');
      if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      state.year = link.dataset.year;
      render();
      writeUrl(true);
      shelf.scrollIntoView();
    });
    yearNav.hidden = false;
  }

  window.addEventListener('popstate', () => {
    readUrl();
    render();
  });

  filters.hidden = false;
  readUrl();
  render();
  writeUrl(false);
})();
