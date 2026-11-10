const entrada = document.getElementById('entrada');
const btnGenerar = document.getElementById('btnGenerar');
const btnFiltrar = document.getElementById('btnFiltrar');
const filtroNombre = document.getElementById('filtroNombre');
const filtroOrden = document.getElementById('filtroOrden');
const errorDiv = document.getElementById('error');
const resultadosDiv = document.getElementById('resultados');
const modoDiv = document.getElementById('modo');

// Indica si corre en modo simulado (se rellena desde el servidor si se desea).
// Por ahora se infiere: si no hay clave, el servidor usa mensajes de ejemplo.

btnGenerar.addEventListener('click', async () => {
  errorDiv.textContent = '';
  resultadosDiv.innerHTML = '';
  btnGenerar.disabled = true;
  btnGenerar.textContent = 'Generando...';

  const texto = entrada.value.trim();
  if (!texto) {
    errorDiv.textContent = 'Ingresa al menos un socio.';
    btnGenerar.disabled = false;
    btnGenerar.textContent = 'Generar mensajes';
    return;
  }

  const lineas = texto.split('\n').map(l => l.trim()).filter(l => l);

  try {
    const res = await fetch('/generar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ socios: lineas }),
    });

    if (res.status === 400) {
      errorDiv.textContent = 'No se pudieron generar los mensajes. Revisa el formato de entrada y los límites.';
      btnGenerar.disabled = false;
      btnGenerar.textContent = 'Generar mensajes';
      return;
    }

    if (!res.ok) {
      errorDiv.textContent = 'Error del servidor al generar los mensajes.';
      btnGenerar.disabled = false;
      btnGenerar.textContent = 'Generar mensajes';
      return;
    }

    const data = await res.json();
    renderizar(data.resultados || []);
  } catch (err) {
    errorDiv.textContent = 'Error al conectar con el servidor.';
  } finally {
    btnGenerar.disabled = false;
    btnGenerar.textContent = 'Generar mensajes';
  }
});

btnFiltrar.addEventListener('click', async () => {
  errorDiv.textContent = '';
  resultadosDiv.innerHTML = '';
  btnFiltrar.disabled = true;
  btnFiltrar.textContent = 'Filtrando...';

  const params = new URLSearchParams();
  if (filtroNombre.value.trim()) {
    params.append('nombre', filtroNombre.value.trim());
  }
  params.append('orden', filtroOrden.value);
  params.append('limite', '50');

  try {
    const res = await fetch('/historial?' + params.toString(), {
      method: 'GET',
    });

    if (res.status === 400) {
      errorDiv.textContent = 'No se pudo aplicar el filtro. Revisa los parámetros.';
      btnFiltrar.disabled = false;
      btnFiltrar.textContent = 'Aplicar filtro';
      return;
    }

    if (!res.ok) {
      errorDiv.textContent = 'Error del servidor al consultar el historial.';
      btnFiltrar.disabled = false;
      btnFiltrar.textContent = 'Aplicar filtro';
      return;
    }

    const filas = await res.json();
    const agrupado = agruparHistorialPorSocio(filas);
    renderizar(agrupado);
  } catch (err) {
    errorDiv.textContent = 'Error al conectar con el servidor.';
  } finally {
    btnFiltrar.disabled = false;
    btnFiltrar.textContent = 'Aplicar filtro';
  }
});

function agruparHistorialPorSocio(filas) {
  // Agrupa filas planas del historial por socio, tomando el mensaje más reciente de cada tono.
  const porSocio = new Map();

  for (const fila of filas) {
    const key = fila.nombre;
    if (!porSocio.has(key)) {
      porSocio.set(key, {
        nombre: fila.nombre,
        dias_vencidos: fila.dias_vencidos,
        plan: fila.plan,
        mensajes: [],
      });
    }
    const socio = porSocio.get(key);
    // Evita duplicar tono: solo agrega si aún no existe ese tono para este socio
    if (!socio.mensajes.find(m => m.tono === fila.tono)) {
      socio.mensajes.push({
        tono: fila.tono,
        mensaje: fila.mensaje,
      });
    }
  }

  return Array.from(porSocio.values());
}

function renderizar(resultados) {
  if (!resultados || resultados.length === 0) {
    resultadosDiv.textContent = 'No se generaron resultados.';
    return;
  }
  for (const r of resultados) {
    const bloque = document.createElement('div');
    bloque.className = 'resultado';

    const etiqueta = document.createElement('div');
    etiqueta.className = 'socio-label';
    etiqueta.textContent = `${r.nombre} · ${r.dias_vencidos} día(s) vencido(s) · ${r.plan}`;
    bloque.appendChild(etiqueta);

    for (const m of r.mensajes) {
      const contenedor = document.createElement('div');
      contenedor.className = 'mensaje';

      const tono = document.createElement('div');
      tono.className = 'tono';
      tono.textContent = m.tono;

      const texto = document.createElement('div');
      // Se inserta como nodo de texto (textContent), nunca como HTML: evita XSS.
      texto.textContent = m.mensaje;

      const btn = document.createElement('button');
      btn.className = 'copiar';
      btn.textContent = 'Copiar';
      btn.addEventListener('click', () => {
        navigator.clipboard.writeText(m.mensaje).then(() => {
          const prev = btn.textContent;
          btn.textContent = '¡Copiado!';
          setTimeout(() => { btn.textContent = prev; }, 1500);
        });
      });

      contenedor.appendChild(tono);
      contenedor.appendChild(texto);
      contenedor.appendChild(btn);
      bloque.appendChild(contenedor);
    }
    resultadosDiv.appendChild(bloque);
  }
}
