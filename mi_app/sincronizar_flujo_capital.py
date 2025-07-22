#!/usr/bin/env python3
"""
Script para sincronizar manualmente el flujo de capital desde las transacciones
"""

import os
import sys
from supabase import create_client, Client
from datetime import datetime, timedelta

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://tmimwpzxmtezopieqzcl.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtaW13cHp4bXRlem9waWVxemNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzY4NTI5NzQsImV4cCI6MjA1MjQyODk3NH0.tTrdPaiPAkQbF_JlfOOWTQwSs3C_zBbFDZECYzPP-Ho')

def sincronizar_flujo_capital_desde_transacciones(fecha):
    """Sincroniza el flujo de capital basado en las transacciones de una fecha específica"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print(f"🔄 Sincronizando flujo de capital para {fecha}...")
        
        # Obtener todas las transacciones de la fecha
        transacciones = supabase.table("transacciones_flujo").select("*").eq("fecha", fecha).order("created_at").execute().data
        
        if not transacciones:
            print(f"ℹ️ No hay transacciones para sincronizar en {fecha}")
            return True
        
        print(f"📊 Encontradas {len(transacciones)} transacciones para {fecha}")
        
        # Calcular totales
        total_entradas = sum(float(t['monto']) for t in transacciones if t['tipo'] == 'ENTRADA')
        total_salidas = sum(float(t['monto']) for t in transacciones if t['tipo'] == 'SALIDA')
        
        print(f"💰 Total entradas: ${total_entradas:,.0f}")
        print(f"💸 Total salidas: ${total_salidas:,.0f}")
        
        # Obtener capital inicial (del día anterior)
        fecha_dt = datetime.strptime(fecha, '%Y-%m-%d')
        fecha_ayer = (fecha_dt - timedelta(days=1)).strftime('%Y-%m-%d')
        capital_ayer = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_ayer).execute().data
        capital_inicial = float(capital_ayer[0]['capital_final']) if capital_ayer else 32000000
        
        print(f"🏦 Capital inicial: ${capital_inicial:,.0f}")
        
        # Calcular capital final
        capital_final = capital_inicial + total_entradas - total_salidas
        
        # Categorizar gastos
        gastos_venezuela = sum(float(t['monto']) for t in transacciones 
                              if t['tipo'] == 'SALIDA' and t['categoria'] == 'GASTOS_VENEZUELA')
        gastos_chile = sum(float(t['monto']) for t in transacciones 
                          if t['tipo'] == 'SALIDA' and t['categoria'] == 'GASTOS_CHILE')
        
        print(f"🇻🇪 Gastos Venezuela: ${gastos_venezuela:,.0f}")
        print(f"🇨🇱 Gastos Chile: ${gastos_chile:,.0f}")
        print(f"🏦 Capital final: ${capital_final:,.0f}")
        
        # Actualizar o crear registro en flujo_capital
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': total_entradas,
            'costo_gastos': gastos_venezuela,
            'gastos_manuales': gastos_chile,
            'capital_final': capital_final
        }
        
        # Verificar si ya existe un registro para esta fecha
        existing = supabase.table("flujo_capital").select("fecha").eq("fecha", fecha).execute().data
        
        if existing:
            # Actualizar registro existente
            response = supabase.table("flujo_capital").update(flujo_data).eq("fecha", fecha).execute()
            print("✅ Registro actualizado en flujo_capital")
        else:
            # Crear nuevo registro
            response = supabase.table("flujo_capital").insert(flujo_data).execute()
            print("✅ Nuevo registro creado en flujo_capital")
        
        print(f"✅ Flujo de capital sincronizado exitosamente para {fecha}")
        return True
        
    except Exception as e:
        print(f"❌ Error al sincronizar flujo de capital: {e}")
        return False

def sincronizar_rango_fechas(fecha_inicio, fecha_fin):
    """Sincroniza el flujo de capital para un rango de fechas"""
    try:
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d')
        
        fechas = []
        current_date = fecha_inicio_dt
        while current_date <= fecha_fin_dt:
            fechas.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        print(f"🔄 Sincronizando {len(fechas)} fechas desde {fecha_inicio} hasta {fecha_fin}")
        
        exitos = 0
        errores = 0
        
        for fecha in fechas:
            if sincronizar_flujo_capital_desde_transacciones(fecha):
                exitos += 1
            else:
                errores += 1
        
        print(f"\n📊 Resumen de sincronización:")
        print(f"✅ Éxitos: {exitos}")
        print(f"❌ Errores: {errores}")
        print(f"📅 Total fechas: {len(fechas)}")
        
        return exitos, errores
        
    except Exception as e:
        print(f"❌ Error al sincronizar rango de fechas: {e}")
        return 0, 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python sincronizar_flujo_capital.py <fecha>")
        print("  python sincronizar_flujo_capital.py <fecha_inicio> <fecha_fin>")
        print("")
        print("Ejemplos:")
        print("  python sincronizar_flujo_capital.py 2025-07-17")
        print("  python sincronizar_flujo_capital.py 2025-07-16 2025-07-17")
        sys.exit(1)
    
    if len(sys.argv) == 2:
        # Sincronizar una fecha específica
        fecha = sys.argv[1]
        print(f"🚀 Sincronizando flujo de capital para {fecha}")
        sincronizar_flujo_capital_desde_transacciones(fecha)
    elif len(sys.argv) == 3:
        # Sincronizar un rango de fechas
        fecha_inicio = sys.argv[1]
        fecha_fin = sys.argv[2]
        print(f"🚀 Sincronizando flujo de capital desde {fecha_inicio} hasta {fecha_fin}")
        sincronizar_rango_fechas(fecha_inicio, fecha_fin) 