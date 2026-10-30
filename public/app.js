// Buscador de códigos postales, selectores y lista GAM de la página principal.
// Los textos cambian según el atributo lang del <html> (es o en).

const TEXTOS = {
  es: {
    elegirProvincia: 'Elegí una provincia',
    elegirCanton: 'Elegí un cantón',
    elegirDistrito: 'Elegí un distrito',
    cpNoExiste: 'Ese código postal no existe.',
    sinResultados: 'No encontramos ese distrito, cantón ni código postal.',
    copiar: 'Copiar',
    copiado: 'Copiado',
    enGam: 'GAM',
    fueraGam: 'Fuera de la GAM',
    verPagina: 'Ver página del distrito',
    resultados: (n) => `${n} ${n === 1 ? 'resultado' : 'resultados'}`,
    mostrarMas: (k, resto) => `Mostrar ${k} más (quedan ${resto})`,
    total: (n) => `${n} ${n === 1 ? 'distrito' : 'distritos'}`,
  },
  en: {
    elegirProvincia: 'Choose a province',
    elegirCanton: 'Choose a canton',
    elegirDistrito: 'Choose a district',
    cpNoExiste: 'That postal code does not exist.',
    sinResultados: 'No district, canton or postal code matches that search.',
    copiar: 'Copy',
    copiado: 'Copied',
    enGam: 'GAM',
    fueraGam: 'Outside the GAM',
    verPagina: 'See district page',
    resultados: (n) => `${n} ${n === 1 ? 'result' : 'results'}`,
    mostrarMas: (k, resto) => `Show ${k} more (${resto} left)`,
    total: (n) => `${n} ${n === 1 ? 'district' : 'districts'}`,
  },
};
const LANG = document.documentElement.lang === 'en' ? 'en' : 'es';
const T = TEXTOS[LANG];
const PREFIJO = LANG === 'en' ? '/en' : '';

const $ = (id) => document.getElementById(id);
const getJSON = (url) => fetch(url).then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); });
const pad = (n) => String(n).padStart(2, '0');
const sinTildes = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();

function crear(tag, attrs = {}, ...hijos) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) k.startsWith('on') ? e.addEventListener(k.slice(2), v) : e.setAttribute(k, v);
  e.append(...hijos);
  return e;
}

