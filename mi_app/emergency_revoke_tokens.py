#!/usr/bin/env python3
"""
SCRIPT DE EMERGENCIA - REVOCAR TOKENS DE TELEGRAM
=================================================

Este script revoca todos los tokens de Telegram encontrados en el código
para prevenir uso malicioso.

USAR SOLO EN EMERGENCIAS DE SEGURIDAD
"""

import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tokens encontrados en el código (REVOCAR INMEDIATAMENTE)
TOKENS_TO_REVOKE = [
    "6962665881:AAG7e9l9rRtcnWyyia8i9jR5aLiU4ldlTzI",  # telegram_bot_always.py - COMPROMETIDO
    "8065976460:AAFD9jTwj8Ec4eDR7j_0BS0ImIEAVL1_1HE",  # telegram_bot_always.py - CORRECTO
    "7503093829:AAGzK60nUU6w4HtBSM8XVeIk9uK5JonjfHI",  # dolar_bcv.py
    "7522395434:AAHg1uPMnT94tRqoY_gWB8IjKt1GTS4cw3o"   # sumar_comprobantes_telegram.py
]

def revoke_token(token):
    """Revoca un token de Telegram"""
    try:
        # Intentar revocar el token usando deleteWebhook
        url = f"https://api.telegram.org/bot{token}/deleteWebhook"
        response = requests.get(url)
        
        if response.status_code == 200:
            logger.info(f"✅ Token {token[:10]}... webhook eliminado")
        else:
            logger.warning(f"⚠️ Token {token[:10]}... respuesta: {response.status_code}")
            
        # Intentar obtener info del bot para verificar si está activo
        url = f"https://api.telegram.org/bot{token}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            bot_info = response.json()
            logger.warning(f"🚨 Token {token[:10]}... ACTIVO - Bot: {bot_info.get('result', {}).get('username', 'Unknown')}")
            return True
        else:
            logger.info(f"✅ Token {token[:10]}... INACTIVO o REVOCADO")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verificando token {token[:10]}...: {e}")
        return None

def main():
    """Función principal"""
    logger.info("🚨 INICIANDO REVOCACIÓN DE EMERGENCIA DE TOKENS")
    logger.info("=" * 50)
    
    active_tokens = []
    
    for token in TOKENS_TO_REVOKE:
        logger.info(f"🔍 Verificando token {token[:10]}...")
        is_active = revoke_token(token)
        
        if is_active:
            active_tokens.append(token)
    
    logger.info("=" * 50)
    logger.info("📊 RESUMEN:")
    logger.info(f"Total tokens verificados: {len(TOKENS_TO_REVOKE)}")
    logger.info(f"Tokens activos encontrados: {len(active_tokens)}")
    
    if active_tokens:
        logger.warning("🚨 TOKENS ACTIVOS DETECTADOS:")
        for token in active_tokens:
            logger.warning(f"   - {token[:10]}...")
        logger.warning("🔧 ACCIÓN REQUERIDA: Revocar estos tokens manualmente en @BotFather")
    else:
        logger.info("✅ No se encontraron tokens activos")

if __name__ == "__main__":
    main()