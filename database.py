import psycopg2
import psycopg2.extras
import os
DATABASE_URL = os.getenv("DATABASE_URL")
print("DATABASE_URL:", DATABASE_URL)

def conectar():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=psycopg2.extras.RealDictCursor
    )
def inicializar_db():
    conn = conectar()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

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
        mensaje_sancion_id BIGINT,
        contador_mensaje_id BIGINT
    )
    """)
    cursor.execute("ALTER TABLE sanciones ADD COLUMN IF NOT EXISTS mensaje_privado_id BIGINT;")
    cursor.execute("ALTER TABLE sanciones ADD COLUMN IF NOT EXISTS contador_mensaje_id BIGINT;")
    # ---- JUSTIFICACIONES ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS justificaciones (
        operativo_id BIGINT,
        user_id BIGINT,
        mensaje_log_id BIGINT,
        PRIMARY KEY (operativo_id, user_id)
    )
    """)
    # ---- ARMAMENTO LOGS ACTUAL ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armamento_logs (
        id SERIAL PRIMARY KEY,
        message_id BIGINT UNIQUE,
        user_id BIGINT,
        username TEXT,
        tipo TEXT,
        categoria TEXT,
        objeto_nombre TEXT,
        objeto_codigo TEXT,
        cantidad INTEGER,
        almacen TEXT,
        timestamp BIGINT
    )
    """)
    # ---- ARMAMENTO HISTORIAL ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armamento_logs_historial (
        id SERIAL PRIMARY KEY,
        message_id BIGINT,
        user_id BIGINT,
        username TEXT,
        tipo TEXT,
        categoria TEXT,
        objeto_nombre TEXT,
        objeto_codigo TEXT,
        cantidad INTEGER,
        almacen TEXT,
        timestamp BIGINT,
        semana INTEGER
    )
    """)
    # ---- CONTROL SEMANA ARMAMENTO ----
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS armamento_control (
        id INTEGER PRIMARY KEY,
        ultima_semana INTEGER
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()