import psycopg2

from database import conectar

def insertar_log(data):

    conn = conectar()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""
        INSERT INTO armamento_logs (
            message_id, user_id, username, tipo,
            categoria, objeto_nombre, objeto_codigo,
            cantidad, almacen, timestamp
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING
    """, (
        data["message_id"],
        data["user_id"],
        data["username"],
        data["tipo"],
        data["categoria"],
        data["objeto_nombre"],
        data["objeto_codigo"],
        data["cantidad"],
        data["almacen"],
        data["timestamp"]
    ))

    conn.commit()
    conn.close()

def obtener_logs_usuario(user_id, timestamp_inicio):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM armamento_logs
        WHERE user_id = %s
        AND timestamp >= %s
    """, (user_id, timestamp_inicio))

    rows = cursor.fetchall()
    conn.close()
    return rows


def obtener_logs_desde(timestamp_inicio):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM armamento_logs
        WHERE timestamp >= %s
    """, (timestamp_inicio,))

    rows = cursor.fetchall()
    conn.close()
    return rows