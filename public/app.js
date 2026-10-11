// Demo y búsqueda por código postal de la página de documentación.
// Los textos cambian según el atributo lang del <html> (es o en).

const TEXTOS = {
  es: {
    elegirProvincia: 'Elegí una provincia',
    elegirCanton: 'Elegí un cantón',
    elegirDistrito: 'Elegí un distrito',
    formatoCP: 'Son 5 dígitos y el primero va de 1 a 7.',
    cpNoExiste: 'Ese código postal no existe.',
    enGam: 'GAM',
    fueraGam: 'Fuera de la GAM',
    total: (n) => `${n} ${n === 1 ? 'distrito' : 'distritos'}`,
    copiar: 'Copiar',
    copiado: 'Copiado',
  },
  en: {
    elegirProvincia: 'Choose a province',
    elegirCanton: 'Choose a canton',
    elegirDistrito: 'Choose a district',
    formatoCP: 'Postal codes have 5 digits and start with 1 to 7.',
    cpNoExiste: 'That postal code does not exist.',
    enGam: 'GAM',
    fueraGam: 'Outside the GAM',
    total: (n) => `${n} ${n === 1 ? 'district' : 'districts'}`,
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
// Todos los distritos con su código postal y el campo gam; lo usan las etiquetas y la lista por zona
const distritos = getJSON('/distritos.json');
const enGam = distritos.then((ds) => new Set(ds.filter((d) => d.gam).map((d) => d.codigo_postal)));
const sinTildes = (s) => s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

function etiquetaGam(nodo, esGam) {
  nodo.textContent = esGam ? T.enGam : T.fueraGam;
  nodo.classList.toggle('si', esGam);
  nodo.hidden = false;
}

function fill(select, data, placeholder) {
  select.replaceChildren(crear('option', { value: '' }, placeholder),
    ...Object.entries(data).map(([k, v]) => crear('option', { value: k }, v)));
  select.disabled = false;
}
function reset(select) { select.replaceChildren(crear('option', { value: '' }, '—')); select.disabled = true; }
async function showCP(text = '', route = '') {
  $('cp').textContent = text;
  $('cp-ruta').textContent = route;
  if (text) etiquetaGam($('cp-gam'), (await enGam).has(text));
  else $('cp-gam').hidden = true;
  const boton = $('copiar-cp');
  boton.hidden = !text;
  boton.textContent = T.copiar;
  boton.classList.remove('listo');
}

// Copia el texto y marca el botón; si no hay acceso al portapapeles, selecciona el texto para copiarlo a mano
async function copiar(boton, texto, nodo) {
  try {
    await navigator.clipboard.writeText(texto);
    boton.textContent = T.copiado;
    boton.classList.add('listo');
    clearTimeout(boton.reinicio);
    boton.reinicio = setTimeout(() => {
      boton.textContent = T.copiar;
      boton.classList.remove('listo');
    }, 2000);
  } catch {
    getSelection().selectAllChildren(nodo);
  }
}

$('copiar-cp').addEventListener('click', (e) => copiar(e.currentTarget, $('cp').textContent, $('cp')));

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
    const lugar = crear('span', { class: 'lugar' }, d.distrito);
    const boton = crear('button', { type: 'button', class: 'copiar' }, T.copiar);
    boton.addEventListener('click', () => copiar(boton, `${d.distrito}, ${d.canton}, ${d.provincia}`, out));
    const etiqueta = crear('span', { class: 'etiqueta-gam' });
    etiquetaGam(etiqueta, d.gam);
    out.replaceChildren(crear('span', { class: 'lugar-fila' }, lugar, etiqueta, boton),
      crear('span', { class: 'lugar-ruta' }, `${d.canton} · ${d.provincia}`));
  } catch { out.textContent = T.cpNoExiste; }
});
$('form-cp').addEventListener('submit', (e) => e.preventDefault());

// Lista de distritos dentro y fuera de la GAM
async function renderLista() {
  const zona = document.querySelector('input[name="zona"]:checked').value;
  const filtro = sinTildes($('filtro-lista').value.trim());
  const filas = (await distritos).filter((d) => (zona === 'todas' || d.gam === (zona === 'gam')) &&
    (!filtro || d.codigo_postal.startsWith(filtro) || sinTildes(`${d.distrito} ${d.canton} ${d.provincia}`).includes(filtro)));
  $('lista-gam').replaceChildren(...filas.map((d) => {
    const etiqueta = crear('span', { class: 'etiqueta-gam' });
    etiquetaGam(etiqueta, d.gam);
    return crear('tr', {}, crear('td', {}, crear('code', {}, d.codigo_postal)),
      crear('td', {}, d.distrito, crear('span', { class: 'sub' }, `${d.canton} · ${d.provincia}`)),
      crear('td', {}, d.canton), crear('td', {}, d.provincia), crear('td', {}, etiqueta));
  }));
  $('lista-total').textContent = T.total(filas.length);
}
document.querySelectorAll('input[name="zona"]').forEach((r) => r.addEventListener('change', renderLista));
$('filtro-lista').addEventListener('input', renderLista);
renderLista();

