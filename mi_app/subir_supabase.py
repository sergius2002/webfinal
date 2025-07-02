import warnings
warnings.filterwarnings("ignore", message="Data Validation extension is not supported and will be removed")

import os
import pandas as pd
from datetime import datetime
from supabase import create_client
from typing import Union

# ---------------- Configuración Global ----------------
# Fecha global en formato YYYY-MM-DD (manual)
fecha_global = "2025-06-30"
# Derivar fecha para DETAL (día-mes) y nombre de archivo MAYOR (YYYYMMDD)
try:
    dt_global = datetime.strptime(fecha_global, "%Y-%m-%d")
    target_detal = f"{dt_global.day:02d}-{dt_global.month:02d}"
    nombre_archivo_mayor = dt_global.strftime("%Y%m%d")
except ValueError:
    raise ValueError(f"Formato inválido en fecha_global: {fecha_global}. Debe ser YYYY-MM-DD.")

# Rutas y credenciales
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0."
    "tTrdPaiPAkQb_F_JlfOOWQwSs3C_zBbFDZECYzPP-Ho"
)
# Archivo Excel cartera MAYOR (usa fecha_global para construir el nombre)
ARCHIVO_MAYOR = (
    f"/Users/sergioplaza/Library/CloudStorage/OneDrive-Personal/"
    f"Sergio/Clientes 2023/{nombre_archivo_mayor}.xlsm"
)
HOJA_MAYOR = "Pedidos"

# Archivo Excel cartera DETAL
ARCHIVO_DETAL = (
    "/Users/sergioplaza/Library/CloudStorage/OneDrive-Personal/"
    "Eudimar y Franco/Ventas detal.xlsx"
)

# Flag preview: si True, no sube a Supabase
autenvista = False

# ---------------- Funciones Comunes ----------------
def get_cliente_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if col.lower() == 'cliente':
            return col
    raise ValueError("No se encontró la columna 'cliente'.")

# ---------------- Funciones Cartera MAYOR ----------------
def leer_excel_y_filtrar_columnas(archivo_excel: str, nombre_hoja: str) -> (pd.DataFrame, list):
    if not os.path.exists(archivo_excel):
        raise FileNotFoundError(f"El archivo '{archivo_excel}' no fue encontrado.")
    df_pedidos = pd.read_excel(archivo_excel, sheet_name=nombre_hoja, header=1, usecols="A:CW", nrows=108)
    # Eliminar columnas intermedias de cada bloque de 5 columnas
    cols_remove = []
    for i in range(1, df_pedidos.shape[1], 5):
        cols_remove.extend([i+3, i+4])
    df_pedidos = df_pedidos.drop(df_pedidos.columns[cols_remove], axis=1)
    df_pedidos = df_pedidos.dropna(axis=1, how='all')
    # Lista de clientes con al menos un pedido
    clientes = df_pedidos[df_pedidos.iloc[:, 1].notnull()].iloc[:, 0].tolist()
    return df_pedidos, clientes

def generar_df_pedidos_cliente(df_pedidos: pd.DataFrame, nombre_cliente: str) -> pd.DataFrame:
    fila = df_pedidos[df_pedidos.iloc[:, 0] == nombre_cliente]
    if fila.empty:
        return pd.DataFrame()
    seq = ["Tasa", "Brs", "Clp"]
    columnas_data = fila.columns[1:]
    mapping = {columnas_data[i]: seq[i % len(seq)] for i in range(len(columnas_data))}
    df_cli = fila.rename(columns=mapping).iloc[:, 1:]
    df_cli = df_cli.dropna(axis=1, how='all')
    df_cli['cliente'] = nombre_cliente
    return df_cli

# Procesa cartera MAYOR y genera registros listos para insertar
def procesar_mayor(archivo: str, hoja: str) -> list:
    df, clientes = leer_excel_y_filtrar_columnas(archivo, hoja)
    registros = []
    for nombre in clientes:
        df_cli = generar_df_pedidos_cliente(df, nombre)
        for _, row in df_cli.iterrows():
            try:
                registros.append({
                    'usuario': 'sergio.plaza@me.com',
                    'cliente': nombre,
                    # Multiplicar tasa por 1_000_000
                    'tasa': int(round(float(row['Tasa']) * 1_000_000)),
                    'brs': int(round(float(row['Brs']))),
                    'fecha': fecha_global
                })
            except Exception:
                continue
    return registros

# ---------------- Funciones Cartera DETAL ----------------
def convertir_fecha(sheet_name: str, year: int) -> str:
    day, month = sheet_name.split("-")
    fecha = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    datetime.strptime(fecha, "%Y-%m-%d")
    return fecha

# Lee solo la hoja correspondiente a target_date ("DD-MM")
def leer_ventas_detal(file_path: str, target_date: str) -> list:
    xls = pd.ExcelFile(file_path)
    registros = []
    año = datetime.now().year
    for hoja in xls.sheet_names:
        if hoja != target_date:
            continue
        try:
            fecha = convertir_fecha(hoja, año)
            df = pd.read_excel(file_path, sheet_name=hoja, header=6).dropna(how='all')
            if not {'Tasa', 'BRs'}.issubset(df.columns):
                continue
            for _, row in df.iterrows():
                t, b = row['Tasa'], row['BRs']
                if pd.isna(t) or pd.isna(b):
                    continue
                registros.append({
                    'usuario': 'sergio.plaza@me.com',
                    'cliente': 'DETAL',
                    'tasa': int(round(t)),
                    'brs': int(round(b)),
                    'fecha': fecha
                })
        except Exception:
            continue
    return registros

# ---------------- Subida a Supabase ----------------
def subir_a_supabase(records: Union[list, pd.DataFrame]):
    if not records:
        print("No hay registros para subir.")
        return
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if isinstance(records, pd.DataFrame):
        records = records.to_dict('records')
    resp = client.table('pedidos').insert(records).execute()
    if hasattr(resp, 'data') and resp.data:
        print(f"Subidos {len(resp.data)} registros correctamente.")
    else:
        print(f"Error al subir a Supabase: {resp}")

# ---------------- EJECUCIÓN ----------------
# 1) Procesar MAYOR
regs_may = []
try:
    regs_may = procesar_mayor(ARCHIVO_MAYOR, HOJA_MAYOR)
    print(f"Pedidos MAYOR: {len(regs_may)} registros.")
except Exception as e:
    print(f"Error en cartera MAYOR: {e}")

# 2) Procesar DETAL
regs_det = []
try:
    regs_det = leer_ventas_detal(ARCHIVO_DETAL, target_detal)
    print(f"Ventas DETAL: {len(regs_det)} registros.")
except Exception as e:
    print(f"Error en cartera DETAL: {e}")

# 3) Unir y subir
todos = regs_may + regs_det
print(f"Total a subir: {len(todos)} registros.")
if not autenvista:
    subir_a_supabase(todos)
else:
    print("Modo preview activado: no se sube nada.")
