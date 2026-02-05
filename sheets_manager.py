import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

CREDS_FILE = "operativosbot-8d6da3299e13.json"
SHEET_NAME = "OperativosBot"

def conectar_sheet():
    SCOPE = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_json = os.getenv("GOOGLE_CREDS")
    creds_dict = json.loads(creds_json)

    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        creds_dict,
        SCOPE
    )

    client = gspread.authorize(creds)
    sheet = client.open("NOMBRE_TU_SHEET").sheet1

    return sheet

def obtener_o_crear_fila(sheet, user_id, username):
    ids = sheet.col_values(1)

    if str(user_id) in ids:
        return ids.index(str(user_id)) + 1

    nueva_fila = len(ids) + 1
    sheet.update_cell(nueva_fila, 1, str(user_id))
    sheet.update_cell(nueva_fila, 2, username)

    print(f"🆕 Usuario creado en fila {nueva_fila}")
    return nueva_fila

def escribir_asistencia(sheet, fila, dia, estado, hora, justificacion=None):
    columnas = {
        "Lunes": 3,
        "Martes": 4,
        "Miércoles": 5,
        "Jueves": 6,
        "Viernes": 7,
        "Sábado": 8,
        "Domingo": 9
    }

    col = columnas[dia]

    if estado == "SI":
        texto = f"SI\nHora de marcación: {hora}"
    else:
        texto = (
            f"NO\n"
            f"Justificación: {justificacion}\n"
            f"Hora de marcación: {hora}"
        )

    sheet.update_cell(fila, col, texto)

    actualizar_total(sheet, fila)
def actualizar_total(sheet, fila):
    valores = sheet.row_values(fila)[2:9]  # Lunes a Domingo

    contador = 0
    for v in valores:
        if v.startswith("SI"):
            contador += 1

    sheet.update_cell(fila, 10, f"{contador}/7")
def crear_columna_operativo(sheet, fecha):
    headers = sheet.row_values(1)

    # asegurar TOTAL primero
    if len(headers) < 3 or headers[2] != "Total":
        sheet.insert_cols([["Total"]], col=3)
        headers = sheet.row_values(1)

    nueva_col = len(headers) + 1
    sheet.update_cell(1, nueva_col, fecha)

    print(f"📅 Nueva columna creada para operativo {fecha} en col {nueva_col}")
    return nueva_col
def escribir_asistencia_operativo(sheet, fila, columna, estado, hora, justificacion=None):
    if estado == "SI":
        texto = f"SI\nHora: {hora}"
    else:
        texto = f"NO\nJustificación: {justificacion}\nHora: {hora}"

    sheet.update_cell(fila, columna, texto)
def actualizar_total(sheet, fila):
    headers = sheet.row_values(1)

    total_operativos = len(headers) - 3  # ID, Usuario, Total

    fila_vals = sheet.row_values(fila)[3:]  # desde col 4
    asistencias = 0

    for celda in fila_vals:
        if celda.startswith("SI"):
            asistencias += 1

    sheet.update_cell(fila, 3, f"{asistencias}/{total_operativos}")
def borrar_columna_operativo(sheet, columna):
    sheet.delete_columns(columna)
    print(f"🗑 Columna {columna} eliminada del Sheets")
def asegurar_columna_total(sheet):
    headers = sheet.row_values(1)

    if len(headers) < 3 or headers[2] != "Total":
        sheet.insert_cols([["Total"]], col=3)
        print("📊 Columna TOTAL creada")
def recalcular_totales_global(sheet):
    headers = sheet.row_values(1)

    total_operativos = len(headers) - 3  # ID, Usuario, Total

    filas = sheet.get_all_values()

    for i in range(1, len(filas)):  # saltar header
        fila_num = i + 1

        fila_vals = sheet.row_values(fila_num)[3:]
        asistencias = 0

        for celda in fila_vals:
            if celda.startswith("SI"):
                asistencias += 1

        sheet.update_cell(fila_num, 3, f"{asistencias}/{total_operativos}")

    print("🔄 Totales recalculados")
