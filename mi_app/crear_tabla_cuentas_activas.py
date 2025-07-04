#!/usr/bin/env python3
"""
Script para crear la tabla cuentas_activas en Supabase
"""

import os
import sys
from supabase import create_client, Client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')

def crear_tabla_cuentas_activas():
    """Crea la tabla cuentas_activas en Supabase"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("🔗 Conectando a Supabase...")
        
        # SQL para crear la tabla
        sql_crear_tabla = """
        -- Tabla para almacenar cuentas activas del sistema
        CREATE TABLE IF NOT EXISTS cuentas_activas (
            id SERIAL PRIMARY KEY,
            banco VARCHAR(100) NOT NULL,
            numero_cuenta BIGINT NOT NULL,
            cedula VARCHAR(20) NOT NULL,
            nombre_titular VARCHAR(200) NOT NULL,
            pais VARCHAR(50) NOT NULL DEFAULT 'Venezuela',
            activa BOOLEAN DEFAULT TRUE,
            usuario_creacion VARCHAR(255),
            usuario_modificacion VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # SQL para crear índices
        sql_indices = """
        -- Crear índices para búsquedas rápidas
        CREATE INDEX IF NOT EXISTS idx_cuentas_activas_banco ON cuentas_activas(banco);
        CREATE INDEX IF NOT EXISTS idx_cuentas_activas_cedula ON cuentas_activas(cedula);
        CREATE INDEX IF NOT EXISTS idx_cuentas_activas_activa ON cuentas_activas(activa);
        """
        
        # SQL para crear trigger
        sql_trigger = """
        -- Trigger para actualizar updated_at automáticamente
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';

        CREATE TRIGGER update_cuentas_activas_updated_at 
            BEFORE UPDATE ON cuentas_activas 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
        """
        
        # SQL para comentarios
        sql_comentarios = """
        -- Comentarios para documentar la tabla
        COMMENT ON TABLE cuentas_activas IS 'Tabla para almacenar las cuentas bancarias activas del sistema';
        COMMENT ON COLUMN cuentas_activas.banco IS 'Nombre del banco (ej: Banesco, Mercantil, Provincial)';
        COMMENT ON COLUMN cuentas_activas.numero_cuenta IS 'Número de cuenta bancaria';
        COMMENT ON COLUMN cuentas_activas.cedula IS 'Cédula de identidad del titular';
        COMMENT ON COLUMN cuentas_activas.nombre_titular IS 'Nombre completo del titular de la cuenta';
        COMMENT ON COLUMN cuentas_activas.pais IS 'País donde está registrada la cuenta';
        COMMENT ON COLUMN cuentas_activas.activa IS 'Indica si la cuenta está activa o no';
        COMMENT ON COLUMN cuentas_activas.usuario_creacion IS 'Email del usuario que creó el registro';
        COMMENT ON COLUMN cuentas_activas.usuario_modificacion IS 'Email del usuario que modificó el registro';
        """
        
        print("📋 Creando tabla cuentas_activas...")
        
        # Ejecutar SQL usando rpc (función personalizada)
        try:
            # Intentar crear la tabla usando una función RPC
            result = supabase.rpc('exec_sql', {'sql_query': sql_crear_tabla}).execute()
            print("✅ Tabla creada exitosamente")
        except Exception as e:
            print(f"⚠️ No se pudo ejecutar SQL directamente: {e}")
            print("💡 Debes ejecutar el SQL manualmente en el panel de Supabase")
            print("\n📝 SQL para ejecutar:")
            print("=" * 50)
            print(sql_crear_tabla)
            print(sql_indices)
            print(sql_trigger)
            print(sql_comentarios)
            print("=" * 50)
            return False
        
        print("🔍 Verificando que la tabla existe...")
        
        # Verificar que la tabla existe intentando hacer una consulta
        try:
            result = supabase.table("cuentas_activas").select("id").limit(1).execute()
            print("✅ Tabla cuentas_activas verificada correctamente")
            
            # Insertar datos de ejemplo
            print("📝 Insertando datos de ejemplo...")
            datos_ejemplo = [
                {
                    "banco": "Banesco",
                    "numero_cuenta": 12345678901234567890,
                    "cedula": "V-12345678",
                    "nombre_titular": "Juan Pérez",
                    "pais": "Venezuela",
                    "activa": True,
                    "usuario_creacion": "admin@example.com"
                },
                {
                    "banco": "Mercantil",
                    "numero_cuenta": 98765432109876543210,
                    "cedula": "V-87654321",
                    "nombre_titular": "María García",
                    "pais": "Venezuela",
                    "activa": True,
                    "usuario_creacion": "admin@example.com"
                },
                {
                    "banco": "Provincial",
                    "numero_cuenta": 11223344556677889900,
                    "cedula": "V-11223344",
                    "nombre_titular": "Carlos López",
                    "pais": "Venezuela",
                    "activa": True,
                    "usuario_creacion": "admin@example.com"
                }
            ]
            
            for dato in datos_ejemplo:
                try:
                    supabase.table("cuentas_activas").insert(dato).execute()
                    print(f"✅ Insertado: {dato['banco']} - {dato['nombre_titular']}")
                except Exception as e:
                    print(f"⚠️ No se pudo insertar {dato['banco']}: {e}")
            
            print("\n🎉 ¡Tabla cuentas_activas creada exitosamente!")
            print("📊 Puedes acceder al módulo desde: /cuentas-activas")
            
        except Exception as e:
            print(f"❌ Error al verificar la tabla: {e}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando creación de tabla cuentas_activas...")
    print("=" * 60)
    
    success = crear_tabla_cuentas_activas()
    
    print("=" * 60)
    if success:
        print("✅ Proceso completado exitosamente")
    else:
        print("❌ Proceso falló")
        print("\n💡 Instrucciones manuales:")
        print("1. Ve al panel de Supabase")
        print("2. Abre el SQL Editor")
        print("3. Ejecuta el contenido del archivo CREATE_CUENTAS_ACTIVAS.sql")
        print("4. Verifica que la tabla se creó correctamente")
    
    print("\n📋 Próximos pasos:")
    print("1. Ejecutar el script de creación de tabla")
    print("2. Reiniciar la aplicación Flask")
    print("3. Acceder al módulo desde el menú de administración") 