import os
import sqlite3
import tempfile

from fastapi.testclient import TestClient

# Forzar modo simulado: asegurar que no hay GEMINI_API_KEY antes de importar la app
os.environ.pop("GEMINI_API_KEY", None)

import db  # noqa: E402
import main  # noqa: E402

client = TestClient(main.app)


def _crear_bd_temporal():
    """Crea una base de datos SQLite temporal y la configura en el módulo db."""
    tmp_dir = tempfile.mkdtemp()
    tmp_path = os.path.join(tmp_dir, "test_historial.db")
    conn = sqlite3.connect(tmp_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS mensajes_generados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            dias_vencidos INTEGER,
            plan TEXT,
            tono TEXT,
            mensaje TEXT,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP,
            enviado INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    conn.close()
    return tmp_path


def test_modo_simulado_sin_api_key(monkeypatch):
    """Con GEMINI_API_KEY desactivada, la app genera 3 mensajes por socio en modo simulado."""
    # Eliminar la variable de entorno para forzar modo simulado
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    respuesta = client.post(
        "/generar",
        json={"socios": ["Maria Lopez|14|Mensualidad", "Juan Perez|5|Anual"]},
    )
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert "resultados" in datos
    assert len(datos["resultados"]) == 2

    for socio in datos["resultados"]:
        assert socio["nombre"] in ("Maria Lopez", "Juan Perez")
        assert len(socio["mensajes"]) == 3
        tonos = {m["tono"] for m in socio["mensajes"]}
        assert tonos == {"amable", "directo", "motivacional"}
        for mensaje in socio["mensajes"]:
            assert len(mensaje["mensaje"]) <= 280


def test_validacion_entrada():
    """La app rechaza peticiones con formato inválido o que exceden los límites."""
    # Más de 30 socios -> 400
    respuesta = client.post(
        "/generar",
        json={"socios": ["a|1|b"] * 31},
    )
    assert respuesta.status_code == 400

    # Línea inválida (solo dos campos) -> 400
    respuesta = client.post(
        "/generar",
        json={"socios": ["solo dos campos"]},
    )
    assert respuesta.status_code == 400

    # Días negativos -> 400
    respuesta = client.post(
        "/generar",
        json={"socios": ["Ana|-3|Plan"]},
    )
    assert respuesta.status_code == 400

    # Nombre muy largo (>60) -> 400
    respuesta = client.post(
        "/generar",
        json={"socios": ["A" * 70 + "|1|Plan"]},
    )
    assert respuesta.status_code == 400


def test_historial_sqlite():
    """Los mensajes generados se guardan en SQLite y se pueden consultar con filtro y orden."""
    # Usar BD temporal para no tocar la del proyecto
    tmp_path = _crear_bd_temporal()
    db.DB_PATH = tmp_path

    try:
        # Generar mensajes para varios socios
        respuesta = client.post(
            "/generar",
            json={
                "socios": [
                    "Maria Lopez|14|Mensualidad",
                    "Juan Perez|5|Anual",
                    "Juan Perez|5|Mensualidad",
                ]
            },
        )
        assert respuesta.status_code == 200

        # Consultar historial sin filtro
        respuesta = client.get("/historial")
        assert respuesta.status_code == 200
        datos = respuesta.json()
        assert len(datos) > 0

        # Verificar que todos los registros tienen los campos esperados
        for registro in datos:
            assert "id" in registro
            assert "nombre" in registro
            assert "dias_vencidos" in registro
            assert "plan" in registro
            assert "tono" in registro
            assert "mensaje" in registro
            assert "enviado" in registro

        # Filtro por nombre (insensible a mayúsculas)
        respuesta = client.get("/historial?nombre=MARIA LOPEZ")
        assert respuesta.status_code == 200
        datos_filtrado = respuesta.json()
        assert len(datos_filtrado) > 0
        for registro in datos_filtrado:
            assert registro["nombre"].lower() == "maria lopez"

        # Verificar que Juan Perez con planes distintos queda en tarjetas separadas
        juan_registros = [r for r in datos if r["nombre"].lower() == "juan perez"]
        planes_juan = {r["plan"] for r in juan_registros}
        assert "Anual" in planes_juan
        assert "Mensualidad" in planes_juan

        # Orden ascendente
        respuesta = client.get("/historial?orden=asc")
        assert respuesta.status_code == 200
        datos_asc = respuesta.json()
        dias_asc = [r["dias_vencidos"] for r in datos_asc]
        assert dias_asc == sorted(dias_asc)

        # Orden descendente
        respuesta = client.get("/historial?orden=desc")
        assert respuesta.status_code == 200
        datos_desc = respuesta.json()
        dias_desc = [r["dias_vencidos"] for r in datos_desc]
        assert dias_desc == sorted(dias_desc, reverse=True)

    finally:
        # Limpiar BD temporal
        db.DB_PATH = "recordatorios.db"
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
            os.rmdir(os.path.dirname(tmp_path))
