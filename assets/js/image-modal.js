// Image modal: opens .image-link images (rendered by partials/plugin/image.html)
// in a centered <dialog> instead of navigating to the file. Without JavaScript,
// or with a modifier key held, the link keeps opening the image itself.
(function () {
  // Posts and the home page summaries both render linked images.
  if (!document.querySelector('.image-link')) return;

  const closeLabel = document.currentScript.dataset.closeLabel;

  const dialog = document.createElement('dialog');
  dialog.className = 'image-modal';
  dialog.innerHTML =
    '<button type="button" class="image-modal-close"><span aria-hidden="true">&times;</span></button>' +
    '<figure class="image-modal-figure"><img class="image-modal-image" alt=""><figcaption class="image-modal-caption"></figcaption></figure>';
  const close = dialog.querySelector('.image-modal-close');
  const image = dialog.querySelector('.image-modal-image');
  const caption = dialog.querySelector('.image-modal-caption');
  close.setAttribute('aria-label', closeLabel);
  close.title = closeLabel;
  document.body.appendChild(dialog);

  function captionFor(link) {
    if (link.dataset.caption) return link.dataset.caption;
    const figure = link.closest('figure');
    const figcaption = figure && figure.querySelector('.image-caption');
    return figcaption ? figcaption.textContent.trim() : '';
  }

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a.image-link');
    if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();

    const thumb = link.querySelector('img');
    image.src = link.href;
    image.alt = thumb ? thumb.alt : '';
    caption.textContent = captionFor(link);
    caption.hidden = !caption.textContent;
    dialog.setAttribute('aria-label', image.alt || caption.textContent);
    document.documentElement.classList.add('image-modal-open');
    dialog.showModal();
  });

  close.addEventListener('click', () => dialog.close());
  // A click on the dialog itself (not its contents) is a click on the backdrop.
  dialog.addEventListener('click', (event) => {
    if (event.target === dialog) dialog.close();
  });
  dialog.addEventListener('close', () => {
    document.documentElement.classList.remove('image-modal-open');
    image.removeAttribute('src');
  });
})();
