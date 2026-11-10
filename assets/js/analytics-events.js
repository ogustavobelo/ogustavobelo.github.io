// Analytics events: forwards the clicks already tracked by GoatCounter
// (data-goatcounter-click) to Firebase Analytics as GA4 recommended events, so
// the markup carries one set of attributes. Only known event names are sent,
// and parameters never include query strings, e-mails or typed text.
(function () {
  if (typeof window.gtag !== 'function') return;

  // GA4 truncates parameter values at 100 characters.
  const clip = (value) => String(value || '').slice(0, 100);

  // Maps a data-goatcounter-click name to a GA4 event; unknown names are dropped.
  const toEvent = (name, el) => {
    const path = el.dataset.goatcounterReferrer || location.pathname;
    let match;
    if ((match = /^share-([a-z]+)$/.exec(name))) {
      return ['share', { method: match[1], content_type: 'post', item_id: path }];
    }
    if ((match = /^image-(\/[^?#]*)$/.exec(name))) {
      return ['select_content', { content_type: 'image', item_id: match[1] }];
    }
    if ((match = /^shelf-no-post-([a-z0-9-]+)$/.exec(name))) {
      return ['select_content', { content_type: 'shelf_card', item_id: match[1] }];
    }
    if (name === 'contato-email') {
      return ['contact_click', { method: 'email', item_id: path }];
    }
    return null;
  };

  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-goatcounter-click]');
    if (!el) return;
    const event = toEvent(el.dataset.goatcounterClick, el);
    if (!event) return;
    const params = { transport_type: 'beacon' };
    for (const key in event[1]) params[key] = clip(event[1][key]);
    window.gtag('event', event[0], params);
  }, true);

  // 404 page (layouts/404.html): the requested path, without the query string.
  if (document.getElementById('content-404')) {
    window.gtag('event', 'page_not_found', { page_path: clip(location.pathname) });
  }
})();
