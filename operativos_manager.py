from database import conectar

def agregar_operativo(mensaje_id, timestamp, columna):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO operativos (mensaje_id, timestamp, columna)
        VALUES (%s, %s, %s)
    """, (mensaje_id, timestamp, columna))

    conn.commit()
    cursor.close()
    conn.close()


def obtener_operativo(mensaje_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM operativos
        WHERE mensaje_id = %s
    """, (mensaje_id,))

    operativo = cursor.fetchone()

    if not operativo:
        cursor.close()
        conn.close()
        return None

    cursor.execute("""
        SELECT user_id, estado
        FROM asistentes
        WHERE operativo_id = %s
    """, (mensaje_id,))

    asistentes = cursor.fetchall()

    cursor.close()
    conn.close()

    asistentes_dict = {}
    si = 0
    no = 0

    for user_id, estado in asistentes:
        asistentes_dict[str(user_id)] = estado
        if estado == "SI":
            si += 1
        elif estado == "NO":
            no += 1

    return {
        "mensaje_id": mensaje_id,
        "timestamp": operativo[1],
        "columna": operativo[2],
        "si": si,
        "no": no,
        "asistentes": asistentes_dict
    }


def actualizar_contadores(mensaje_id, user_id, estado):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT estado FROM asistentes
        WHERE operativo_id = %s AND user_id = %s
    """, (mensaje_id, user_id))

    anterior = cursor.fetchone()

    if anterior:
        cursor.execute("""
            UPDATE asistentes
            SET estado = %s
            WHERE operativo_id = %s AND user_id = %s
        """, (estado, mensaje_id, user_id))
    else:
        cursor.execute("""
            INSERT INTO asistentes (operativo_id, user_id, estado)
            VALUES (%s, %s, %s)
        """, (mensaje_id, user_id, estado))

    conn.commit()
    cursor.close()
    conn.close()

    return obtener_operativo(mensaje_id)


def borrar_operativo(mensaje_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM asistentes
        WHERE operativo_id = %s
    """, (mensaje_id,))

    cursor.execute("""
        DELETE FROM operativos
        WHERE mensaje_id = %s
    """, (mensaje_id,))

    eliminado = cursor.rowcount > 0

    conn.commit()
    cursor.close()
    conn.close()

    return eliminado

def obtener_justificacion(operativo_id, user_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mensaje_log_id
        FROM justificaciones
        WHERE operativo_id = %s AND user_id = %s
    """, (operativo_id, user_id))

    resultado = cursor.fetchone()

    cursor.close()
    conn.close()

    return resultado[0] if resultado else None


def guardar_justificacion(operativo_id, user_id, mensaje_log_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO justificaciones (operativo_id, user_id, mensaje_log_id)
        VALUES (%s, %s, %s)
        ON CONFLICT (operativo_id, user_id)
        DO UPDATE SET mensaje_log_id = EXCLUDED.mensaje_log_id
    """, (operativo_id, user_id, mensaje_log_id))

    conn.commit()
    cursor.close()
    conn.close()

def obtener_operativos_pendientes():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT mensaje_id, timestamp, columna, procesado, recordatorio_enviado
        FROM operativos
        WHERE procesado = FALSE
    """)

    operativos = cursor.fetchall()

    cursor.close()
    conn.close()

    return operativos


def marcar_operativo_procesado(mensaje_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE operativos
        SET procesado = TRUE
        WHERE mensaje_id = %s
    """, (mensaje_id,))

    conn.commit()
    cursor.close()
    conn.close()


def marcar_recordatorio_enviado(mensaje_id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE operativos
        SET recordatorio_enviado = TRUE
        WHERE mensaje_id = %s
    """, (mensaje_id,))

    conn.commit()
    cursor.close()
    conn.close()