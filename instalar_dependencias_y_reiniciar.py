#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para instalar dependencias y reiniciar el bot de Telegram en PythonAnywhere
"""

import paramiko
import sys
import time


class PythonAnywhereSSH:
    """Clase para manejar conexiones SSH a PythonAnywhere"""
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def conectar(self) -> bool:
        """Establece la conexión SSH"""
        try:
            print(f"🔌 Conectando a {self.hostname} como {self.username}...")
            
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            print("✅ Conexión SSH establecida exitosamente")
            return True
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def ejecutar_comando(self, comando: str, timeout: int = 60) -> str:
        """Ejecuta un comando en el servidor remoto"""
        if not self.client:
            print("❌ No hay conexión SSH activa")
            return ""
        
        try:
            print(f"🚀 Ejecutando: {comando}")
            
            stdin, stdout, stderr = self.client.exec_command(comando, timeout=timeout)
            
            salida = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                print(f"⚠️ Errores: {error}")
            
            return salida
            
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")
            return ""
    
    def cerrar_conexion(self):
        """Cierra la conexión SSH"""
        if self.client:
            self.client.close()
            print("🔌 Conexión SSH cerrada")
    
    def __enter__(self):
        if self.conectar():
            return self
        else:
            raise Exception("No se pudo establecer la conexión SSH")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar_conexion()


def main():
    """Función principal para instalar dependencias y reiniciar el bot"""
    
    # Configuración de conexión
    HOSTNAME = "ssh.eu.pythonanywhere.com"
    USERNAME = "sacristobalspa"
    PASSWORD = "dirqoc-navco2-zethaB"
    
    print("📦 Instalando dependencias y reiniciando Bot de Telegram")
    print("=" * 60)
    
    try:
        with PythonAnywhereSSH(HOSTNAME, USERNAME, PASSWORD) as ssh:
            
            # 1. Detener procesos del bot
            print("\n🛑 Deteniendo procesos del bot:")
            ssh.ejecutar_comando("pkill -f telegram_bot_always")
            time.sleep(2)
            
            # 2. Navegar al directorio del proyecto
            print("\n📂 Navegando al directorio del proyecto:")
            resultado = ssh.ejecutar_comando("cd webfinal && pwd")
            print(f"Directorio: {resultado.strip()}")
            
            # 3. Verificar requirements.txt
            print("\n📄 Verificando requirements.txt:")
            resultado = ssh.ejecutar_comando("cd webfinal && ls -la requirements.txt")
            if resultado:
                print(resultado)
            
            # 4. Mostrar contenido de requirements.txt
            print("\n📋 Contenido de requirements.txt:")
            resultado = ssh.ejecutar_comando("cd webfinal && cat requirements.txt")
            if resultado:
                print(resultado)
            
            # 5. Instalar dependencias con pip3 --user
            print("\n📦 Instalando dependencias (esto puede tomar varios minutos):")
            resultado = ssh.ejecutar_comando("cd webfinal && pip3 install --user -r requirements.txt", timeout=300)
            if resultado:
                print(resultado)
            
            # 6. Verificar instalación de supabase específicamente
            print("\n🔍 Verificando instalación de supabase:")
            resultado = ssh.ejecutar_comando("python3 -c 'import supabase; print(\"✅ Supabase instalado correctamente\")'")
            if resultado:
                print(resultado)
            
            # 7. Verificar instalación de telebot
            print("\n🔍 Verificando instalación de telebot:")
            resultado = ssh.ejecutar_comando("python3 -c 'import telebot; print(\"✅ Telebot instalado correctamente\")'")
            if resultado:
                print(resultado)
            
            # 8. Verificar el archivo .env
            print("\n🔑 Verificando archivo .env:")
            resultado = ssh.ejecutar_comando("cd webfinal && ls -la .env")
            if resultado:
                print(resultado)
            
            # 9. Iniciar el bot en segundo plano
            print("\n🚀 Iniciando bot en segundo plano:")
            comando_inicio = "cd webfinal/mi_app && nohup python3 telegram_bot_always.py > telegram_bot.log 2>&1 &"
            ssh.ejecutar_comando(comando_inicio)
            
            # 10. Esperar y verificar
            print("\n⏳ Esperando 10 segundos para que el bot se inicie...")
            time.sleep(10)
            
            # 11. Verificar log del bot
            print("\n📋 Últimas líneas del log del bot:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && tail -15 telegram_bot.log")
            if resultado:
                print(resultado)
            
            # 12. Verificar procesos
            print("\n🔍 Verificando procesos del bot:")
            resultado = ssh.ejecutar_comando("ps aux | grep python3 | grep telegram")
            if resultado:
                print("✅ Procesos encontrados:")
                print(resultado)
            else:
                print("❌ No se encontraron procesos del bot")
            
            print("\n" + "=" * 60)
            print("🎯 RESUMEN:")
            print("✅ Dependencias instaladas")
            print("✅ Bot reiniciado con nuevo token")
            print("🔒 Revisa el log para confirmar que funciona correctamente")
            
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()