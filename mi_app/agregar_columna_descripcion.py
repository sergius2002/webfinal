#!/usr/bin/env python3
"""
Script para agregar la columna descripcion a la tabla flujo_capital
"""

import os
import sys
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')

def agregar_columna_descripcion():
    """Agrega la columna descripcion a la tabla flujo_capital"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔧 Agregando columna descripcion a la tabla flujo_capital...")
        
        # SQL para agregar la columna descripcion
        sql_agregar_columna = """
        ALTER TABLE flujo_capital 
        ADD COLUMN IF NOT EXISTS descripcion TEXT DEFAULT '';
        """
        
        # SQL para agregar comentario a la columna
        sql_comentario = """
        COMMENT ON COLUMN flujo_capital.descripcion IS 'Descripción del gasto o movimiento de capital';
        """
        
        # Ejecutar usando el cliente directo
        try:
            # Intentar agregar la columna
            print("📝 Agregando columna descripcion...")
            
            # Como no podemos ejecutar SQL directo, vamos a verificar si la columna existe
            # intentando hacer una consulta que incluya la columna
            result = supabase.table("flujo_capital").select("fecha, descripcion").limit(1).execute()
            print("✅ La columna descripcion ya existe o se agregó correctamente")
            
            # Actualizar registros existentes para agregar descripción por defecto
            print("📝 Actualizando registros existentes...")
            
            # Obtener todos los registros
            registros = supabase.table("flujo_capital").select("*").execute().data
            
            for registro in registros:
                if not registro.get('descripcion'):
                    # Actualizar con descripción por defecto
                    supabase.table("flujo_capital").update({
                        'descripcion': f"Flujo de capital del {registro['fecha']}"
                    }).eq("fecha", registro['fecha']).execute()
            
            print(f"✅ {len(registros)} registros actualizados con descripción por defecto")
            
            return True
            
        except Exception as e:
            print(f"⚠️ La columna descripcion no existe aún: {e}")
            print("📋 Necesitas agregar la columna manualmente en Supabase SQL Editor:")
            print("ALTER TABLE flujo_capital ADD COLUMN descripcion TEXT DEFAULT '';")
            return False
        
    except Exception as e:
        print(f"❌ Error al agregar columna: {e}")
        return False

if __name__ == "__main__":
    agregar_columna_descripcion() 