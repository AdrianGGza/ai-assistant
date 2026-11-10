const entrada = document.getElementById('entrada');
const btnGenerar = document.getElementById('btnGenerar');
const btnFiltrar = document.getElementById('btnFiltrar');
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
  btnFiltrar.textContent = 'Aplicando...';

  try{
    const params = new URLSearchParams({
      orden: filtroOrden.value,
      limite: '50',
    });

    const res = await fetch('/historial?' + params.toString());

    if (res.status === 400){
      errorDiv.textContent = 'No se pudo aplicar el orden. Revisa los parametros'
      return;
    }
    if(!res.ok){
      errorDiv.textContent = 'Error del servidor al consultar el historial'
      return;
    }

    const filas = await res.json();
    renderizar(agruparHistorialPorSocio(filas));
  } catch(err){
    console.error('Error real en orden: ',err);
    errorDiv.textContent = 'Error al consultar el historial';
  }finally {
    btnFiltrar.disabled = false;
    btnFiltrar.textContent = 'Aplicar orden'
  }
});

function agruparHistorialPorSocio(filas) {
  // Agrupa filas planas del historial por socio.
  // La DB ya devuelve solo el mensaje más reciente por socio+tono (ROW_NUMBER rn=1),
  // por lo que no hay que recalcular fechas ni verificar duplicados aquí.
  const porSocio = new Map();

  for (const fila of filas) {
    const key = `${fila.nombre.toLowerCase()}|${fila.plan}|${fila.dias_vencidos}`;
    if (!porSocio.has(key)) {
      porSocio.set(key, {
        id: fila.id,
        nombre: fila.nombre,
        dias_vencidos: fila.dias_vencidos,
        plan: fila.plan,
        mensajes: [],
      });
    }
    const socio = porSocio.get(key);
    socio.mensajes.push({
      id: fila.id,
      tono: fila.tono,
      mensaje: fila.mensaje,
      enviado: fila.enviado,
    });
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

      // Contenedor de botones para separarlos del texto
      const contenedorBotones = document.createElement('div');
      contenedorBotones.className = 'botones-mensaje';

      // Botón copiar
      const btnCopiar = document.createElement('button');
      btnCopiar.className = 'copiar';
      btnCopiar.textContent = 'Copiar';
      btnCopiar.addEventListener('click', () => {
        navigator.clipboard.writeText(m.mensaje).then(() => {
          const prev = btnCopiar.textContent;
          btnCopiar.textContent = '¡Copiado!';
          setTimeout(() => { btnCopiar.textContent = prev; }, 1500);
        });
      });

      // Botón enviar
      const btnEnviar = document.createElement('button');
      btnEnviar.className = 'btn-enviar';
      btnEnviar.textContent = m.enviado ? 'Mensaje enviado' : 'Enviar';
      btnEnviar.disabled = m.enviado;
      btnEnviar.addEventListener('click', async () => {
        try {
          const res = await fetch(`/historial/${m.id}/enviado`, {
            method: 'PATCH',
          });
          if (res.ok) {
            contenedor.classList.add('enviado');
            btnEnviar.textContent = 'Mensaje enviado';
            btnEnviar.disabled = true;

            const estado = document.createElement('div');
            estado.className = 'estado-enviado';
            estado.textContent = 'Mensaje enviado';
            contenedor.appendChild(estado);
          }
        } catch (err) {
          errorDiv.textContent = 'Error al marcar como enviado.';
        }
      });

      contenedorBotones.appendChild(btnCopiar);
      contenedorBotones.appendChild(btnEnviar);

      contenedor.appendChild(tono);
      contenedor.appendChild(texto);
      contenedor.appendChild(contenedorBotones);

      // Mostrar estado si ya fue enviado (después de los botones)
      if (m.enviado) {
        contenedor.classList.add('enviado');
        const estado = document.createElement('div');
        estado.className = 'estado-enviado';
        estado.textContent = 'Mensaje enviado';
        contenedor.appendChild(estado);
      }

      bloque.appendChild(contenedor);
    }
    resultadosDiv.appendChild(bloque);
  }
}
