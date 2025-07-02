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
logger.setLevel(logging.DEBUG)  # DEBUG para archivo, pero solo INFO en consola

# Crear un formateador
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

# Handler para el archivo de log
file_handler = logging.FileHandler('flujo_san_cristobal.log')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Handler para la consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Solo INFO o superior en consola
console_handler.setFormatter(formatter)

# Limpiar handlers previos y añadir los nuevos
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# --------------------------------------------------------------------------------
# Cargar variables de entorno directamente en el código
# --------------------------------------------------------------------------------
SUPABASE_URL = "https://tmimwpzxmtezopieqzcl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"
CARPETA_ARCHIVOS = "Santander_archivos"
# En este caso, no se procesan montos negativos, por lo que no se permite su procesamiento.

logger.info("Inicio del script.")

# Obtener el directorio del script actual
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta completa a la carpeta de archivos (ahora en uploads)
CARPETA_ARCHIVOS = os.path.join(SCRIPT_DIR, "uploads", "transferencias", "uploads")

# Después de cargar las variables de entorno
# logger.info(f"Buscando archivos en la carpeta: {CARPETA_ARCHIVOS}")

# Verificar si la carpeta existe
if not os.path.exists(CARPETA_ARCHIVOS):
    # logger.error(f"La carpeta {CARPETA_ARCHIVOS} no existe")
    sys.exit(0)

# Listar archivos en la carpeta para debug
# logger.info("Archivos encontrados en la carpeta:")
# for archivo in os.listdir(CARPETA_ARCHIVOS):
#     logger.info(f"- {archivo}")

# --------------------------------------------------------------------------------
# Inicializar el cliente de Supabase
# --------------------------------------------------------------------------------
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # logger.info("Cliente de Supabase inicializado correctamente.")
except Exception as e:
    # logger.error(f"Error al inicializar el cliente de Supabase: {e}")
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
    """
    Normaliza la fecha al formato 'YYYY-MM-DD'.
    """
    try:
        dt = pd.to_datetime(fecha_str, errors='coerce', dayfirst=True)
        if pd.isna(dt):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Error al normalizar fecha '{fecha_str}': {e}")
        return None

def normalizar_monto(valor):
    """
    Normaliza el monto asegurando que sea un entero positivo.
    Retorna el valor como entero o None si no es válido.
    """
    try:
        num = float(valor)
        if num.is_integer() and num > 0:
            return int(num)
        else:
            raise ValueError(f"Valor de monto inválido: {valor}")
    except ValueError as e:
        # logger.error(f"Error al normalizar monto '{valor}': {e}")
        return None

def normalizar_rut(rut_str):
    """
    Normaliza el RUT eliminando puntos y convirtiéndolo a mayúsculas.
    """
    try:
        rut = str(rut_str).replace(".", "").upper().strip()
        return rut
    except Exception as e:
        logger.error(f"Error al normalizar RUT '{rut_str}': {e}")
        return rut_str

# --------------------------------------------------------------------------------
# Función para determinar si es persona o empresa
# --------------------------------------------------------------------------------
def determinar_facturacion(rut_str):
    """
    Determina si un RUT corresponde a 'persona' o 'empresa' basándose en su parte numérica.
    Ejemplo: si el número del RUT < 50000000 -> persona, si no -> empresa.
    Ajusta la lógica según tu regla real.
    """
    try:
        partes = rut_str.split("-")
        numero = partes[0] if len(partes) > 0 else rut_str
        rut_int = int(numero)
        if rut_int < 50000000:
            return "persona"
        else:
            return "empresa"
    except Exception as e:
        # logger.warning(f"No se pudo determinar facturación para el RUT '{rut_str}'. Error: {e}")
        return "persona"

# --------------------------------------------------------------------------------
# Función para calcular el hash único
# --------------------------------------------------------------------------------
def calcular_hash(row):
    """
    Genera un hash MD5 a partir de (monto, fecha, rut) normalizados.
    Se registra en DEBUG la cadena base para confirmar que sea la esperada.
    """
    data = f"{row['monto']}_{row['fecha']}_{row['rut']}"
    # logger.debug(f"Calculando hash para: {data}")
    return hashlib.md5(data.encode('utf-8')).hexdigest()

