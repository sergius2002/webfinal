#!/usr/bin/env python3
"""
Script para verificar y corregir los cálculos del flujo de capital
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def verificar_datos_dia(fecha):
    """Verificar los datos disponibles para un día específico"""
    print(f"\n🔍 VERIFICANDO DATOS PARA {fecha}")
    print("="*50)
    
    # 1. Verificar stock diario
    stock_data = supabase.table("stock_diario").select("*").eq("fecha", fecha).execute().data
    print(f"📊 Stock diario: {len(stock_data)} registros")
    if stock_data:
        stock = stock_data[0]
        print(f"   - Gastos: ${stock.get('gastos', 0):,.0f}")
        print(f"   - Pago móvil: ${stock.get('pago_movil', 0):,.0f}")
        print(f"   - Envíos al detal: ${stock.get('envios_al_detal', 0):,.0f}")
        print(f"   - BRS Stock: {stock.get('brs_stock', 0):,.0f}")
        print(f"   - USDT Stock: {stock.get('usdt_stock', 0):,.0f}")
    else:
        print("   ⚠️  NO HAY DATOS DE STOCK DIARIO")
    
    # 2. Verificar pedidos
    pedidos = supabase.table("pedidos").select("brs, clp, cliente").eq("fecha", fecha).eq("eliminado", False).execute().data
    print(f"📋 Pedidos: {len(pedidos)} registros")
    if pedidos:
        total_brs = sum(float(p['brs']) for p in pedidos)
        total_clp = sum(float(p['clp']) for p in pedidos)
        print(f"   - Total BRS vendidos: {total_brs:,.0f}")
        print(f"   - Total CLP recibidos: ${total_clp:,.0f}")
        
        # Detal vs Mayor
        detal_pedidos = [p for p in pedidos if p.get('cliente') == 'DETAL']
        mayor_pedidos = [p for p in pedidos if p.get('cliente') != 'DETAL']
        
        print(f"   - Pedidos DETAL: {len(detal_pedidos)}")
        print(f"   - Pedidos MAYOR: {len(mayor_pedidos)}")
    else:
        print("   ⚠️  NO HAY PEDIDOS")
    
    # 3. Verificar compras
    inicio = fecha + "T00:00:00"
    fin = fecha + "T23:59:59"
    
    # Compras BRS (VES)
    compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
    print(f"💰 Compras BRS (VES): {len(compras_brs)} registros")
    if compras_brs:
        total_compras_brs = sum(float(c['totalprice']) for c in compras_brs)
        commission_compras_brs = sum(float(c['commission']) for c in compras_brs)
        print(f"   - Total compras: ${total_compras_brs:,.0f}")
        print(f"   - Comisiones: ${commission_compras_brs:,.0f}")
    else:
        print("   ⚠️  NO HAY COMPRAS BRS")
    
    # Compras USDT (CLP)
    compras_usdt = supabase.table("compras").select("costo_real, totalprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
    print(f"💵 Compras USDT (CLP): {len(compras_usdt)} registros")
    if compras_usdt:
        total_compras_usdt = sum(float(c['costo_real']) for c in compras_usdt)
        print(f"   - Total compras: ${total_compras_usdt:,.0f}")
    else:
        print("   ⚠️  NO HAY COMPRAS USDT")
    
    # Ventas USDT (CLP)
    ventas_usdt_clp = supabase.table("compras").select("amount, totalprice").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
    print(f"💸 Ventas USDT (CLP): {len(ventas_usdt_clp)} registros")
    if ventas_usdt_clp:
        total_ventas_usdt = sum(float(v['totalprice']) for v in ventas_usdt_clp)
        print(f"   - Total ventas: ${total_ventas_usdt:,.0f}")
    else:
        print("   ⚠️  NO HAY VENTAS USDT")
    
    # 4. Verificar flujo de capital actual
    flujo_actual = supabase.table("flujo_capital").select("*").eq("fecha", fecha).execute().data
    print(f"📈 Flujo de capital actual: {len(flujo_actual)} registros")
    if flujo_actual:
        flujo = flujo_actual[0]
        print(f"   - Capital inicial: ${flujo.get('capital_inicial', 0):,.0f}")
        print(f"   - Ganancias: ${flujo.get('ganancias', 0):,.0f}")
        print(f"   - Gastos: ${flujo.get('gastos_manuales', 0):,.0f}")
        print(f"   - Capital final: ${flujo.get('capital_final', 0):,.0f}")
    else:
        print("   ⚠️  NO HAY FLUJO DE CAPITAL")

def recalcular_flujo_correcto(fecha):
    """Recalcular el flujo de capital con lógica corregida"""
    print(f"\n🔄 RECALCULANDO FLUJO PARA {fecha}")
    print("="*50)
    
    try:
        # 1. Obtener capital anterior (día anterior)
        fecha_anterior = (datetime.strptime(fecha, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        capital_anterior = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_anterior).execute().data
        
        if not capital_anterior:
            print(f"   ⚠️  No hay capital anterior para {fecha_anterior}, usando $32,000,000")
            capital_inicial = 32000000
        else:
            capital_inicial = float(capital_anterior[0]['capital_final'])
        
        print(f"   💰 Capital inicial: ${capital_inicial:,.0f}")
        
        # 2. Obtener datos del día
        # Stock diario
        stock_data = supabase.table("stock_diario").select("*").eq("fecha", fecha).execute().data
        
        # Pedidos del día
        pedidos = supabase.table("pedidos").select("brs, clp, cliente").eq("fecha", fecha).eq("eliminado", False).execute().data
        
        # Compras del día
        inicio = fecha + "T00:00:00"
        fin = fecha + "T23:59:59"
        compras_brs = supabase.table("compras").select("totalprice, amount, commission").eq("fiat", "VES").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        compras_usdt = supabase.table("compras").select("costo_real, totalprice").eq("fiat", "CLP").eq("tradetype", "BUY").gte("createtime", inicio).lte("createtime", fin).execute().data
        ventas_usdt_clp = supabase.table("compras").select("amount, totalprice").eq("fiat", "CLP").eq("tradetype", "SELL").gte("createtime", inicio).lte("createtime", fin).execute().data
        
        # 3. Calcular métricas
        # Gastos del stock diario
        gastos = float(stock_data[0]['gastos']) if stock_data and stock_data[0].get('gastos') else 0
        pago_movil = float(stock_data[0]['pago_movil']) if stock_data and stock_data[0].get('pago_movil') else 0
        envios_al_detal = float(stock_data[0]['envios_al_detal']) if stock_data and stock_data[0].get('envios_al_detal') else 0
        
        # Ventas BRS
        brs_vendidos = sum(float(p['brs']) for p in pedidos) if pedidos else 0
        clp_recibidos = sum(float(p['clp']) for p in pedidos) if pedidos else 0
        
        # Compras BRS
        total_compras_brs = sum(float(c['totalprice']) for c in compras_brs) if compras_brs else 0
        commission_compras_brs = sum(float(c['commission']) for c in compras_brs) if compras_brs else 0
        
        # Compras USDT
        total_compras_usdt = sum(float(c['costo_real']) for c in compras_usdt) if compras_usdt else 0
        
        # Ventas USDT
        total_ventas_usdt = sum(float(v['totalprice']) for v in ventas_usdt_clp) if ventas_usdt_clp else 0
        
        # 4. Calcular ganancias (LÓGICA CORREGIDA)
        # Ganancias = CLP recibidos por ventas - Costo de compras BRS - Comisiones - Costo de compras USDT + Ventas USDT
        ganancias = clp_recibidos - total_compras_brs - commission_compras_brs - total_compras_usdt + total_ventas_usdt
        
        # 5. Calcular gastos totales
        gastos_manuales = gastos + pago_movil + envios_al_detal
        
        # 6. Calcular capital final
        capital_final = capital_inicial + ganancias - gastos_manuales
        
        print(f"   📊 Resumen de cálculos:")
        print(f"      - CLP recibidos: ${clp_recibidos:,.0f}")
        print(f"      - Compras BRS: ${total_compras_brs:,.0f}")
        print(f"      - Comisiones: ${commission_compras_brs:,.0f}")
        print(f"      - Compras USDT: ${total_compras_usdt:,.0f}")
        print(f"      - Ventas USDT: ${total_ventas_usdt:,.0f}")
        print(f"      - Ganancias: ${ganancias:,.0f}")
        print(f"      - Gastos: ${gastos_manuales:,.0f}")
        print(f"      - Capital final: ${capital_final:,.0f}")
        
        # 7. Actualizar en la base de datos
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': ganancias,
            'costo_gastos': gastos_manuales,
            'gastos_manuales': gastos_manuales,
            'capital_final': capital_final
        }
        
        # Eliminar registro existente si existe
        supabase.table("flujo_capital").delete().eq("fecha", fecha).execute()
        
        # Insertar nuevo registro
        result = supabase.table("flujo_capital").insert(flujo_data).execute()
        
        if result.data:
            print(f"   ✅ {fecha} - Actualizado exitosamente")
            return True
        else:
            print(f"   ❌ Error al actualizar {fecha}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error al recalcular {fecha}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Función principal"""
    print("🔧 VERIFICACIÓN Y CORRECCIÓN DE FLUJO DE CAPITAL")
    print("="*60)
    
    # Días problemáticos
    dias_problematicos = [
        "2025-07-18",
        "2025-07-19", 
        "2025-07-20",
        "2025-07-21"
    ]
    
    # Verificar datos de cada día
    for dia in dias_problematicos:
        verificar_datos_dia(dia)
    
    print("\n" + "="*60)
    print("🔄 INICIANDO RECÁLCULO CORREGIDO")
    print("="*60)
    
    # Recalcular cada día
    exitosos = 0
    for dia in dias_problematicos:
        if recalcular_flujo_correcto(dia):
            exitosos += 1
    
    print("\n" + "="*60)
    print(f"✅ RECÁLCULO COMPLETADO - {exitosos}/{len(dias_problematicos)} días corregidos")
    print("="*60)
    
    # Verificar resultados finales
    print("\n📊 VERIFICACIÓN FINAL:")
    for dia in dias_problematicos:
        try:
            result = supabase.table("flujo_capital").select("fecha, capital_inicial, ganancias, capital_final").eq("fecha", dia).execute().data
            if result:
                data = result[0]
                print(f"   ✅ {dia} - Capital: ${data['capital_inicial']:,.0f} → ${data['capital_final']:,.0f} (Ganancias: ${data['ganancias']:,.0f})")
            else:
                print(f"   ❌ {dia} - Aún faltante")
        except Exception as e:
            print(f"   ⚠️  {dia} - Error: {e}")

if __name__ == "__main__":
    main() 