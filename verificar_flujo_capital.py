#!/usr/bin/env python3
"""
Script para verificar datos del flujo de capital
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuración de Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def verificar_datos_flujo_capital():
    """Verifica qué datos existen en la tabla flujo_capital"""
    
    print("🔍 VERIFICANDO DATOS DEL FLUJO DE CAPITAL")
    print("=" * 60)
    
    try:
        # Obtener todos los datos de flujo_capital
        flujo_data = supabase.table("flujo_capital").select("*").order("fecha").execute().data
        
        if not flujo_data:
            print("❌ No hay datos en la tabla flujo_capital")
            return
        
        print(f"✅ Encontrados {len(flujo_data)} registros en flujo_capital:")
        
        for item in flujo_data:
            print(f"📅 {item['fecha']}: Capital inicial=${item.get('capital_inicial', 0):,.0f}, "
                  f"Ganancias=${item.get('ganancias', 0):,.0f}, "
                  f"Capital final=${item.get('capital_final', 0):,.0f}")
        
        # Verificar qué fechas tienen pedidos pero no flujo_capital
        print(f"\n🔍 VERIFICANDO FECHAS CON PEDIDOS PERO SIN FLUJO DE CAPITAL")
        print("=" * 60)
        
        # Obtener fechas con pedidos
        pedidos = supabase.table("pedidos").select("fecha").eq("eliminado", False).execute().data
        fechas_con_pedidos = set(item['fecha'] for item in pedidos)
        
        # Obtener fechas con flujo_capital
        fechas_con_flujo = set(item['fecha'] for item in flujo_data)
        
        # Fechas que faltan
        fechas_faltantes = fechas_con_pedidos - fechas_con_flujo
        
        if fechas_faltantes:
            print(f"⚠️ Fechas con pedidos pero sin flujo de capital ({len(fechas_faltantes)}):")
            for fecha in sorted(fechas_faltantes):
                print(f"   - {fecha}")
        else:
            print("✅ Todas las fechas con pedidos tienen flujo de capital")
        
        # Verificar rango de fechas
        if flujo_data:
            fecha_min = min(item['fecha'] for item in flujo_data)
            fecha_max = max(item['fecha'] for item in flujo_data)
            print(f"\n📊 Rango de datos: {fecha_min} a {fecha_max}")
        
    except Exception as e:
        print(f"❌ Error al verificar datos: {e}")

def verificar_calculo_automatico():
    """Verifica por qué no se calcula automáticamente para más fechas"""
    
    print(f"\n🔄 VERIFICANDO CÁLCULO AUTOMÁTICO")
    print("=" * 60)
    
    try:
        # Obtener fechas recientes con pedidos
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        fecha_ayer = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        print(f"📅 Verificando fechas: {fecha_ayer} y {fecha_hoy}")
        
        # Verificar si hay pedidos en estas fechas
        pedidos_ayer = supabase.table("pedidos").select("fecha").eq("fecha", fecha_ayer).eq("eliminado", False).execute().data
        pedidos_hoy = supabase.table("pedidos").select("fecha").eq("fecha", fecha_hoy).eq("eliminado", False).execute().data
        
        print(f"📋 Pedidos ayer ({fecha_ayer}): {len(pedidos_ayer)}")
        print(f"📋 Pedidos hoy ({fecha_hoy}): {len(pedidos_hoy)}")
        
        # Verificar si hay flujo_capital para estas fechas
        flujo_ayer = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha_ayer).execute().data
        flujo_hoy = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha_hoy).execute().data
        
        print(f"💰 Flujo capital ayer ({fecha_ayer}): {'✅' if flujo_ayer else '❌'}")
        print(f"💰 Flujo capital hoy ({fecha_hoy}): {'✅' if flujo_hoy else '❌'}")
        
    except Exception as e:
        print(f"❌ Error al verificar cálculo automático: {e}")

if __name__ == "__main__":
    verificar_datos_flujo_capital()
    verificar_calculo_automatico() 