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
    """Devuelve los mensajes guardados, con filtro opcional por nombre
    (insensible a mayúsculas/minúsculas) y ordenamiento por días vencidos
    (asc o desc). No incluye datos de contacto (no hay teléfonos)."""
    if orden not in ("asc", "desc"):
        raise ValueError("Orden inválido: use 'asc' o 'desc'")

    direccion = "ASC" if orden == "asc" else "DESC"

    conn = get_conn()
    try:
        if nombre:
            cur = conn.execute(
                f"""
                SELECT nombre, dias_vencidos, plan, tono, mensaje, fecha_creacion
                FROM mensajes_generados
                WHERE LOWER(nombre) = LOWER(?)
                ORDER BY dias_vencidos {direccion}
                LIMIT ?
                """,
                (nombre, limite),
            )
        else:
            cur = conn.execute(
                f"""
                SELECT nombre, dias_vencidos, plan, tono, mensaje, fecha_creacion
                FROM mensajes_generados
                ORDER BY dias_vencidos {direccion}
                LIMIT ?
                """,
                (limite,),
            )
        return cur.fetchall()
    finally:
        conn.close()
