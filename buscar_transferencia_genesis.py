#!/usr/bin/env python3
"""
Script para buscar la transferencia específica de Genesis Cliente
"""

import os
import sys
from datetime import datetime
from supabase import create_client, Client

# Configuración de Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def buscar_transferencia_genesis():
    """Busca la transferencia específica de Genesis Cliente con monto 30.000"""
    
    print("🔍 BUSCANDO TRANSFERENCIA DE GENESIS CLIENTE")
    print("=" * 60)
    
    try:
        # Buscar transferencias de Genesis Cliente con monto 30.000
        response = supabase.table("transferencias") \
            .select("*") \
            .eq("cliente", "Genesis Cliente") \
            .eq("monto", 30000) \
            .order("fecha_detec", desc=True) \
            .execute()
        
        if not response.data:
            print("❌ No se encontraron transferencias de Genesis Cliente con monto 30.000")
            return
        
        print(f"✅ Encontradas {len(response.data)} transferencias:")
        
        for i, transferencia in enumerate(response.data):
            print(f"\n📋 Transferencia {i+1}:")
            print(f"   - ID: {transferencia.get('id')}")
            print(f"   - Cliente: {transferencia.get('cliente')}")
            print(f"   - Monto: {transferencia.get('monto')}")
            print(f"   - RUT: {transferencia.get('rut')}")
            print(f"   - Empresa: {transferencia.get('empresa')}")
            print(f"   - Fecha: {transferencia.get('fecha')}")
            print(f"   - Fecha Detec: {transferencia.get('fecha_detec')}")
            
            # Verificar si está asignada
            asignacion = supabase.table("transferencias_pagos") \
                .select("*") \
                .eq("transferencia_id", transferencia.get('id')) \
                .execute()
            
            if asignacion.data:
                print(f"   - ✅ ASIGNADA: Pago ID {asignacion.data[0].get('pago_id')}")
            else:
                print(f"   - ❌ NO ASIGNADA")
        
    except Exception as e:
        print(f"❌ Error al buscar: {e}")

if __name__ == "__main__":
    buscar_transferencia_genesis() 