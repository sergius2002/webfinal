#!/usr/bin/env python3
"""
Script para sincronizar datos de Binance P2P con Supabase
Ejecutar como Always Task en PythonAnywhere
"""

import os
import sys
import time
import logging
import warnings
from datetime import datetime, timedelta
import pytz
from pathlib import Path

# Suprime los avisos FutureWarning
warnings.filterwarnings("ignore", category=FutureWarning)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/sacristobalspa/webfinal/mi_app/binance_updater.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Reducir mensajes de módulos externos
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("postgrest").setLevel(logging.WARNING)

# Agregar el directorio del proyecto al path
project_dir = '/home/sacristobalspa/webfinal'
sys.path.insert(0, project_dir)

# Configurar zona horaria
os.environ['TZ'] = 'America/Santiago'
time.tzset()
local_tz = pytz.timezone('America/Santiago')

def ahora_ajustada():
    """Retorna la hora local ajustada manualmente -2 horas"""
    return datetime.now(local_tz) - timedelta(hours=2)

# Cargar variables de entorno desde .env
def cargar_variables_entorno():
    """Carga las variables de entorno desde el archivo .env"""
    try:
        env_file = Path(project_dir) / '.env'
        if env_file.exists():
            logging.info(f"📁 Cargando variables de entorno desde: {env_file}")
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
            logging.info("✅ Variables de entorno cargadas correctamente")
        else:
            logging.warning(f"⚠️ Archivo .env no encontrado en: {env_file}")
    except Exception as e:
        logging.error(f"❌ Error al cargar variables de entorno: {e}")

# Cargar variables de entorno antes de importar módulos
cargar_variables_entorno()

