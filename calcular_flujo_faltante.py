#!/usr/bin/env python3
"""
Script para calcular automáticamente el flujo de capital para fechas faltantes
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client, Client

# Configuración de Supabase
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def calcular_flujo_faltante():
    """Calcula el flujo de capital para todas las fechas que tienen pedidos pero no flujo_capital"""
    
    print("🔄 CALCULANDO FLUJO DE CAPITAL PARA FECHAS FALTANTES")
    print("=" * 60)
    
    try:
        # Obtener fechas con pedidos
        pedidos = supabase.table("pedidos").select("fecha").eq("eliminado", False).execute().data
        fechas_con_pedidos = set(item['fecha'] for item in pedidos)
        
        # Obtener fechas con flujo_capital
        flujo_data = supabase.table("flujo_capital").select("fecha").execute().data
        fechas_con_flujo = set(item['fecha'] for item in flujo_data)
        
        # Fechas que faltan
        fechas_faltantes = fechas_con_pedidos - fechas_con_flujo
        
        if not fechas_faltantes:
            print("✅ Todas las fechas con pedidos ya tienen flujo de capital")
            return
        
        print(f"⚠️ Encontradas {len(fechas_faltantes)} fechas con pedidos pero sin flujo de capital")
        
        # Ordenar fechas cronológicamente
        fechas_ordenadas = sorted(fechas_faltantes)
        
        for fecha in fechas_ordenadas:
            print(f"\n📅 Calculando flujo de capital para {fecha}...")
            
            try:
                # Importar la función del blueprint
                sys.path.append('/Users/sergioplaza/Library/CloudStorage/OneDrive-Personal/Sergio/WEB/mi_app')
                from mi_app.blueprints.margen import calcular_flujo_capital_automatico
                
                # Calcular flujo de capital
                resultado = calcular_flujo_capital_automatico(fecha)
                
                if resultado:
                    print(f"✅ Flujo de capital calculado para {fecha}")
                    # Mostrar resumen
                    capital_final = resultado[0].get('capital_final', 0)
                    ganancias = resultado[0].get('ganancias', 0)
                    print(f"   - Ganancias: ${ganancias:,.0f}")
                    print(f"   - Capital final: ${capital_final:,.0f}")
                else:
                    print(f"❌ Error al calcular flujo de capital para {fecha}")
                    
            except Exception as e:
                print(f"❌ Error al calcular {fecha}: {e}")
        
        print(f"\n🎉 Proceso completado. Calculado flujo de capital para {len(fechas_ordenadas)} fechas.")
        
    except Exception as e:
        print(f"❌ Error general: {e}")

if __name__ == "__main__":
    calcular_flujo_faltante() 