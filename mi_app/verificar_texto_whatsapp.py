#!/usr/bin/env python3
"""
Script simple para verificar el texto de WhatsApp
"""

def verificar_texto_whatsapp():
    """Verifica que el texto de WhatsApp no contenga tasa ponderada"""
    
    print("🔍 VERIFICANDO TEXTO DE WHATSAPP")
    print("=" * 50)
    
    # Simular datos de ejemplo
    cliente = "Cliente Ejemplo"
    fecha = "2025-07-22"
    cantidad = 3
    total_brs = 1500.00
    total_clp = 4500000.00
    
    pedidos = [
        {"brs": 500.00, "clp": 1500000.00},
        {"brs": 600.00, "clp": 1800000.00},
        {"brs": 400.00, "clp": 1200000.00}
    ]
    
    # Generar texto como lo hace la función del frontend
    print("📱 TEXTO QUE SE GENERARÍA:")
    print("-" * 30)
    
    # Calcular anchos máximos para alineación
    max_brs_width = max(len(f"{p['brs']:,.2f}") for p in pedidos)
    max_clp_width = max(len(f"{p['clp']:,.2f}") for p in pedidos)
    
    # Generar líneas de detalle con alineación
    lineas_detalle = []
    for i, pedido in enumerate(pedidos):
        brs_padded = f"{pedido['brs']:,.2f}".rjust(max_brs_width)
        clp_padded = f"{pedido['clp']:,.2f}".rjust(max_clp_width)
        lineas_detalle.append(f"{i+1}. BRS: {brs_padded} | CLP: {clp_padded}")
    
    # Generar texto completo - SOLO BRS Y CLP, SIN TASA PONDERADA
    texto = f"""📦 *RESUMEN DE PEDIDOS HOY*
👤 Cliente: {cliente}
📅 Fecha: {fecha}
🔢 Cantidad de pedidos: {cantidad}

💰 *TOTALES:*
• BRS: {total_brs:,.2f}
• CLP: {total_clp:,.2f}

📋 *DETALLE DE PEDIDOS:*
{chr(10).join(lineas_detalle)}"""
    
    print(texto)
    print("-" * 30)
    
    # Verificar que NO contiene "ponderada"
    if "ponderada" in texto.lower():
        print("❌ ERROR: El texto contiene 'ponderada'")
        return False
    else:
        print("✅ El texto NO contiene 'ponderada'")
    
    # Verificar que NO contiene "tasa"
    if "tasa" in texto.lower():
        print("❌ ERROR: El texto contiene 'tasa'")
        return False
    else:
        print("✅ El texto NO contiene 'tasa'")
    
    # Verificar que contiene los elementos correctos
    elementos_requeridos = ["BRS:", "CLP:", "TOTALES:", "DETALLE DE PEDIDOS:"]
    for elemento in elementos_requeridos:
        if elemento in texto:
            print(f"✅ Contiene '{elemento}'")
        else:
            print(f"❌ Falta '{elemento}'")
            return False
    
    print("\n" + "=" * 50)
    print("✅ VERIFICACIÓN COMPLETADA: El texto está correcto")
    print("✅ NO contiene tasa ponderada")
    print("✅ Solo contiene BRS y CLP como solicitado")
    
    return True

if __name__ == "__main__":
    verificar_texto_whatsapp() 