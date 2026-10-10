// Demo y búsqueda por código postal de la página de documentación.
// Los textos cambian según el atributo lang del <html> (es o en).

const TEXTOS = {
  es: {
    elegirProvincia: 'Elegí una provincia',
    elegirCanton: 'Elegí un cantón',
    elegirDistrito: 'Elegí un distrito',
    formatoCP: 'Son 5 dígitos y el primero va de 1 a 7.',
    cpNoExiste: 'Ese código postal no existe.',
    copiar: 'Copiar',
    copiado: 'Copiado',
  },
  en: {
    elegirProvincia: 'Choose a province',
    elegirCanton: 'Choose a canton',
    elegirDistrito: 'Choose a district',
    formatoCP: 'Postal codes have 5 digits and start with 1 to 7.',
    cpNoExiste: 'That postal code does not exist.',
    copiar: 'Copy',
    copiado: 'Copied',
  },
};
const T = TEXTOS[document.documentElement.lang] || TEXTOS.es;

const $ = (id) => document.getElementById(id);
const getJSON = (url) => fetch(url).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
const pad = (n) => String(n).padStart(2, '0');

function crear(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) k.startsWith('on') ? e.addEventListener(k.slice(2), v) : e.setAttribute(k, v);
  e.append(...hijos);
  return e;
}

// Totales en vivo desde /meta.json
getJSON('/meta.json').then((m) => {
  for (const k of ['provincias', 'cantones', 'distritos']) $('n-' + k).textContent = m.totales[k];
  $('fuente').href = m.fuente.url;
}).catch(() => {});

// Demo: selectores en cascada
function fill(select, data, placeholder) {
  select.replaceChildren(crear('option', { value: '' }, placeholder),
    ...Object.entries(data).map(([k, v]) => crear('option', { value: k }, v)));
  select.disabled = false;
}
function reset(select) { select.replaceChildren(crear('option', { value: '' }, '—')); select.disabled = true; }
function showCP(text = '', route = '') {
  $('cp').textContent = text;
  $('cp-ruta').textContent = route;
  const boton = $('copiar-cp');
  boton.hidden = !text;
  boton.textContent = T.copiar;
  boton.classList.remove('listo');
}

$('copiar-cp').addEventListener('click', async () => {
  const boton = $('copiar-cp');
  try {
    await navigator.clipboard.writeText($('cp').textContent);
    boton.textContent = T.copiado;
    boton.classList.add('listo');
  } catch {
    // Sin acceso al portapapeles: seleccionar el código para copiarlo a mano
    getSelection().selectAllChildren($('cp'));
  }
});

getJSON('/provincias.json').then((d) => fill($('sel-provincia'), d, T.elegirProvincia));

$('sel-provincia').addEventListener('change', async (e) => {
  reset($('sel-canton')); reset($('sel-distrito')); showCP();
  if (e.target.value) fill($('sel-canton'), await getJSON(`/provincia/${e.target.value}/cantones.json`), T.elegirCanton);
});
$('sel-canton').addEventListener('change', async (e) => {
  reset($('sel-distrito')); showCP();
  const p = $('sel-provincia').value;
  if (e.target.value) fill($('sel-distrito'), await getJSON(`/provincia/${p}/canton/${e.target.value}/distritos.json`), T.elegirDistrito);
});
$('sel-distrito').addEventListener('change', (e) => {
  const p = $('sel-provincia').value, c = $('sel-canton').value, d = e.target.value;
  if (!d) return showCP();
  showCP(`${p}${pad(c)}${pad(d)}`, `/codigo-postal/${p}${pad(c)}${pad(d)}.json`);
});

// Búsqueda por código postal
$('in-cp').addEventListener('input', async (e) => {
  const v = e.target.value.trim(), out = $('out-cp');
  if (!/^[1-7]\d{4}$/.test(v)) { out.textContent = v ? T.formatoCP : ''; return; }
  try {
    const d = await getJSON(`/codigo-postal/${v}.json`);
    out.textContent = `${d.distrito}, ${d.canton}, ${d.provincia}`;
  } catch { out.textContent = T.cpNoExiste; }
});
$('form-cp').addEventListener('submit', (e) => e.preventDefault());

