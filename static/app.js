const entrada = document.getElementById('entrada');
const btnGenerar = document.getElementById('btnGenerar');
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
