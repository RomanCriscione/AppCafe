// JS global
document.addEventListener('DOMContentLoaded', () => {
  // Delegación: AJAX para forms con clase .js-ajax-post
  document.body.addEventListener('submit', async (ev) => {
    const form = ev.target.closest('form.js-ajax-post');
    if (!form) return;

    // Si el navegador no soporta fetch, dejamos que haga submit normal
    if (!window.fetch) return;

    ev.preventDefault();

    const btn = form.querySelector('.js-fav-btn');
    const icon = form.querySelector('.js-fav-icon');
    const csrf = form.querySelector('input[name="csrfmiddlewaretoken"]')?.value || '';
    const fd = new FormData(form);

    try {
      const resp = await fetch(form.action, {
        method: 'POST',
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrf
        },
        body: fd,
        credentials: 'same-origin'
      });

      // Si el view devuelve JSON (como lo actualizamos), actualizamos UI sin recargar.
      if (resp.headers.get('content-type')?.includes('application/json')) {
        const data = await resp.json();

        // Toggle clases/estado
        if (btn) {
          const liked = !!data.liked;
          btn.classList.toggle('btn-success', liked);
          btn.classList.toggle('btn-outline', !liked);
          btn.classList.toggle('btn-danger', liked); // en detalle puede ser rojo
          btn.setAttribute('aria-pressed', liked ? 'true' : 'false');

          // Icono y label
          if (icon) icon.textContent = liked ? (btn.dataset.icon || '❤️') : (btn.dataset.iconOff || '🤍');

          // En el detalle, actualizamos el texto visible
          const hasTextNode = btn.childNodes.length > 1;
          if (hasTextNode) {
            // Deja el icono (primer span) y cambia el texto plano siguiente
            const labelOn  = btn.dataset.labelOn  || 'Quitar de favoritos';
            const labelOff = btn.dataset.labelOff || 'Agregar a favoritos';
            // Busca el nodo de texto después del icono
            for (let i = 0; i < btn.childNodes.length; i++) {
              const n = btn.childNodes[i];
              if (n.nodeType === Node.TEXT_NODE) {
                n.textContent = ' ' + (liked ? labelOn : labelOff);
                break;
              }
            }
          }
        }
        // animación suave opcional
        if (window.bounceLike) window.bounceLike(btn);
        return;
      }

      // Si no es JSON (por ejemplo redirección normal), hacemos fallback
      window.location.reload();
    } catch (err) {
      console.error(err);
      // Fallback final si algo explota
      window.location.reload();
    }
  });
});
