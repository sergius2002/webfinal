#!/usr/bin/env python3
"""
Script para corregir el cálculo de ganancias usando la lógica real de margen
"""

import os
import sys
from datetime import datetime, timedelta
from supabase import create_client

# Configuración de Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def calcular_ganancias_margen_real(fecha):
    """Calcular ganancias usando la lógica real de margen del sistema"""
    print(f"\n🔄 CALCULANDO GANANCIAS CON MARGEN REAL PARA {fecha}")
    print("="*50)
    
    try:
        # 1. Obtener capital anterior
        fecha_anterior = (datetime.strptime(fecha, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
        capital_anterior = supabase.table("flujo_capital").select("capital_final").eq("fecha", fecha_anterior).execute().data
        
        if not capital_anterior:
            print(f"   ⚠️  No hay capital anterior para {fecha_anterior}, usando $32,000,000")
            capital_inicial = 32000000
        else:
            capital_inicial = float(capital_anterior[0]['capital_final'])
        
        print(f"   💰 Capital inicial: ${capital_inicial:,.0f}")
        
        # 2. Obtener datos del día (usando la lógica real del sistema)
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
        
        # 3. Calcular métricas usando la lógica real del sistema
        # Gastos del stock diario
        gastos = float(stock_data[0]['gastos']) if stock_data and stock_data[0].get('gastos') else 0
        pago_movil = float(stock_data[0]['pago_movil']) if stock_data and stock_data[0].get('pago_movil') else 0
        envios_al_detal = float(stock_data[0]['envios_al_detal']) if stock_data and stock_data[0].get('envios_al_detal') else 0
        
        # Ventas BRS
        brs_vendidos_hoy = sum(float(p['brs']) for p in pedidos) if pedidos else 0
        clp_recibidos = sum(float(p['clp']) for p in pedidos) if pedidos else 0
        
        # Compras BRS
        brs_comprados = sum(float(c['totalprice']) for c in compras_brs) if compras_brs else 0
        usdt_vendidos = sum(float(c['amount']) + float(c.get('commission', 0)) for c in compras_brs) if compras_brs else 0
        
        # Compras USDT
        usdt_comprados = sum(float(c['costo_real']) for c in compras_usdt) if compras_usdt else 0
        clp_invertidos = sum(float(c['totalprice']) for c in compras_usdt) if compras_usdt else 0
        
        # Ventas USDT
        usdt_vendidos_clp = sum(float(v['amount']) for v in ventas_usdt_clp) if ventas_usdt_clp else 0
        clp_recibidos_usdt = sum(float(v['totalprice']) for v in ventas_usdt_clp) if ventas_usdt_clp else 0
        
        # 4. CALCULAR TASAS (lógica real del sistema)
        tasa_usdt_ves_actual = brs_comprados / usdt_vendidos if usdt_vendidos > 0 else 0
        tasa_usdt_clp_actual = clp_invertidos / usdt_comprados if usdt_comprados > 0 else 0
        
        # Obtener saldo anterior
        saldo_anterior = supabase.table("stock_diario").select("brs_stock, usdt_stock, tasa_ves_clp, usdt_tasa").eq("fecha", fecha_anterior).execute().data
        saldo_anterior = saldo_anterior[0] if saldo_anterior else None
        
        total_brs = (float(saldo_anterior["brs_stock"]) if saldo_anterior and saldo_anterior.get("brs_stock") is not None else 0) + brs_comprados
        total_usdt = (float(saldo_anterior["usdt_stock"]) if saldo_anterior and saldo_anterior.get("usdt_stock") is not None else 0) + usdt_comprados - usdt_vendidos_clp
        
        clp_anterior = 0
        if saldo_anterior and saldo_anterior.get('usdt_stock') is not None and saldo_anterior.get('usdt_tasa') is not None:
            clp_anterior = float(saldo_anterior['usdt_stock']) * float(saldo_anterior['usdt_tasa'])
        
        total_clp = clp_anterior + clp_invertidos + clp_recibidos_usdt
        usdt_anterior = float(saldo_anterior["usdt_stock"]) if saldo_anterior and saldo_anterior.get("usdt_stock") is not None else 0
        tasa_usdt_clp_anterior = float(saldo_anterior["usdt_tasa"]) if saldo_anterior and saldo_anterior.get("usdt_tasa") is not None else 0
        tasa_usdt_clp_general = 0
        if total_usdt > 0:
            # Solo incluir USDT que permanecen en stock: saldo anterior + compras
            tasa_usdt_clp_general = (usdt_anterior * tasa_usdt_clp_anterior + usdt_comprados * tasa_usdt_clp_actual) / (usdt_anterior + usdt_comprados)
        
        clp_por_usdt_vendido = usdt_vendidos * tasa_usdt_clp_general
        tasa_ves_clp_actual = brs_comprados / clp_por_usdt_vendido if clp_por_usdt_vendido > 0 else 0
        
        brs_anterior = float(saldo_anterior["brs_stock"]) if saldo_anterior and saldo_anterior.get("brs_stock") is not None else 0
        tasa_ves_clp_anterior = float(saldo_anterior["tasa_ves_clp"]) if saldo_anterior and saldo_anterior.get("tasa_ves_clp") is not None else 0
        ponderado_ves_clp = 0
        if total_brs > 0:
            ponderado_ves_clp = (brs_anterior * tasa_ves_clp_anterior + brs_comprados * tasa_ves_clp_actual) / total_brs
        
        # 5. CALCULAR MÁRGENES (lógica real del sistema)
        # Calcular BRS vendidos al cliente DETAL
        brs_vendidos_detal = sum(float(p["brs"]) for p in pedidos if p.get("cliente") == "DETAL") if pedidos else 0
        brs_vendidos_mayor = brs_vendidos_hoy - brs_vendidos_detal
        
        # CLP recibidos del cliente DETAL
        clp_recibidos_detal = sum(float(p["clp"]) for p in pedidos if p.get("cliente") == "DETAL") if pedidos else 0
        
        # CLP recibidos de todos menos DETAL
        clp_recibidos_mayor = sum(float(p["clp"]) for p in pedidos if p.get("cliente") != "DETAL") if pedidos else 0
        
        # Calcular márgenes
        if ponderado_ves_clp > 0:
            margen_mayor = clp_recibidos_mayor - (brs_vendidos_mayor / ponderado_ves_clp)
            margen_detal = clp_recibidos_detal - (brs_vendidos_detal / ponderado_ves_clp)
            costo_pago_movil = pago_movil / ponderado_ves_clp
            costo_gastos = gastos / ponderado_ves_clp
        else:
            margen_mayor = 0
            margen_detal = 0
            costo_pago_movil = 0
            costo_gastos = 0
        
        margen_total = margen_mayor + margen_detal
        margen_neto = margen_total - costo_pago_movil
        
        # 6. Calcular gastos totales
        gastos_manuales = gastos + pago_movil + envios_al_detal
        
        # 7. Calcular ganancias (margen neto)
        ganancias = margen_neto
        
        # 8. Calcular capital final
        capital_final = capital_inicial + ganancias - costo_gastos - gastos_manuales
        
        print(f"   📊 Resumen de cálculos con margen real:")
        print(f"      - BRS vendidos: {brs_vendidos_hoy:,.0f}")
        print(f"      - CLP recibidos: ${clp_recibidos:,.0f}")
        print(f"      - Ponderado VES/CLP: {ponderado_ves_clp:,.2f}")
        print(f"      - Margen mayor: ${margen_mayor:,.0f}")
        print(f"      - Margen detal: ${margen_detal:,.0f}")
        print(f"      - Margen total: ${margen_total:,.0f}")
        print(f"      - Costo pago móvil: ${costo_pago_movil:,.0f}")
        print(f"      - Margen neto: ${margen_neto:,.0f}")
        print(f"      - Ganancias: ${ganancias:,.0f}")
        print(f"      - Gastos: ${gastos_manuales:,.0f}")
        print(f"      - Capital final: ${capital_final:,.0f}")
        
        # 9. Actualizar en la base de datos
        flujo_data = {
            'fecha': fecha,
            'capital_inicial': capital_inicial,
            'ganancias': ganancias,
            'costo_gastos': costo_gastos,
            'gastos_manuales': gastos_manuales,
            'capital_final': capital_final
        }
        
        # Eliminar registro existente si existe
        supabase.table("flujo_capital").delete().eq("fecha", fecha).execute()
        
        # Insertar nuevo registro
        result = supabase.table("flujo_capital").insert(flujo_data).execute()
        
        if result.data:
            print(f"   ✅ {fecha} - Actualizado con margen real exitosamente")
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
    print("🔧 CORRECCIÓN DE CÁLCULO CON MARGEN REAL DEL SISTEMA")
    print("="*60)
    
    # Días a corregir
    dias_corregir = [
        "2025-07-18",
        "2025-07-19", 
        "2025-07-20",
        "2025-07-21"
    ]
    
    # Recalcular cada día con margen real
    exitosos = 0
    for dia in dias_corregir:
        if calcular_ganancias_margen_real(dia):
            exitosos += 1
    
    print("\n" + "="*60)
    print(f"✅ CORRECCIÓN COMPLETADA - {exitosos}/{len(dias_corregir)} días corregidos")
    print("="*60)
    
    # Verificar resultados finales
    print("\n📊 VERIFICACIÓN FINAL:")
    for dia in dias_corregir:
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