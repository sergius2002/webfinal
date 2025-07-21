#!/usr/bin/env python3
"""
Script para crear la tabla flujo_capital en Supabase usando el cliente directo
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
        
        # Verificar si la tabla ya existe
        try:
            result = supabase.table("flujo_capital").select("fecha").limit(1).execute()
            print("✅ La tabla flujo_capital ya existe")
            
            # Verificar si ya existe el capital inicial
            result = supabase.table("flujo_capital").select("*").eq("fecha", "2025-07-16").execute()
            if result.data:
                print("✅ El capital inicial ya está configurado")
                return True
            else:
                print("📝 Insertando capital inicial...")
                # Insertar capital inicial
                data = {
                    'fecha': '2025-07-16',
                    'capital_inicial': 32000000,
                    'capital_final': 32000000,
                    'ganancias': 0,
                    'costo_gastos': 0,
                    'gastos_manuales': 0,
                    'margen_neto': 0,
                    'ponderado_ves_clp': 0,
                    'gastos_brs': 0,
                    'pago_movil_brs': 0,
                    'envios_al_detal_brs': 0
                }
                result = supabase.table("flujo_capital").insert(data).execute()
                print("✅ Capital inicial insertado exitosamente")
                return True
                
        except Exception as e:
            print(f"❌ La tabla no existe o hay un error: {e}")
            print("📋 Necesitas crear la tabla manualmente en Supabase SQL Editor")
            print("📄 Usa el archivo CREATE_FLUJO_CAPITAL.sql")
            return False
        
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        return False

def probar_calculo_flujo_capital():
    """Prueba el cálculo del flujo de capital para una fecha específica"""
    try:
        # Crear cliente de Supabase
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("\n🧮 Probando cálculo de flujo de capital...")
        
        # Fecha de prueba
        fecha = "2025-07-17"
        
        # Obtener datos de márgenes para esta fecha
        row_gastos = supabase.table("stock_diario").select("gastos, pago_movil, envios_al_detal").eq("fecha", fecha).execute().data
        print(f"📊 Datos de gastos para {fecha}: {row_gastos}")
        
        if row_gastos and row_gastos[0]:
            gastos = float(row_gastos[0].get('gastos', 0))
            pago_movil = float(row_gastos[0].get('pago_movil', 0))
            envios_al_detal = float(row_gastos[0].get('envios_al_detal', 0))
            print(f"💰 Gastos: {gastos}, Pago móvil: {pago_movil}, Envíos al detal: {envios_al_detal}")
        else:
            print("⚠️ No hay datos de gastos para esta fecha")
        
        # Obtener pedidos para esta fecha
        pedidos = supabase.table("pedidos").select("brs, clp").eq("fecha", fecha).eq("eliminado", False).execute().data
        print(f"📦 Pedidos para {fecha}: {len(pedidos) if pedidos else 0} registros")
        
        if pedidos:
            brs_vendidos = sum(float(p["brs"]) for p in pedidos)
            clp_recibidos = sum(float(p["clp"]) for p in pedidos)
            print(f"🔄 BRS vendidos: {brs_vendidos}, CLP recibidos: {clp_recibidos}")
        
        # Obtener compras para esta fecha
        inicio = fecha + "T00:00:00"
        fin = fecha + "T23:59:59"
        compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        print(f"💱 Compras BRS para {fecha}: {len(compras_brs) if compras_brs else 0} registros")
        
        if compras_brs:
            brs_comprados = sum(float(c["totalprice"]) for c in compras_brs)
            usdt_vendidos = sum(float(c["amount"]) + float(c.get("commission", 0)) for c in compras_brs)
            print(f"🔄 BRS comprados: {brs_comprados}, USDT vendidos: {usdt_vendidos}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al probar cálculo: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando configuración de flujo de capital...")
    
    # Crear tabla
    if crear_tabla_flujo_capital():
        # Probar cálculo
        probar_calculo_flujo_capital()
    else:
        print("\n📋 Para crear la tabla manualmente:")
        print("1. Ve a Supabase Dashboard")
        print("2. Abre SQL Editor")
        print("3. Ejecuta el contenido de CREATE_FLUJO_CAPITAL.sql")
        print("4. Vuelve a ejecutar este script") 