#!/usr/bin/env python3
"""
Script de prueba para verificar el texto de WhatsApp
"""

import requests
import json

def test_whatsapp_text():
    """Prueba la generación de texto de WhatsApp"""
    
    # URL del servidor Flask
    base_url = "http://127.0.0.1:5001"
    
    try:
        # Obtener datos de un cliente específico
        cliente = "Carlos Azuaje"  # Cambiar por un cliente que tenga pedidos hoy
        
        # Hacer request a la API del dashboard
        response = requests.get(f"{base_url}/dashboard/api/cliente/{cliente}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Datos obtenidos correctamente")
            print(f"Cliente: {cliente}")
            print(f"Pedidos hoy: {data.get('pedidos_hoy', 0)}")
            print(f"Pagos hoy: {data.get('pagos_hoy', 0)}")
            print(f"Deuda anterior: {data.get('deuda_anterior', 0)}")
            print(f"Saldo final: {data.get('saldo_final', 0)}")
            
            # Verificar pedidos
            pedidos = data.get('pedidos', [])
            print(f"\n📋 Pedidos ({len(pedidos)}):")
            for i, pedido in enumerate(pedidos[:3]):  # Solo mostrar los primeros 3
                print(f"  {i+1}. Fecha: {pedido.get('fecha')}, BRS: {pedido.get('brs')}, CLP: {pedido.get('clp')}")
            
            # Verificar que NO hay tasa ponderada
            if 'tasa_ponderada' in data:
                print("❌ ERROR: tasa_ponderada encontrada en los datos")
                return False
            else:
                print("✅ No hay tasa_ponderada en los datos")
            
            # Simular el texto que se generaría
            print("\n📱 Texto que se generaría para WhatsApp:")
            print("=" * 50)
            
            # Calcular totales
            total_brs = sum(float(p.get('brs', 0)) for p in pedidos)
            total_clp = sum(float(p.get('clp', 0)) for p in pedidos)
            
            # Generar texto similar al frontend
            texto = f"""📦 *RESUMEN DE PEDIDOS HOY*
👤 Cliente: {cliente}
📅 Fecha: 2025-07-22
🔢 Cantidad de pedidos: {len(pedidos)}

💰 *TOTALES:*
• BRS: {total_brs:,.2f}
• CLP: {total_clp:,.2f}

📋 *DETALLE DE PEDIDOS:*"""
            
            for i, pedido in enumerate(pedidos):
                brs = float(pedido.get('brs', 0))
                clp = float(pedido.get('clp', 0))
                texto += f"\n{i+1}. BRS: {brs:,.2f} | CLP: {clp:,.2f}"
            
            print(texto)
            print("=" * 50)
            
            # Verificar que NO contiene "ponderada"
            if "ponderada" in texto.lower():
                print("❌ ERROR: El texto contiene 'ponderada'")
                return False
            else:
                print("✅ El texto NO contiene 'ponderada'")
                return True
                
        else:
            print(f"❌ Error al obtener datos: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Probando generación de texto de WhatsApp...")
    success = test_whatsapp_text()
    
    if success:
        print("\n✅ PRUEBA EXITOSA: No hay tasa ponderada en el texto")
    else:
        print("\n❌ PRUEBA FALLIDA: Se encontró tasa ponderada") 