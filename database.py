import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)
def conectar():
    return psycopg2.connect(
        DATABASE_URL,
        sslmode="require"
    )

def inicializar_db():
    conn = conectar()
    cursor = conn.cursor()

    # ---- OPERATIVOS ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operativos (
        mensaje_id BIGINT PRIMARY KEY,
        timestamp BIGINT,
        columna INTEGER,
        procesado BOOLEAN DEFAULT FALSE,
        recordatorio_enviado BOOLEAN DEFAULT FALSE
    )
    """)

    # ---- ASISTENTES ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asistentes (
        operativo_id BIGINT,
        user_id BIGINT,
        estado TEXT,
        PRIMARY KEY (operativo_id, user_id)
    )
    """)

    # ---- SANCIONES ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sanciones (
        id_unico TEXT PRIMARY KEY,
        user_id BIGINT,
        nivel INTEGER,
        motivo TEXT,
        fecha_limite BIGINT,
        estado TEXT,
        canal_id BIGINT,
        mensaje_sancion_id BIGINT
    )
    """)
    # ---- JUSTIFICACIONES ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS justificaciones (
        operativo_id BIGINT,
        user_id BIGINT,
        mensaje_log_id BIGINT,
        PRIMARY KEY (operativo_id, user_id)
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()