function etiquetaGam(nodo, esGam) {
  nodo.textContent = esGam ? T.enGam : T.fueraGam;
  nodo.classList.toggle('si', esGam);
  nodo.hidden = false;
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

// Índice de los 494 distritos: c = código postal, d = distrito, k = cantón, p = provincia, g = GAM (1/0), u = página
const indice = getJSON('/buscador.json').then((filas) => filas.map((f) => ({
  ...f, texto: sinTildes(`${f.d} ${f.k} ${f.p}`), distrito: sinTildes(f.d), canton: sinTildes(f.k),
})));
const porCodigo = indice.then((filas) => new Map(filas.map((f) => [f.c, f])));

// Totales en vivo desde /meta.json
getJSON('/meta.json').then((m) => {
  for (const k of ['provincias', 'cantones', 'distritos']) $('n-' + k).textContent = m.totales[k];
  $('fuente').href = m.fuente.url;
}).catch(() => {});

// Buscador principal: por nombre de distrito o cantón, o por código postal. Devuelve todas las coincidencias,
// ordenadas: distrito con ese nombre, distrito que empieza así, cantón con ese nombre, cantón que empieza así,
// nombre que lo contiene y, al final, las que solo coinciden por la provincia.
function buscar(filas, consulta) {
  const q = sinTildes(consulta.trim()).replace(/\s+/g, ' ');
  if (!q) return [];
  if (/^\d+$/.test(q)) return filas.filter((f) => f.c.startsWith(q));
  const palabras = q.split(' ').filter((w) => !['de', 'del', 'la', 'el', 'en'].includes(w));
  const puntaje = (f) => {
    const nivel = [f.distrito === q, f.distrito.startsWith(q), f.canton === q, f.canton.startsWith(q),
      f.distrito.includes(q), f.canton.includes(q)].indexOf(true);
    return nivel === -1 ? 6 : nivel;
  };
  return filas.filter((f) => palabras.every((w) => f.texto.includes(w)))
    .sort((a, b) => puntaje(a) - puntaje(b) || a.c.localeCompare(b.c));
}

function resultado(f) {
  const etiqueta = crear('span', { class: 'etiqueta-gam' });
  etiquetaGam(etiqueta, f.g === 1);
  const boton = crear('button', { type: 'button', class: 'copiar' }, T.copiar);
  const codigo = crear('span', { class: 'cp' }, f.c);
  boton.addEventListener('click', () => copiar(boton, f.c, codigo));
  return crear('li', {},
    crear('a', { href: PREFIJO + f.u }, crear('span', { class: 'lugar' }, f.d), crear('span', { class: 'lugar-ruta' }, `${f.k} · ${f.p}`)),
    codigo, etiqueta, boton);
}

// Los resultados se muestran de a PASO, con un botón para ver los siguientes
const PASO = 10;
let coincidencias = [], mostrados = 0;

function mostrarMas() {
  const lista = $('resultados');
  lista.querySelector('.mas')?.remove();
  const nuevos = coincidencias.slice(mostrados, mostrados + PASO).map(resultado);
  lista.append(...nuevos);
  mostrados += nuevos.length;
  const resto = coincidencias.length - mostrados;
  if (resto > 0) {
    lista.append(crear('li', { class: 'mas' },
      // Al pedir más, el foco pasa al primer resultado nuevo para quien navega con teclado
      crear('button', { type: 'button', class: 'boton-mas', onclick: () => mostrarMas()[0]?.querySelector('a').focus() },
        T.mostrarMas(Math.min(PASO, resto), resto))));
  }
  return nuevos;
}

$('buscador').addEventListener('input', async (e) => {
  const v = e.target.value;
  coincidencias = buscar(await indice, v);
  mostrados = 0;
  const lista = $('resultados'), total = $('resultados-total');
  lista.replaceChildren();
  if (!v.trim()) { total.textContent = ''; return; }
  if (!coincidencias.length) {
    total.textContent = '';
    const msg = /^\d{5}$/.test(v.trim()) ? T.cpNoExiste : T.sinResultados;
    return lista.replaceChildren(crear('li', { class: 'sin-resultados' }, msg));
  }
  total.textContent = T.resultados(coincidencias.length);
  mostrarMas();
});
// Enter abre el primer resultado
$('form-buscador').addEventListener('submit', async (e) => {
  e.preventDefault();
  const [primero] = buscar(await indice, $('buscador').value);
  if (primero) location.href = PREFIJO + primero.u;
});

// Selectores en cascada: provincia → cantón → distrito
function fill(select, data, placeholder) {
  select.replaceChildren(crear('option', { value: '' }, placeholder),
    ...Object.entries(data).map(([k, v]) => crear('option', { value: k }, v)));
  select.disabled = false;
}
function reset(select) { select.replaceChildren(crear('option', { value: '' }, '—')); select.disabled = true; }
async function showCP(text = '') {
  $('cp').textContent = text;
  const boton = $('copiar-cp'), enlace = $('cp-enlace');
  boton.hidden = !text;
  boton.textContent = T.copiar;
  boton.classList.remove('listo');
  enlace.hidden = true;
  $('cp-gam').hidden = true;
  if (!text) return;
  const f = (await porCodigo).get(text);
  if (f) {
    etiquetaGam($('cp-gam'), f.g === 1);
    enlace.href = PREFIJO + f.u;
    enlace.textContent = T.verPagina;
    enlace.hidden = false;
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
  showCP(d ? `${p}${pad(c)}${pad(d)}` : '');
});

// Lista de distritos dentro y fuera de la GAM
async function renderLista() {
  const zona = document.querySelector('input[name="zona"]:checked').value;
  const filtro = sinTildes($('filtro-lista').value.trim());
  const filas = (await indice).filter((f) => (zona === 'todas' || (f.g === 1) === (zona === 'gam')) &&
    (!filtro || f.c.startsWith(filtro) || f.texto.includes(filtro)));
  $('lista-gam').replaceChildren(...filas.map((f) => {
    const etiqueta = crear('span', { class: 'etiqueta-gam' });
    const subEtiqueta = crear('span', { class: 'etiqueta-gam sub-gam' });
    etiquetaGam(etiqueta, f.g === 1);
    etiquetaGam(subEtiqueta, f.g === 1);
    // En celular, cantón, provincia y zona se muestran debajo del distrito y sus columnas se ocultan
    return crear('tr', {}, crear('td', {}, crear('code', {}, f.c)),
      crear('td', {}, crear('a', { href: PREFIJO + f.u }, f.d), crear('span', { class: 'sub' }, `${f.k} · ${f.p}`), subEtiqueta),
      crear('td', {}, f.k), crear('td', {}, f.p), crear('td', {}, etiqueta));
  }));
  $('lista-total').textContent = T.total(filas.length);
}
document.querySelectorAll('input[name="zona"]').forEach((r) => r.addEventListener('change', renderLista));
$('filtro-lista').addEventListener('input', renderLista);
renderLista();