def ejecutar_escaneo_binance(fecha_escaneo=None):
    """Función principal para escanear datos de Binance"""
    try:
        # Importar aquí para evitar problemas de path
        from binance.client import Client
        import pandas as pd
        from supabase import create_client
        from postgrest.exceptions import APIError
        
        # Configuración de Binance (credenciales de pruebas)
        api_key = 'Ds4W6XojH4dvM8eCre4U5rVBZpn03e8wM3POSOHHuDajdL33Cjg99JbLQ62n4Uti'
        api_secret = 'ljnha3p0yTg5tKpWm41sZMAH79LOsuwSiL7he6lU9ovUEM0D4e1AaeYkT1TFWo2A'
        client = Client(api_key, api_secret)

        # Configuración de Supabase (credenciales de pruebas)
        supabase_url = "https://tmimwpzxmtezopieqzcl.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho"
        supabase = create_client(supabase_url, supabase_key)

        # Si no se proporciona una fecha, se usa la fecha actual (en zona local)
        if fecha_escaneo is None:
            fecha_escaneo = ahora_ajustada().strftime("%Y-%m-%d")
        fecha_escaneo_dt = datetime.strptime(fecha_escaneo, "%Y-%m-%d")

        def llamada_binance():
            ad_params = {"asset": 'USDT'}
            try:
                result = client.get_c2c_trade_history(**ad_params)
                logging.debug(f"Resultado completo de Binance: {result}")

                data = result.get('data', [])
                if isinstance(data, dict):
                    lengths = [len(v) for v in data.values() if isinstance(v, list)]
                    if lengths and len(set(lengths)) != 1:
                        logging.error("Las listas en result['data'] tienen longitudes diferentes.")
                        return pd.DataFrame()
                    df = pd.DataFrame(data)
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    logging.error("El formato de result['data'] no es ni lista ni diccionario.")
                    return pd.DataFrame()

                # Verificar si la columna 'orderNumber' existe
                if 'orderNumber' in df.columns:
                    logging.info("La columna 'orderNumber' está presente y se utilizará como identificador único.")
                else:
                    if 'tradeType' in df.columns and 'createTime' in df.columns:
                        df['orderNumber'] = df.apply(lambda row: f"{row['tradeType']}_{row['createTime']}", axis=1)
                        logging.info("La columna 'orderNumber' no estaba presente. Se ha generado un identificador único.")
                    else:
                        logging.error("Faltan columnas necesarias para generar 'orderNumber'.")
                        return pd.DataFrame()

                # Convertir 'createTime' a datetime
                if 'createTime' in df.columns:
                    df['createTime'] = pd.to_datetime(df['createTime'], unit='ms', errors='coerce', utc=True)
                    df['createTime'] = df['createTime'].dt.tz_convert('America/Santiago')
                    df['createTime'] = df['createTime'].dt.floor('s')
                else:
                    logging.error("La columna 'createTime' no existe en los datos.")
                    return pd.DataFrame()

                # Definir las columnas que se convertirán a float
                cols_float = ['amount', 'totalPrice', 'unitPrice', 'commission', 'takerCommission']
                for col in cols_float:
                    if col not in df.columns:
                        df[col] = 0.0
                df[cols_float] = df[cols_float].apply(pd.to_numeric, errors='coerce')

                # Seleccionar las columnas de interés
                columnas = ['orderNumber', 'tradeType', 'asset', 'fiat', 'amount', 'totalPrice',
                            'unitPrice', 'commission', 'takerCommission', 'orderStatus',
                            'createTime', 'payMethodName']
                columnas_existentes = [col for col in columnas if col in df.columns]
                df = df[columnas_existentes]

                # Filtrar registros descartando aquellos con estados no válidos
                if 'orderStatus' in df.columns:
                    df = df[df['orderStatus'] == 'COMPLETED']
                    logging.info(f"Filtrado de transacciones: solo se aceptan transacciones COMPLETED")

                # Filtrar registros por fecha
                df = df[df['createTime'].dt.date == fecha_escaneo_dt.date()]

                # Renombrar métodos de pago
                if 'payMethodName' in df.columns:
                    df['payMethodName'] = df['payMethodName'].replace('SpecificBank', 'Venezuela')
                    df['payMethodName'] = df['payMethodName'].replace('BANK', 'Venezuela')

                # Ajustar la comisión
                if 'takerCommission' in df.columns and 'commission' in df.columns:
                    df['commission'] = df.apply(
                        lambda row: row['takerCommission'] if pd.notnull(row['takerCommission']) and row['takerCommission'] != 0 else row['commission'], axis=1)
                    df = df.drop(columns=['takerCommission'])

                logging.info("Datos procesados correctamente desde Binance.")
                return df
            except Exception as e:
                logging.error(f"Error en llamada_binance: {e}")
                return pd.DataFrame()

        def verificar_y_upsert(data, supabase):
            try:
                batch_size = 50
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    # Verificar si ya existen los datos antes de hacer el upsert
                    existing_data = supabase.table('compras').select('*').in_('ordernumber',
                                                                              [item['ordernumber'] for item in batch]).execute()
                    existing_order_numbers = [item['ordernumber'] for item in existing_data.data]
                    records_to_upsert = [item for item in batch if item['ordernumber'] not in existing_order_numbers]
                    if records_to_upsert:
                        logging.info(f"Realizando upsert de {len(records_to_upsert)} registros.")
                        supabase.table('compras').upsert(records_to_upsert, on_conflict='ordernumber').execute()
                    else:
                        logging.info("No hay registros nuevos o actualizados.")
            except Exception as e:
                logging.error(f"Error al realizar el upsert en Supabase: {e}")

        # Actualizar la fecha de escaneo si ha cambiado el día
        current_date_str = ahora_ajustada().strftime("%Y-%m-%d")
        if current_date_str != fecha_escaneo:
            fecha_escaneo = current_date_str
            fecha_escaneo_dt = datetime.strptime(fecha_escaneo, "%Y-%m-%d")
            logging.info(f"Se actualizó la fecha de escaneo a {fecha_escaneo}")

        df_completo = llamada_binance()
        if df_completo.empty:
            logging.info("No se obtuvieron datos nuevos desde Binance.")
            return False
        else:
            # Convertir 'createTime' a cadena con el formato "YYYY-MM-DD HH:MM:SS"
            df_completo['createTime'] = df_completo['createTime'].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notnull(x) else None
            )
            # Convertir los nombres de las columnas a minúsculas
            df_completo.columns = [col.lower() for col in df_completo.columns]
            # Convertir el DataFrame a una lista de diccionarios para la inserción en Supabase
            records = df_completo.to_dict(orient='records')
            try:
                verificar_y_upsert(records, supabase)
                return True
            except APIError as api_err:
                logging.error(f"APIError al realizar el upsert en Supabase: {api_err}")
                return False
            except Exception as e:
                logging.error(f"Error al realizar el upsert en Supabase: {e}")
                return False
                
    except Exception as e:
        logging.error(f"❌ Error crítico en ejecutar_escaneo_binance: {e}")
        return False

def main():
    """Función principal del script"""
    logging.info("🚀 Iniciando script de sincronización de datos de Binance")
    
    # Contador de actualizaciones exitosas y fallidas
    exitosas = 0
    fallidas = 0
    
    while True:
        try:
            # Obtener hora actual
            ahora = ahora_ajustada()
            logging.info(f"⏰ Hora actual: {ahora.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Ejecutar escaneo de Binance
            if ejecutar_escaneo_binance():
                exitosas += 1
                logging.info("✅ Datos de Binance sincronizados correctamente")
            else:
                fallidas += 1
                logging.warning("⚠️ No se pudieron sincronizar datos de Binance")
            
            # Mostrar estadísticas cada 10 actualizaciones
            if (exitosas + fallidas) % 10 == 0:
                logging.info(f"📊 Estadísticas: {exitosas} exitosas, {fallidas} fallidas")
            
            # Esperar 1 minuto (60 segundos)
            logging.info("⏳ Esperando 1 minuto hasta la próxima sincronización...")
            time.sleep(60)
            
        except KeyboardInterrupt:
            logging.info("🛑 Script interrumpido por el usuario")
            break
        except Exception as e:
            logging.error(f"💥 Error crítico en el script: {e}")
            time.sleep(60)  # Esperar 1 minuto antes de reintentar

if __name__ == "__main__":
    main() 