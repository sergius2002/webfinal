#!/usr/bin/env python3
"""
Script para verificar el estado de asignación de transferencias
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Configuración de Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def verificar_asignacion_transferencia(transferencia_id):
    """Verifica el estado de asignación de una transferencia específica"""
    
    print(f"🔍 VERIFICANDO TRANSFERENCIA ID: {transferencia_id}")
    print("=" * 60)
    
    try:
        # 1. Verificar si existe en transferencias
        print("1. Verificando tabla transferencias...")
        transferencia = supabase.table("transferencias").select("*").eq("id", transferencia_id).execute()
        
        if not transferencia.data:
            print("❌ Transferencia no encontrada en tabla transferencias")
            return
        
        transferencia_data = transferencia.data[0]
        print(f"✅ Transferencia encontrada:")
        print(f"   - Cliente: {transferencia_data.get('cliente')}")
        print(f"   - Monto: {transferencia_data.get('monto')}")
        print(f"   - Fecha: {transferencia_data.get('fecha')}")
        
        # 2. Verificar si tiene asignación en transferencias_pagos
        print("\n2. Verificando tabla transferencias_pagos...")
        asignacion = supabase.table("transferencias_pagos").select("*").eq("transferencia_id", transferencia_id).execute()
        
        if asignacion.data:
            asignacion_data = asignacion.data[0]
            print(f"✅ Asignación encontrada:")
            print(f"   - Pago ID: {asignacion_data.get('pago_id')}")
            print(f"   - Cliente: {asignacion_data.get('cliente')}")
            print(f"   - Usuario: {asignacion_data.get('usuario_asignacion')}")
            
            # 3. Verificar el pago correspondiente
            print("\n3. Verificando tabla pagos_realizados...")
            pago = supabase.table("pagos_realizados").select("*").eq("id", asignacion_data.get('pago_id')).execute()
            
            if pago.data:
                pago_data = pago.data[0]
                print(f"✅ Pago encontrado:")
                print(f"   - Cliente: {pago_data.get('cliente')}")
                print(f"   - Monto: {pago_data.get('monto_total')}")
                print(f"   - Fecha: {pago_data.get('fecha_registro')}")
            else:
                print("❌ Pago no encontrado en pagos_realizados")
        else:
            print("❌ No hay asignación en transferencias_pagos")
        
        # 4. Estado final
        print(f"\n📊 ESTADO FINAL:")
        if asignacion.data:
            print("✅ TRANSFERENCIA ASIGNADA CORRECTAMENTE")
        else:
            print("❌ TRANSFERENCIA NO ASIGNADA")
            
    except Exception as e:
        print(f"❌ Error al verificar: {e}")

def verificar_todas_asignaciones():
    """Verifica todas las asignaciones recientes"""
    
    print("🔍 VERIFICANDO TODAS LAS ASIGNACIONES RECIENTES")
    print("=" * 60)
    
    try:
        # Obtener todas las asignaciones (sin filtro de fecha por ahora)
        asignaciones = supabase.table("transferencias_pagos").select("*").execute()
        
        if not asignaciones.data:
            print("❌ No hay asignaciones")
            return
        
        print(f"✅ Encontradas {len(asignaciones.data)} asignaciones:")
        
        for asignacion in asignaciones.data:
            print(f"\n📋 Asignación ID: {asignacion.get('id')}")
            print(f"   - Transferencia ID: {asignacion.get('transferencia_id')}")
            print(f"   - Pago ID: {asignacion.get('pago_id')}")
            print(f"   - Cliente: {asignacion.get('cliente')}")
            print(f"   - Usuario: {asignacion.get('usuario_asignacion')}")
            
    except Exception as e:
        print(f"❌ Error al verificar asignaciones: {e}")

if __name__ == "__main__":
    print("🚀 SCRIPT DE VERIFICACIÓN DE ASIGNACIONES")
    print("=" * 60)
    
    # Verificar todas las asignaciones recientes
    verificar_todas_asignaciones()
    
    # Si se proporciona un ID específico, verificarlo
    if len(sys.argv) > 1:
        transferencia_id = sys.argv[1]
        print(f"\n" + "=" * 60)
        verificar_asignacion_transferencia(transferencia_id)
    else:
        print(f"\n💡 Para verificar una transferencia específica:")
        print(f"   python verificar_asignacion.py [TRANSFERENCIA_ID]") 