# --------------------------------------------------------------------------------
# FUNCIÓN: manejar_respuesta
# --------------------------------------------------------------------------------
def manejar_respuesta(response, contexto):
    """
    Maneja la respuesta de Supabase.
    Si hay un error, lo registra y retorna None.
    Si todo está bien, retorna los datos.
    """
    # logger.debug(f"Respuesta de Supabase en {contexto}: {response}")  # Comentado para evitar mostrar todos los hashes
    # logger.debug(f"Atributos de la respuesta: {dir(response)}")
    if hasattr(response, 'error') and response.error:
        logger.error(f"Error en {contexto}: {response.error}")
        return None
    elif hasattr(response, 'status_code') and response.status_code >= 400:
        logger.error(f"Error en {contexto}: {response.status_message}")
        return None
    return response.data

# --------------------------------------------------------------------------------
# FUNCIÓN: get_all_hashes
# --------------------------------------------------------------------------------
def get_all_hashes(supabase_client, batch_size=1000):
    """
    Recupera todos los hashes existentes en la tabla 'transferencias' paginando la consulta.
    """
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
    # logger.info(f"Se recuperaron {len(all_hashes)} hashes en total de la base de datos.")
    return set(item['hash'] for item in all_hashes if item.get('hash') is not None)

# --------------------------------------------------------------------------------
# FUNCIÓN: SANTANDER
# --------------------------------------------------------------------------------
def SANTANDER():
    # logger.info("Entrando en la función SANTANDER().")
    dataframes = []
    archivos_encontrados = 0

    # Definir la expresión regular para extraer el RUT
    rut_regex = re.compile(r'\b0*([1-9]\d{6,7})[-.]?([0-9Kk])\b')

    for archivo in os.listdir(CARPETA_ARCHIVOS):
        # Evitar archivos temporales o repetidos
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
                
                # Eliminar o comentar logs de depuración masiva
                # logger.info(f"\nContenido del archivo {archivo}:")
                # logger.info("\nPrimeras 5 filas del archivo original:")
                # logger.info(df.head().to_string())
                
                columnas_relevantes = df[["MONTO", "DESCRIPCIÓN MOVIMIENTO", "FECHA"]].copy()
                
                # Eliminar o comentar logs de depuración masiva
                # logger.info("\nColumnas relevantes seleccionadas:")
                # logger.info(columnas_relevantes.head().to_string())
                
                # Eliminar o comentar logs de depuración masiva
                # logger.info("\nDatos procesados (después de normalización):")
                # logger.info(columnas_relevantes.head().to_string())

                # Normalizar 'monto'
                columnas_relevantes["MONTO"] = columnas_relevantes["MONTO"].apply(normalizar_monto)
                # Eliminar filas donde la normalización de monto falló
                columnas_relevantes = columnas_relevantes[columnas_relevantes["MONTO"].notna()]

                # Asignar la cadena (para identificar de dónde proviene si hay múltiples empresas)
                columnas_relevantes["CADENA"] = cadena_encontrada

                # Extraer RUT de la descripción usando regex
                def extraer_rut(descripcion):
                    # Eliminar puntos para normalizar el formato del RUT
                    descripcion_limpia = descripcion.replace('.', '')
                    # logger.info(f"Buscando RUT en descripción: {descripcion_limpia}")
                    matches = rut_regex.findall(descripcion_limpia)
                    if matches:
                        numero, verificador = matches[0]
                        rut_completo = f"{numero}-{verificador.upper()}"
                        # logger.info(f"RUT encontrado: {rut_completo}")
                        return rut_completo
                    else:
                        # logger.warning(f"RUT no encontrado en la descripción: {descripcion}")
                        return None

                columnas_relevantes["rut"] = columnas_relevantes["DESCRIPCIÓN MOVIMIENTO"].apply(extraer_rut)
                # Eliminar filas donde el RUT no fue encontrado
                columnas_relevantes = columnas_relevantes.dropna(subset=["rut"])

                # Normalizar RUT
                columnas_relevantes["rut"] = columnas_relevantes["rut"].apply(normalizar_rut)

                # Eliminar filas con RUTs a eliminar
                columnas_relevantes = columnas_relevantes[~columnas_relevantes['rut'].isin(RUTS_A_ELIMINAR)]
                if columnas_relevantes.empty:
                    logger.info(
                        f"Todos los registros en el archivo {archivo} están en la lista de RUTs a eliminar o no hay datos válidos. Omitiendo archivo.")
                    archivos_procesados.add(archivo)
                    continue

                # Eliminar o comentar logs de depuración masiva
                # logger.info(f"Primeras fechas originales en {archivo}:")
                # logger.info(columnas_relevantes["FECHA"].head().to_string())

                # Normalizar fechas a 'YYYY-MM-DD'
                columnas_relevantes["fecha"] = columnas_relevantes["FECHA"].apply(normalizar_fecha)

                # Eliminar registros con fecha inválida
                columnas_relevantes = columnas_relevantes[columnas_relevantes["fecha"].notna()]

                # Eliminar o comentar logs de depuración masiva
                # logger.info(f"Primeras fechas procesadas en {archivo}:")
                # logger.info(columnas_relevantes["fecha"].head().to_string())

                # Renombrar columnas para estandarizar
                columnas_relevantes = columnas_relevantes.rename(columns={"MONTO": "monto"})

                # Determinar si es empresa o persona
                columnas_relevantes["facturación"] = columnas_relevantes["rut"].apply(determinar_facturacion)

                # Asignar la empresa basada en la cadena
                empresa = MAPEO_EMPRESAS.get(cadena_encontrada, "Desconocida")
                columnas_relevantes["empresa"] = empresa

                # Calcular el hash con la fecha ya normalizada
                columnas_relevantes["hash"] = columnas_relevantes.apply(calcular_hash, axis=1)

                # Añadir la columna 'rs' con valores nulos inicialmente
                columnas_relevantes["rs"] = None

                # Reorganizar columnas para mayor claridad
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
        # logger.info("Procesamiento completo. Archivos procesados.")
        return pd.concat(dataframes, ignore_index=True)
    else:
        logger.info("No se procesaron datos en SANTANDER.")
        return None

