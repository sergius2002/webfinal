#!/bin/bash

# Script para iniciar el monitor de archivos bancarios en segundo plano

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Archivo de log para el monitor
LOG_FILE="$PROJECT_DIR/monitor_archivos.log"

# Archivo PID para controlar el proceso
PID_FILE="$PROJECT_DIR/monitor_archivos.pid"

# Función para verificar si el monitor ya está ejecutándose
check_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "El monitor ya está ejecutándose con PID: $PID"
            return 0
        else
            echo "PID file existe pero el proceso no está ejecutándose. Limpiando..."
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Función para detener el monitor
stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "Deteniendo monitor con PID: $PID"
            kill $PID
            rm -f "$PID_FILE"
            echo "Monitor detenido."
        else
            echo "Monitor no está ejecutándose."
            rm -f "$PID_FILE"
        fi
    else
        echo "No se encontró archivo PID. El monitor no está ejecutándose."
    fi
}

# Función para mostrar el estado
status_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo "✅ Monitor ejecutándose con PID: $PID"
            echo "📁 Directorio monitoreado: $PROJECT_DIR/uploads/transferencias/uploads"
            echo "📋 Log file: $LOG_FILE"
        else
            echo "❌ PID file existe pero el proceso no está ejecutándose"
            rm -f "$PID_FILE"
        fi
    else
        echo "❌ Monitor no está ejecutándose"
    fi
}

# Función para mostrar los logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "=== Últimas 20 líneas del log ==="
        tail -n 20 "$LOG_FILE"
    else
        echo "No se encontró archivo de log."
    fi
}

# Procesar argumentos
case "$1" in
    start)
        if check_monitor; then
            exit 1
        fi
        
        echo "Iniciando monitor de archivos bancarios..."
        cd "$PROJECT_DIR"
        
        # Activar entorno virtual si existe
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        # Iniciar el monitor en segundo plano
        nohup python3 monitor_archivos_bancarios.py > "$LOG_FILE" 2>&1 &
        MONITOR_PID=$!
        
        # Guardar PID
        echo $MONITOR_PID > "$PID_FILE"
        
        echo "✅ Monitor iniciado con PID: $MONITOR_PID"
        echo "📁 Monitoreando: $PROJECT_DIR/uploads/transferencias/uploads"
        echo "📋 Log: $LOG_FILE"
        ;;
        
    stop)
        stop_monitor
        ;;
        
    restart)
        echo "Reiniciando monitor..."
        stop_monitor
        sleep 2
        $0 start
        ;;
        
    status)
        status_monitor
        ;;
        
    logs)
        show_logs
        ;;
        
    *)
        echo "Uso: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Comandos:"
        echo "  start   - Iniciar el monitor de archivos bancarios"
        echo "  stop    - Detener el monitor"
        echo "  restart - Reiniciar el monitor"
        echo "  status  - Mostrar estado del monitor"
        echo "  logs    - Mostrar últimas líneas del log"
        echo ""
        echo "El monitor detectará automáticamente archivos XLSX de BCI y Santander"
        echo "y los procesará ejecutando los scripts correspondientes."
        exit 1
        ;;
esac 