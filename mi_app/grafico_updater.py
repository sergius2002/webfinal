import time
import logging
from mi_app.blueprints.utilidades import actualizar_datos

logging.basicConfig(level=logging.INFO)

while True:
    try:
        actualizar_datos()
        logging.info("Datos del gráfico actualizados.")
    except Exception as e:
        logging.error(f"Error al actualizar datos del gráfico: {e}")
    time.sleep(3)  # Espera 60 segundos entre actualizaciones 