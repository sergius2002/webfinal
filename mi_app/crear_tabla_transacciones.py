#!/usr/bin/env python3
"""
Script para crear la tabla transacciones_flujo en Supabase
"""

import os
import sys
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')

def crear_tabla_transacciones():
    """Crea la tabla transacciones_flujo en Supabase"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔧 Creando tabla transacciones_flujo...")
        
        # Verificar si la tabla ya existe
        try:
            result = supabase.table("transacciones_flujo").select("id").limit(1).execute()
            print("✅ La tabla transacciones_flujo ya existe")
            return True
        except Exception as e:
            print(f"📋 La tabla no existe, necesitas crearla manualmente en Supabase SQL Editor")
            print("\n📄 Ejecuta este SQL en Supabase:")
            print("=" * 80)
            
            # Leer el archivo SQL
            try:
                with open('CREATE_TRANSACCIONES_FLUJO.sql', 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                print(sql_content)
            except FileNotFoundError:
                print("""
-- Tabla para almacenar transacciones individuales del flujo de capital
CREATE TABLE IF NOT EXISTS transacciones_flujo (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('ENTRADA', 'SALIDA')),
    monto NUMERIC(15,2) NOT NULL,
    descripcion TEXT NOT NULL,
    categoria VARCHAR(50),
    capital_anterior NUMERIC(15,2) NOT NULL,
    capital_posterior NUMERIC(15,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_fecha ON transacciones_flujo(fecha);
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_tipo ON transacciones_flujo(tipo);
CREATE INDEX IF NOT EXISTS idx_transacciones_flujo_categoria ON transacciones_flujo(categoria);

-- Función para actualizar el timestamp de updated_at
CREATE OR REPLACE FUNCTION update_transacciones_flujo_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
CREATE TRIGGER update_transacciones_flujo_updated_at 
    BEFORE UPDATE ON transacciones_flujo 
    FOR EACH ROW 
    EXECUTE FUNCTION update_transacciones_flujo_updated_at();
""")
            
            print("=" * 80)
            print("\n📋 Pasos para crear la tabla:")
            print("1. Ve a Supabase Dashboard")
            print("2. Abre SQL Editor")
            print("3. Copia y pega el SQL de arriba")
            print("4. Ejecuta el script")
            print("5. Vuelve a ejecutar este script para verificar")
            
            return False
        
    except Exception as e:
        print(f"❌ Error al verificar tabla: {e}")
        return False

def migrar_datos_existentes():
    """Migra datos existentes del flujo_capital a transacciones_flujo"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("\n🔄 Migrando datos existentes...")
        
        # Verificar si ya hay transacciones
        transacciones_existentes = supabase.table("transacciones_flujo").select("id").limit(1).execute().data
        if transacciones_existentes:
            print("⚠️ Ya existen transacciones, saltando migración")
            return True
        
        # Obtener datos del flujo_capital
        flujo_data = supabase.table("flujo_capital").select("*").order("fecha").execute().data
        
        if not flujo_data:
            print("ℹ️ No hay datos de flujo_capital para migrar")
            return True
        
        print(f"📊 Migrando {len(flujo_data)} registros...")
        
        for item in flujo_data:
            fecha = item['fecha']
            ganancias = float(item.get('ganancias', 0))
            costo_gastos = float(item.get('costo_gastos', 0))
            gastos_manuales = float(item.get('gastos_manuales', 0))
            capital_inicial = float(item.get('capital_inicial', 0))
            capital_final = float(item.get('capital_final', 0))
            
            # Agregar ganancias como entrada
            if ganancias > 0:
                agregar_transaccion_flujo(fecha, 'ENTRADA', ganancias, f"Ganancias del {fecha}", 'GANANCIAS')
            
            # Agregar gastos Venezuela como salida
            if costo_gastos > 0:
                agregar_transaccion_flujo(fecha, 'SALIDA', costo_gastos, "Gastos Venezuela", 'GASTOS_VENEZUELA')
            
            # Agregar gastos Chile como salida
            if gastos_manuales > 0:
                agregar_transaccion_flujo(fecha, 'SALIDA', gastos_manuales, "Gastos Chile", 'GASTOS_CHILE')
        
        print("✅ Migración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en migración: {e}")
        return False

def agregar_transaccion_flujo(fecha, tipo, monto, descripcion, categoria):
    """Función auxiliar para agregar transacciones"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Obtener el capital actual para esa fecha
        capital_actual = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha).execute().data
        
        if capital_actual:
            capital_anterior = float(capital_actual[0]['capital_final'])
        else:
            # Si no existe, usar el capital del día anterior o 32M por defecto
            from datetime import datetime, timedelta
            fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
            fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
            capital_ayer = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
            capital_anterior = float(capital_ayer[0]['capital_final']) if capital_ayer else 32000000
        
        # Calcular capital posterior
        if tipo == 'ENTRADA':
            capital_posterior = capital_anterior + monto
        else:  # SALIDA
            capital_posterior = capital_anterior - monto
        
        # Insertar transacción
        transaccion_data = {
            'fecha': fecha,
            'tipo': tipo,
            'monto': monto,
            'descripcion': descripcion,
            'categoria': categoria,
            'capital_anterior': capital_anterior,
            'capital_posterior': capital_posterior
        }
        
        response = supabase.table("transacciones_flujo").insert(transaccion_data).execute()
        
        if response.data:
            print(f"✅ Transacción migrada: {tipo} ${monto:,.0f} - {descripcion}")
            return True
        else:
            print(f"❌ Error al migrar transacción")
            return False
            
    except Exception as e:
        print(f"❌ Error al migrar transacción: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando creación de tabla transacciones_flujo...")
    
    # Crear tabla
    if crear_tabla_transacciones():
        # Migrar datos existentes
        migrar_datos_existentes()
    else:
        print("\n📋 Después de crear la tabla en Supabase, ejecuta este script nuevamente para migrar los datos") 