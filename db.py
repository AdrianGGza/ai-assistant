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


def obtener_historial(limite: int = 50):
    """Devuelve los mensajes guardados, sin incluir datos de contacto (no hay teléfonos)."""
    conn = get_conn()
    try:
        cur = conn.execute(
            """
            SELECT nombre, dias_vencidos, plan, tono, mensaje, fecha_creacion
            FROM mensajes_generados
            ORDER BY id DESC
            LIMIT ?
            """,
            (limite,),
        )
        return cur.fetchall()
    finally:
        conn.close()
