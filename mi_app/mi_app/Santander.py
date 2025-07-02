#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys  # Importar sys para usar en os.execv
import pandas as pd
from supabase import create_client, Client
import hashlib
from datetime import datetime
import time
import re
from dotenv import load_dotenv
import logging

# --------------------------------------------------------------------------------
# Configurar el logging para escribir en archivo y consola
# --------------------------------------------------------------------------------
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # INFO para evitar logs excesivos en consola

# Crear un formateador
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

# Handler para el archivo de log
file_handler = logging.FileHandler('flujo_san_cristobal.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Handler para la consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# Añadir ambos handlers al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --------------------------------------------------------------------------------
# Cargar variables de entorno desde .env
# --------------------------------------------------------------------------------
load_dotenv()

logger.info("Inicio del script.")

# --------------------------------------------------------------------------------
# Cargar variables de entorno (adaptadas a las usadas en tu proyecto)
# --------------------------------------------------------------------------------
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"
CARPETA_ARCHIVOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Santander_archivos")

if not all([SUPABASE_URL, SUPABASE_KEY, CARPETA_ARCHIVOS]):
    logger.error("Error: Faltan variables de entorno o rutas.")
    sys.exit(0)

# Después de cargar las variables de entorno
logger.info(f"Buscando archivos en la carpeta: {CARPETA_ARCHIVOS}")

# Verificar si la carpeta existe
if not os.path.exists(CARPETA_ARCHIVOS):
    logger.error(f"La carpeta {CARPETA_ARCHIVOS} no existe")
    sys.exit(0)

# Listar archivos en la carpeta para debug
logger.info("Archivos encontrados en la carpeta:")
for archivo in os.listdir(CARPETA_ARCHIVOS):
    logger.info(f"- {archivo}")

# --------------------------------------------------------------------------------
# Inicializar el cliente de Supabase
# --------------------------------------------------------------------------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Cliente de Supabase inicializado correctamente.")
except Exception as e:
    logger.error(f"Error al inicializar el cliente de Supabase: {e}")
    sys.exit(0)

# --------------------------------------------------------------------------------
# Diccionario que mapea cada cadena a su empresa o banco (usado en SANTANDER)
# --------------------------------------------------------------------------------
MAPEO_EMPRESAS = {
    "91404630": "SAN CRISTOBAL SPA",
    "91903610": "SAN CRISTOBAL SPA",
    "94288371": "ST CRISTOBAL SPA",
}

# --------------------------------------------------------------------------------
# Lista de cadenas para procesamiento actual en SANTANDER
# --------------------------------------------------------------------------------
CADENAS = list(MAPEO_EMPRESAS.keys())

# --------------------------------------------------------------------------------
# Lista de RUTs a eliminar
# --------------------------------------------------------------------------------
RUTS_A_ELIMINAR = [
    "77773448-2",
    "77469173-1",
    "77936187-K"
]

# --------------------------------------------------------------------------------
# Registro de archivos procesados
# --------------------------------------------------------------------------------
archivos_procesados = set()

# --------------------------------------------------------------------------------
# Funciones de Normalización
# --------------------------------------------------------------------------------
def normalizar_fecha(fecha_str):
    try:
        dt = pd.to_datetime(fecha_str, errors='coerce', dayfirst=True)
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error al normalizar fecha '{fecha_str}': {e}")
        return None

def normalizar_monto(valor):
    try:
        num = float(valor)
        if num.is_integer() and num > 0:
            return int(num)
        else:
            raise ValueError(f"Valor de monto inválido: {valor}")
    except ValueError as e:
        logger.error(f"Error al normalizar monto '{valor}': {e}")
        return None

def normalizar_rut(rut_str):
    try:
        rut = str(rut_str).replace(".", "").upper().strip()
        return rut
    except Exception as e:
        logger.error(f"Error al normalizar RUT '{rut_str}': {e}")
        return rut_str

def determinar_facturacion(rut_str):
    try:
        partes = rut_str.split("-")
        numero = partes[0] if len(partes) > 0 else rut_str
        rut_int = int(numero)
        if rut_int < 50000000:
            return "persona"
        else:
            return "empresa"
    except Exception as e:
        logger.warning(f"No se pudo determinar facturación para el RUT '{rut_str}'. Error: {e}")
        return "persona"

def calcular_hash(row):
    data = f"{row['monto']}_{row['fecha']}_{row['rut']}"
    return hashlib.md5(data.encode('utf-8')).hexdigest()

def manejar_respuesta(response, contexto):
    logger.debug(f"Respuesta de Supabase en {contexto}: {response}")
    logger.debug(f"Atributos de la respuesta: {dir(response)}")
    if hasattr(response, 'error') and response.error:
        logger.error(f"Error en {contexto}: {response.error}")
        return None
    elif hasattr(response, 'status_code') and response.status_code >= 400:
        logger.error(f"Error en {contexto}: {response.status_message}")
        return None
    return response.data

def get_all_hashes(supabase_client, batch_size=1000):
    all_hashes = []
    offset = 0
    while True:
        response = supabase_client.table('transferencias').select('hash').range(offset, offset + batch_size - 1).execute()
        batch = manejar_respuesta(response, "recuperar hashes existentes (paginado)")
        if not batch or len(batch) == 0:
            break
        all_hashes.extend(batch)
        if len(batch) < batch_size:
            break
        offset += batch_size
    logger.info(f"Se recuperaron {len(all_hashes)} hashes en total de la base de datos.")
    return set(item['hash'] for item in all_hashes if item.get('hash') is not None)

def SANTANDER():
    logger.info("Entrando en la función SANTANDER().")
    dataframes = []
    archivos_encontrados = 0
    rut_regex = re.compile(r'\\b0*([1-9]\\d{6,7})[-.]?([0-9Kk])\\b')
    for archivo in os.listdir(CARPETA_ARCHIVOS):
        if archivo.startswith("~$") or archivo in archivos_procesados:
            continue
        cadena_encontrada = None
        for cadena in CADENAS:
            if cadena in archivo:
                cadena_encontrada = cadena
                break
        if cadena_encontrada:
            archivos_encontrados += 1
            logger.info(f"Archivo encontrado: {archivo}. Procesando...")
            ruta_archivo = os.path.join(CARPETA_ARCHIVOS, archivo)
            try:
                df = pd.read_excel(ruta_archivo, engine="openpyxl", skiprows=11)
                columnas_relevantes = df[["MONTO", "DESCRIPCIÓN MOVIMIENTO", "FECHA"]].copy()
                columnas_relevantes["MONTO"] = columnas_relevantes["MONTO"].apply(normalizar_monto)
                columnas_relevantes = columnas_relevantes[columnas_relevantes["MONTO"].notna()]
                columnas_relevantes["CADENA"] = cadena_encontrada
                def extraer_rut(descripcion):
                    descripcion_limpia = descripcion.replace('.', '')
                    matches = rut_regex.findall(descripcion_limpia)
                    if matches:
                        numero, verificador = matches[0]
                        rut_completo = f"{numero}-{verificador.upper()}"
                        return rut_completo
                    else:
                        logger.warning(f"RUT no encontrado en la descripción: {descripcion}")
                        return None
                columnas_relevantes["rut"] = columnas_relevantes["DESCRIPCIÓN MOVIMIENTO"].apply(extraer_rut)
                columnas_relevantes = columnas_relevantes.dropna(subset=["rut"])
                columnas_relevantes["rut"] = columnas_relevantes["rut"].apply(normalizar_rut)
                columnas_relevantes = columnas_relevantes[~columnas_relevantes['rut'].isin(RUTS_A_ELIMINAR)]
                if columnas_relevantes.empty:
                    logger.info(f"Todos los registros en el archivo {archivo} están en la lista de RUTs a eliminar o no hay datos válidos. Omitiendo archivo.")
                    archivos_procesados.add(archivo)
                    continue
                columnas_relevantes["fecha"] = columnas_relevantes["FECHA"].apply(normalizar_fecha)
                columnas_relevantes = columnas_relevantes[columnas_relevantes["fecha"].notna()]
                columnas_relevantes = columnas_relevantes.rename(columns={"MONTO": "monto"})
                columnas_relevantes["facturación"] = columnas_relevantes["rut"].apply(determinar_facturacion)
                empresa = MAPEO_EMPRESAS.get(cadena_encontrada, "Desconocida")
                columnas_relevantes["empresa"] = empresa
                columnas_relevantes["hash"] = columnas_relevantes.apply(calcular_hash, axis=1)
                columnas_relevantes["rs"] = None
                columnas_relevantes = columnas_relevantes[
                    ["monto", "fecha", "rut", "facturación", "hash", "empresa", "rs"]]
                dataframes.append(columnas_relevantes)
                archivos_procesados.add(archivo)
                logger.info(f"Archivo procesado exitosamente: {archivo}")
                
                # Borrar el archivo después de procesarlo exitosamente
                try:
                    os.remove(ruta_archivo)
                    logger.info(f"Archivo borrado exitosamente: {archivo}")
                except Exception as e:
                    logger.error(f"Error al borrar el archivo {archivo}: {e}")
            except Exception as e:
                logger.error(f"Error al procesar el archivo {archivo} en SANTANDER: {e}")
    if archivos_encontrados == 0:
        logger.info("No se encontraron archivos nuevos para procesar en SANTANDER.")
    else:
        logger.info(f"Se encontraron y procesaron {archivos_encontrados} archivos en SANTANDER.")
    if dataframes:
        logger.info("Procesamiento completo. Archivos procesados.")
        return pd.concat(dataframes, ignore_index=True)
    else:
        logger.info("No se procesaron datos en SANTANDER.")
        return None

def BASE_DE_DATOS(df_resultado, supabase_client):
    if df_resultado is None or df_resultado.empty:
        logger.info("No se encontraron datos nuevos para agregar a la base de datos.")
        return
    logger.info(f"Cantidad de registros a revisar: {df_resultado.shape[0]}")
    duplicados = df_resultado[df_resultado.duplicated(subset=['hash'], keep=False)]
    if not duplicados.empty:
        logger.warning(
            "Existen filas con 'hash' duplicados en el DataFrame a insertar. Mostrando duplicados (columnas: rut, hash y fecha):")
        logger.warning(duplicados[['rut', 'hash', 'fecha']].to_string())
        df_resultado = df_resultado.drop_duplicates(subset=['hash'], keep='first')
        logger.info("Duplicados eliminados del DataFrame a insertar (manteniendo la primera ocurrencia).")
    try:
        logger.info("Recuperando hashes existentes en la base de datos (paginado)...")
        hashes_existentes = get_all_hashes(supabase_client, batch_size=1000)
        logger.debug(f"Hashes existentes: {hashes_existentes}")
    except Exception as e:
        logger.error(f"Error al interactuar con Supabase al recuperar hashes existentes: {e}")
        hashes_existentes = set()
    df_nuevos = df_resultado[~df_resultado['hash'].isin(hashes_existentes)]
    logger.info(f"Registros nuevos después de filtrar por hash: {df_nuevos.shape[0]}")
    if df_nuevos.empty:
        logger.info("No hay registros nuevos para insertar en la base de datos.")
        return
    else:
        logger.info(f"Se insertarán {df_nuevos.shape[0]} registros nuevos en la base de datos.")
    df_empresas = df_nuevos[df_nuevos["facturación"] == "empresa"]
    rs_dict = {}
    if not df_empresas.empty:
        ruts_empresas_unicos = df_empresas["rut"].unique().tolist()
        logger.info(f"Consultando 'rs' para {len(ruts_empresas_unicos)} RUT(s) de empresa en bloque...")
        for rut_emp in ruts_empresas_unicos:
            try:
                consulta_rs = supabase_client.table('datos_faltantes').select("rs").eq("rut", rut_emp).execute()
                rs_data = manejar_respuesta(consulta_rs, f"consultar 'rs' en bloque para rut {rut_emp}")
                if rs_data is not None and len(rs_data) > 0:
                    rs_dict[rut_emp] = rs_data[0].get("rs", None)
                else:
                    rs_dict[rut_emp] = None
            except Exception as e:
                logger.warning(f"Error consultando 'rs' para {rut_emp}: {e}")
                rs_dict[rut_emp] = None
    def determinar_fecha_detec(fecha_str):
        try:
            fecha_transaccion = datetime.strptime(fecha_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Formato de fecha inválido: {fecha_str}. Usando fecha actual.")
            return datetime.now()
        fecha_actual = datetime.now()
        return fecha_transaccion if fecha_actual > fecha_transaccion else fecha_actual
    registros_agregados = 0
    datos_insertar = []
    for _, row in df_nuevos.iterrows():
        fecha_detec = determinar_fecha_detec(row["fecha"])
        if row["facturación"] == "persona":
            rs_value = row["rut"]
        else:
            rs_value = rs_dict.get(row["rut"], None)
        datos_insertar.append({
            "monto": int(row["monto"]),
            "fecha": row["fecha"],
            "rut": row["rut"],
            "facturación": row["facturación"],
            "empresa": row["empresa"],
            "hash": row["hash"],
            "rs": rs_value,
            "enviada": 0,
            "fecha_detec": fecha_detec.strftime("%Y-%m-%d %H:%M:%S")
        })
        print(f"Nuevo hash insertado: {row['hash']} (monto={row['monto']}, fecha={row['fecha']}, rut={row['rut']})")
    if datos_insertar:
        logger.info("Insertando nuevos registros en la base de datos...")
        try:
            response_insert = supabase_client.table('transferencias').insert(datos_insertar).execute()
            insert_data = manejar_respuesta(response_insert, "insertar nuevos registros")
            if insert_data is not None:
                registros_insertados = len(insert_data)
                logger.info(f"Registros insertados exitosamente: {registros_insertados}.")
                registros_agregados += registros_insertados
            else:
                logger.error("No se pudieron insertar los nuevos registros. Verifica la respuesta de Supabase.")
        except Exception as e:
            if "duplicate key value violates unique constraint" in str(e):
                logger.warning("Registros duplicados encontrados. Se omiten registros duplicados.")
            else:
                logger.error(f"Error al interactuar con la base de datos en Supabase: {e}")
    else:
        logger.info("No hay datos para insertar después de asignar 'rs'.")
    if registros_agregados > 0:
        logger.info(f"Se agregaron {registros_agregados} nuevos registros a la base de datos.")
    else:
        logger.info("No se agregaron registros nuevos a la base de datos.")

    # Mostrar hashes duplicados (omitidos)
    df_duplicados = df_resultado[df_resultado['hash'].isin(hashes_existentes)]
    for _, row in df_duplicados.iterrows():
        print(f"Hash duplicado (omitido): {row['hash']} (monto={row['monto']}, fecha={row['fecha']}, rut={row['rut']})")

if __name__ == "__main__":
    try:
        logger.info("Iniciando procesamiento de datos de Santander...")
        # Silenciar logs de httpx, httpcore y supabase a WARNING o superior
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("supabase").setLevel(logging.WARNING)
        df_resultado = SANTANDER()
        if df_resultado is not None:
            BASE_DE_DATOS(df_resultado, supabase)
        logger.info("Procesamiento completado exitosamente.")
    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")
        sys.exit(0)
