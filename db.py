import sqlite3
from datetime import datetime

DB_PATH = "recordatorios.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Crea la tabla de historial si no existe."""
    conn = get_conn()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS mensajes_generados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                dias_vencidos INTEGER,
                plan TEXT,
                tono TEXT,
                mensaje TEXT,
                fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def guardar(nombre: str, dias_vencidos: int, plan: str, tono: str, mensaje: str):
    """Guarda un mensaje generado en el historial (sin datos sensibles extra)."""
    conn = get_conn()
    try:
        conn.execute(
            """
            INSERT INTO mensajes_generados (nombre, dias_vencidos, plan, tono, mensaje, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (nombre, dias_vencidos, plan, tono, mensaje, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def obtener_historial(nombre: str | None, limite: int = 50, orden: str = "desc"):
    if orden not in ("asc", "desc"):
        raise ValueError("Orden inválido: use 'asc' o 'desc'")

    direccion = "ASC" if orden == "asc" else "DESC"
    filtro = "WHERE LOWER(nombre) = LOWER(?)" if nombre else ""
    params = [nombre] if nombre else []

    conn = get_conn()
    try:
        cur = conn.execute(
            f"""
            SELECT id, nombre, dias_vencidos, plan, tono, mensaje, fecha_creacion
            FROM (
                SELECT *,
                       ROW_NUMBER() OVER (
                           PARTITION BY LOWER(nombre), plan, tono
                           ORDER BY fecha_creacion DESC, id DESC
                       ) AS rn
                FROM mensajes_generados
                {filtro}
            )
            WHERE rn = 1
            ORDER BY dias_vencidos {direccion}, LOWER(nombre), plan, tono
            LIMIT ?
            """,
            (*params, limite),
        )
        return cur.fetchall()
    finally:
        conn.close()