# --------------------------------------------------------------------------------
# FUNCIÓN: BASE_DE_DATOS
# --------------------------------------------------------------------------------
def BASE_DE_DATOS(df_resultado, supabase_client):
    """
    Inserta los datos procesados en la tabla 'transferencias' en Supabase,
    asegurando que solo se agreguen nuevos registros basados en el 'hash'.
    No se actualizan registros existentes.
    """
    if df_resultado is None or df_resultado.empty:
        logger.info("No se encontraron datos nuevos para agregar a la base de datos.")
        return

    logger.info(f"Cantidad de registros a revisar: {df_resultado.shape[0]}")
    logger.info("Primeras filas a insertar en la base de datos:")
    logger.info(df_resultado.head().to_string())

    # Eliminar duplicados basados en 'hash' dentro del propio DataFrame
    duplicados = df_resultado[df_resultado.duplicated(subset=['hash'], keep=False)]
    if not duplicados.empty:
        logger.warning(
            "Existen filas con 'hash' duplicados en el DataFrame a insertar. Mostrando duplicados (columnas: rut, hash y fecha):")
        logger.warning(duplicados[['rut', 'hash', 'fecha']].to_string())
        df_resultado = df_resultado.drop_duplicates(subset=['hash'], keep='first')
        logger.info("Duplicados eliminados del DataFrame a insertar (manteniendo la primera ocurrencia).")

    # --------------------------------------------------------------------------------
    # Recuperar todos los hashes existentes en la base de datos mediante paginación
    # --------------------------------------------------------------------------------
    try:
        logger.info("Recuperando hashes existentes en la base de datos (paginado)...")
        hashes_existentes = get_all_hashes(supabase_client, batch_size=1000)
        logger.debug(f"Hashes existentes: {hashes_existentes}")
    except Exception as e:
        logger.error(f"Error al interactuar con Supabase al recuperar hashes existentes: {e}")
        hashes_existentes = set()

    # Depuración: Mostrar los hashes del DataFrame antes de filtrar
    logger.debug(f"Hashes en DataFrame a insertar: {df_resultado['hash'].tolist()}")

    # Filtrar el DataFrame para excluir registros con hashes existentes
    df_nuevos = df_resultado[~df_resultado['hash'].isin(hashes_existentes)]
    logger.info(f"Registros nuevos después de filtrar por hash: {df_nuevos.shape[0]}")

    if df_nuevos.empty:
        logger.info("No hay registros nuevos para insertar en la base de datos.")
        return
    else:
        logger.info(f"Se insertarán {df_nuevos.shape[0]} registros nuevos en la base de datos.")

    # Registro de la cadena base y hash para cada registro nuevo (para depuración)
    for _, row in df_nuevos.iterrows():
        data_str = f"{row['monto']}_{row['fecha']}_{row['rut']}"
        logger.debug(f"Registro a insertar: {data_str} -> Hash: {row['hash']}")

    # --------------------------------------------------------------------------------
    # Preparar 'rs' en bloque para las empresas
    # --------------------------------------------------------------------------------
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

    # Función auxiliar para determinar fecha_detec
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
        logger.info("Primeras filas con 'rs' asignado a insertar:")
        logger.info(pd.DataFrame(datos_insertar).head().to_string())
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

# --------------------------------------------------------------------------------
# Bloque principal de ejecución
# --------------------------------------------------------------------------------
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
