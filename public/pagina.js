// Botones de copiar de las páginas de provincia, cantón y distrito.
const copiado = document.documentElement.lang === 'en' ? 'Copied' : 'Copiado';

document.querySelectorAll('[data-copiar]').forEach((boton) => {
  const texto = boton.textContent;
  boton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(boton.dataset.copiar);
      boton.textContent = copiado;
      boton.classList.add('listo');
      clearTimeout(boton.reinicio);
      boton.reinicio = setTimeout(() => {
        boton.textContent = texto;
        boton.classList.remove('listo');
      }, 2000);
    } catch {
      getSelection().selectAllChildren(boton.previousElementSibling || boton);
    }
  });
});
