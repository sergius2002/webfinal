#!/usr/bin/env python3
"""
Script para crear la tabla flujo_capital en Supabase
"""

import os
import sys
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')

def crear_tabla_flujo_capital():
    """Crea la tabla flujo_capital en Supabase"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔗 Conectando a Supabase...")
        
        # SQL para crear la tabla
        sql_crear_tabla = """
        -- Tabla para almacenar el flujo de capital día a día
        CREATE TABLE IF NOT EXISTS flujo_capital (
            id SERIAL PRIMARY KEY,
            fecha DATE NOT NULL UNIQUE,
            capital_inicial NUMERIC(15,2) NOT NULL DEFAULT 0,
            ganancias NUMERIC(15,2) NOT NULL DEFAULT 0,
            costo_gastos NUMERIC(15,2) NOT NULL DEFAULT 0,
            gastos_manuales NUMERIC(15,2) NOT NULL DEFAULT 0,
            capital_final NUMERIC(15,2) NOT NULL DEFAULT 0,
            margen_neto NUMERIC(15,2) NOT NULL DEFAULT 0,
            ponderado_ves_clp NUMERIC(10,5) NOT NULL DEFAULT 0,
            gastos_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
            pago_movil_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
            envios_al_detal_brs NUMERIC(15,2) NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # SQL para crear índices
        sql_indices = """
        -- Crear índices para búsquedas rápidas
        CREATE INDEX IF NOT EXISTS idx_flujo_capital_fecha ON flujo_capital(fecha);
        CREATE INDEX IF NOT EXISTS idx_flujo_capital_capital_final ON flujo_capital(capital_final);
        """
        
        # SQL para insertar capital inicial
        sql_capital_inicial = """
        -- Insertar capital inicial para el 16-07-2025
        INSERT INTO flujo_capital (fecha, capital_inicial, capital_final) 
        VALUES ('2025-07-16', 32000000, 32000000)
        ON CONFLICT (fecha) DO NOTHING;
        """
        
        # SQL para función y trigger
        sql_funcion_trigger = """
        -- Función para actualizar el timestamp de updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        -- Trigger para actualizar updated_at automáticamente
        CREATE TRIGGER update_flujo_capital_updated_at 
            BEFORE UPDATE ON flujo_capital 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        print("📋 Creando tabla flujo_capital...")
        result = supabase.rpc('exec_sql', {'sql': sql_crear_tabla}).execute()
        print("✅ Tabla creada exitosamente")
        
        print("📊 Creando índices...")
        result = supabase.rpc('exec_sql', {'sql': sql_indices}).execute()
        print("✅ Índices creados exitosamente")
        
        print("💰 Insertando capital inicial...")
        result = supabase.rpc('exec_sql', {'sql': sql_capital_inicial}).execute()
        print("✅ Capital inicial insertado exitosamente")
        
        print("⚙️ Creando función y trigger...")
        result = supabase.rpc('exec_sql', {'sql': sql_funcion_trigger}).execute()
        print("✅ Función y trigger creados exitosamente")
        
        print("\n🎉 ¡Tabla flujo_capital creada exitosamente!")
        print("📅 Capital inicial configurado para 2025-07-16: $32,000,000")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al crear la tabla: {e}")
        return False

if __name__ == "__main__":
    crear_tabla_flujo_capital() 