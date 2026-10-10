// Demo, búsqueda por código postal y explorador de la página de documentación.
// Los textos cambian según el atributo lang del <html> (es o en).

const TEXTOS = {
  es: {
    elegirProvincia: 'Elegí una provincia',
    elegirCanton: 'Elegí un cantón',
    elegirDistrito: 'Elegí un distrito',
    formatoCP: 'Son 5 dígitos y el primero va de 1 a 7.',
    cpNoExiste: 'Ese código postal no existe.',
    copiado: (d) => `Copiado: ${d.codigo} · ${d.nombre}`,
    codigoDe: (d) => `Código postal de ${d.nombre}: ${d.codigo}`,
    copiarTitulo: 'Copiar código postal',
    cantidad: (n, enCanton) => `${n} ${enCanton ? (n === 1 ? 'distrito' : 'distritos') : (n === 1 ? 'cantón' : 'cantones')}`,
    sinResultados: 'Sin resultados',
    pasoCanton: 'elegí un cantón',
    filtrarCantones: (nombre) => `Filtrar cantones de ${nombre}…`,
    filtrarDistritos: (nombre) => `Filtrar distritos de ${nombre}…`,
    errorDatos: 'No se pudieron cargar los datos.',
  },
  en: {
    elegirProvincia: 'Choose a province',
    elegirCanton: 'Choose a canton',
    elegirDistrito: 'Choose a district',
    formatoCP: 'Postal codes have 5 digits and start with 1 to 7.',
    cpNoExiste: 'That postal code does not exist.',
    copiado: (d) => `Copied: ${d.codigo} · ${d.nombre}`,
    codigoDe: (d) => `Postal code for ${d.nombre}: ${d.codigo}`,
    copiarTitulo: 'Copy postal code',
    cantidad: (n, enCanton) => `${n} ${enCanton ? (n === 1 ? 'district' : 'districts') : (n === 1 ? 'canton' : 'cantons')}`,
    sinResultados: 'No results',
    pasoCanton: 'choose a canton',
    filtrarCantones: (nombre) => `Filter cantons in ${nombre}…`,
    filtrarDistritos: (nombre) => `Filter districts in ${nombre}…`,
    errorDatos: 'Could not load the data.',
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
function showCP(text = '', route = '') { $('cp').textContent = text; $('cp-ruta').textContent = route; }

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

// Explorador: provincia → cantón → distritos con código postal, a partir de /todo.json
const ex = { provincias: [], prov: null, canton: null };
const sinTildes = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

function elegirProvincia(p) { ex.prov = p; ex.canton = null; $('ex-filtro').value = ''; renderExplorador(); }
function elegirCanton(c) { ex.canton = c; $('ex-filtro').value = ''; renderExplorador(); $('ex-filtro').focus(); }

async function copiar(distrito) {
  try {
    await navigator.clipboard.writeText(distrito.codigo);
    $('ex-estado').textContent = T.copiado(distrito);
  } catch {
    $('ex-estado').textContent = T.codigoDe(distrito);
  }
}

function renderItems() {
  const filtro = sinTildes($('ex-filtro').value.trim());
  const enCanton = Boolean(ex.canton);
  const lista = (enCanton ? ex.canton.distritos : ex.prov.cantones)
    .filter((x) => !filtro || sinTildes(x.nombre).includes(filtro) || x.codigo.includes(filtro));
  $('ex-items').replaceChildren(...lista.map((x) => enCanton
    ? crear('button', { type: 'button', class: 'chip distrito', title: T.copiarTitulo, onclick: () => copiar(x) },
        crear('span', { class: 'num' }, x.codigo), x.nombre)
    : crear('button', { type: 'button', class: 'chip', onclick: () => elegirCanton(x) },
        crear('span', { class: 'num' }, x.codigo.slice(1)), x.nombre)));
  $('ex-estado').textContent = lista.length ? T.cantidad(lista.length, enCanton) : T.sinResultados;
}

function renderExplorador() {
  $('ex-provincias').replaceChildren(...ex.provincias.map((p) => crear('li', {},
    crear('button', { type: 'button', 'aria-pressed': String(p === ex.prov), onclick: () => elegirProvincia(p) }, p.nombre))));
  const sep = () => crear('span', { 'aria-hidden': 'true' }, '›');
  $('ex-ruta').replaceChildren(...(ex.canton
    ? [crear('button', { type: 'button', onclick: () => elegirProvincia(ex.prov) }, ex.prov.nombre), sep(),
       crear('span', { class: 'actual', 'aria-current': 'location' }, ex.canton.nombre)]
    : [crear('span', { class: 'actual', 'aria-current': 'location' }, ex.prov.nombre), sep(), crear('span', {}, T.pasoCanton)]));
  $('ex-filtro').placeholder = ex.canton ? T.filtrarDistritos(ex.canton.nombre) : T.filtrarCantones(ex.prov.nombre);
  renderItems();
}

$('ex-filtro').addEventListener('input', renderItems);
getJSON('/todo.json').then((t) => { ex.provincias = t.provincias; elegirProvincia(t.provincias[0]); })
  .catch(() => { $('ex-provincias').replaceChildren(crear('li', { class: 'ex-estado' }, T.errorDatos)); });
