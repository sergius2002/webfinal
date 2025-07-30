#!/usr/bin/env python3
"""
Script para verificar si la transferencia específica está en la lista de ids_asignadas
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Configuración de Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def verificar_cache():
    """Verifica si la transferencia específica está en la lista de ids_asignadas"""
    
    transferencia_id = "40b184a5-b535-4ae9-ae09-125e1305243d"
    
    print("🔍 VERIFICANDO CACHÉ DEL BACKEND")
    print("=" * 60)
    
    try:
        # Obtener todos los IDs de transferencias asignadas (igual que el backend)
        ids_asignadas = set()
        offset = 0
        limit = 1000
        while True:
            asignadas_resp = supabase.table('transferencias_pagos').select('transferencia_id').range(offset, offset + limit - 1).execute()
            if not asignadas_resp.data:
                break
            ids_asignadas.update({item['transferencia_id'] for item in asignadas_resp.data})
            if len(asignadas_resp.data) < limit:
                break
            offset += limit
        
        print(f"✅ Total de transferencias asignadas: {len(ids_asignadas)}")
        print(f"🔍 Buscando transferencia ID: {transferencia_id}")
        
        if transferencia_id in ids_asignadas:
            print(f"✅ TRANSFERENCIA ENCONTRADA EN ids_asignadas")
            print(f"   - El backend debería mostrar t.asignado = True")
            print(f"   - El frontend debería mostrar 'Asignado' en lugar de 'Asignar pago'")
        else:
            print(f"❌ TRANSFERENCIA NO ENCONTRADA EN ids_asignadas")
            print(f"   - El backend mostrará t.asignado = False")
            print(f"   - El frontend mostrará 'Asignar pago'")
        
        # Verificar específicamente esta transferencia
        asignacion_especifica = supabase.table("transferencias_pagos") \
            .select("*") \
            .eq("transferencia_id", transferencia_id) \
            .execute()
        
        if asignacion_especifica.data:
            print(f"\n📋 Asignación específica encontrada:")
            for asignacion in asignacion_especifica.data:
                print(f"   - ID: {asignacion.get('id')}")
                print(f"   - Transferencia ID: {asignacion.get('transferencia_id')}")
                print(f"   - Pago ID: {asignacion.get('pago_id')}")
                print(f"   - Cliente: {asignacion.get('cliente')}")
        else:
            print(f"\n❌ No se encontró asignación específica para esta transferencia")
        
    except Exception as e:
        print(f"❌ Error al verificar: {e}")

if __name__ == "__main__":
    verificar_cache() 